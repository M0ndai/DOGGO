"""Scope structure and companion timing checks, including fail-closed inputs."""

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from validators.observation_scope import validate_scope_time


ROOT = Path(__file__).resolve().parents[1]


class ScopeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = json.loads(
            (ROOT / "schemas/observation-scope.schema.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        cls.validator = Draft202012Validator(schema)

    def setUp(self):
        self.scope = {
            "subject": "service-A",
            "evidence_boundary": "caller-supplied snapshot",
            "collection_time": "2026-10-11T10:00:00Z",
            "time_window": {
                "start": "2026-10-10T00:00:00Z",
                "end": "2026-10-11T00:00:00Z",
            },
            "requested_signal": "availability",
        }

    def test_accepts_valid_scope_without_mutating_input(self):
        before = copy.deepcopy(self.scope)
        self.assertTrue(self.validator.is_valid(self.scope))
        self.assertEqual(validate_scope_time(self.scope), [])
        self.assertEqual(self.scope, before)

    def test_rejects_reversed_interval_even_when_schema_accepts(self):
        self.scope["time_window"]["end"] = "2026-10-09T00:00:00Z"
        self.assertTrue(self.validator.is_valid(self.scope))
        self.assertIn(
            "time_window.end must not precede time_window.start",
            validate_scope_time(self.scope),
        )

    def test_compares_instants_instead_of_local_clock_strings(self):
        self.scope["time_window"] = {
            "start": "2026-10-11T10:00:00+02:00",
            "end": "2026-10-11T08:00:00Z",
        }
        self.assertEqual(validate_scope_time(self.scope), [])
        self.scope["time_window"]["end"] = "2026-10-11T08:59:59+01:00"
        self.assertTrue(validate_scope_time(self.scope))

    def test_rejects_invalid_timestamps_without_optional_format_checker(self):
        for value in (
            "invalid", "2026-02-30T00:00:00Z", "2026-10-11T00:00:00",
            "2026-10-11", "2026-10-11T00:00:00-00:00",
            "2026-10-11T00:00:60Z", "2026-10-11T00:00:00+25:00",
            "2026-10-11T00:00:00+01:99", "2026-10-11T00:00:00.1234567Z",
            None, 42,
        ):
            for field in ("collection_time", "start", "end"):
                with self.subTest(value=value, field=field):
                    candidate = copy.deepcopy(self.scope)
                    container = candidate if field == "collection_time" else candidate["time_window"]
                    container[field] = value
                    self.assertTrue(validate_scope_time(candidate))

    def test_missing_or_malformed_timing_fails_closed(self):
        for candidate in (None, [], {}, {"time_window": []}):
            with self.subTest(candidate=candidate):
                self.assertTrue(validate_scope_time(candidate))
        for field in ("start", "end"):
            candidate = copy.deepcopy(self.scope)
            del candidate["time_window"][field]
            self.assertTrue(validate_scope_time(candidate))

    def test_accepts_fractional_seconds_and_lowercase_rfc3339(self):
        self.scope["time_window"] = {
            "start": "2026-10-11t08:00:00.125z",
            "end": "2026-10-11T08:00:00.126Z",
        }
        self.assertEqual(validate_scope_time(self.scope), [])

    def test_structural_schema_rejects_missing_and_extra_fields(self):
        for field in self.scope:
            candidate = copy.deepcopy(self.scope)
            del candidate[field]
            self.assertFalse(self.validator.is_valid(candidate), field)
        self.scope["execute"] = "repair"
        self.assertFalse(self.validator.is_valid(self.scope))


if __name__ == "__main__":
    unittest.main()
