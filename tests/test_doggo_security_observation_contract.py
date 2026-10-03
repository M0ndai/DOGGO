from __future__ import annotations

import copy
import hashlib
import json
import math
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "contracts" / "doggo-security-observation.v0.1.schema.json"
VALID_FIXTURES = ROOT / "fixtures" / "valid"
INVALID_FIXTURES = ROOT / "fixtures" / "invalid"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def canonical_json_bytes(value: object) -> bytes:
    """Return the local v0.1 fixture projection documented in contracts/README."""

    def reject_non_finite(node: object) -> None:
        if isinstance(node, float) and not math.isfinite(node):
            raise ValueError("non-finite numbers are not canonical JSON")
        if isinstance(node, list):
            for item in node:
                reject_non_finite(item)
        elif isinstance(node, dict):
            for item in node.values():
                reject_non_finite(item)

    reject_non_finite(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def observation_ref(payload: dict) -> str:
    digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return f"sha256:{digest}"


class DOGGOSecurityObservationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(
            cls.schema,
            format_checker=FormatChecker(),
        )
        cls.ref_validator = Draft202012Validator(
            cls.schema["$defs"]["DOGGOSecurityObservationRef"]
        )

    def test_contract_fixes_authority_effect_and_closed_status_axes(self) -> None:
        properties = self.schema["properties"]
        self.assertEqual(properties["authority"], {"const": "NONE"})
        self.assertEqual(properties["effect"], {"const": "NONE"})
        self.assertEqual(
            properties["observation_status"]["enum"],
            [
                "NOMINAL",
                "ATTENTION",
                "ANOMALY",
                "UNKNOWN",
                "INSUFFICIENT_EVIDENCE",
                "INSUFFICIENT_SCOPE",
            ],
        )
        self.assertEqual(
            properties["handoff_status"]["enum"],
            ["NONE", "PROPOSED", "BLOCKED_AUTHORITY"],
        )

    def test_valid_observations_and_refs_match_deterministic_identity(self) -> None:
        observation_paths = sorted(VALID_FIXTURES.glob("*.observation.json"))
        self.assertTrue(observation_paths)

        for observation_path in observation_paths:
            with self.subTest(fixture=observation_path.name):
                payload = load_json(observation_path)
                self.validator.validate(payload)

                ref_path = observation_path.with_name(
                    observation_path.name.replace(".observation.json", ".ref.json")
                )
                ref = load_json(ref_path)
                self.ref_validator.validate(ref)
                self.assertEqual(ref["ref"], observation_ref(payload))

                reordered = dict(reversed(list(payload.items())))
                self.assertEqual(observation_ref(reordered), observation_ref(payload))

    def test_negative_examples_are_rejected_at_the_intended_boundary(self) -> None:
        expected_error = {
            "authority-request.observation.json": "authority_request",
            "effect-command.observation.json": "effect",
            "incident-decision.observation.json": "incident_decision",
            "mandate.observation.json": "mandate",
            "remediation.observation.json": "remediation",
        }
        self.assertEqual(
            {path.name for path in INVALID_FIXTURES.glob("*.json")},
            set(expected_error),
        )

        for name, marker in expected_error.items():
            with self.subTest(fixture=name):
                errors = list(
                    self.validator.iter_errors(load_json(INVALID_FIXTURES / name))
                )
                self.assertTrue(errors)
                rendered = "\n".join(
                    f"{error.json_path}: {error.message}" for error in errors
                )
                self.assertIn(marker, rendered)

    def test_anomaly_handoff_requires_rationale_but_no_handoff_is_allowed(self) -> None:
        payload = load_json(
            VALID_FIXTURES / "anomaly-proposed.observation.json"
        )

        without_rationale = copy.deepcopy(payload)
        del without_rationale["external_recommendation"]["severity_rationale"]
        errors = list(self.validator.iter_errors(without_rationale))
        self.assertTrue(errors)
        self.assertIn("severity_rationale", "\n".join(e.message for e in errors))

        no_handoff = copy.deepcopy(payload)
        no_handoff["handoff_status"] = "NONE"
        del no_handoff["external_recommendation"]
        self.validator.validate(no_handoff)

    def test_identity_preserves_arrays_absence_null_and_schema_version(self) -> None:
        payload = load_json(VALID_FIXTURES / "nominal.observation.json")

        reordered_array = copy.deepcopy(payload)
        reordered_array["limits"] = ["second", "first"]
        opposite_array = copy.deepcopy(reordered_array)
        opposite_array["limits"].reverse()
        self.assertNotEqual(observation_ref(reordered_array), observation_ref(opposite_array))

        absent = {"field": "value"}
        explicit_null = {"field": "value", "optional": None}
        self.assertNotEqual(observation_ref(absent), observation_ref(explicit_null))

        changed_version = copy.deepcopy(payload)
        changed_version["schema"] = "DOGGOSecurityObservation/v0.2"
        self.assertNotEqual(observation_ref(payload), observation_ref(changed_version))

        unicode_payload = {"signal": "D.O.G.G.O. beobachtet präzise"}
        self.assertEqual(
            canonical_json_bytes(unicode_payload),
            '{"signal":"D.O.G.G.O. beobachtet präzise"}'.encode("utf-8"),
        )

        with self.assertRaisesRegex(ValueError, "non-finite"):
            canonical_json_bytes({"not_a_number": math.nan})


if __name__ == "__main__":
    unittest.main()
