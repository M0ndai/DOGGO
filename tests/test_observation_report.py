"""Exercise the report schema locally; no remote references are resolved."""

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


class ReportContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = json.loads(
            (ROOT / "schemas/observation-report.schema.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        cls.validator = Draft202012Validator(schema)

    def setUp(self):
        self.report = {
            "observation": {"subject": "service-A", "scope_ref": "scope-1"},
            "assessment": {"status": "ATTENTION"},
            "claims": {
                "observed": [],
                "inferred": [{
                    "statement": "Availability may be degraded.",
                    "basis": ["evidence-1"],
                    "derivation": "The supplied snapshot shows three failed probes.",
                }],
                "unknown": [],
                "limits": [],
            },
            "proposal": {"external_actions": []},
            "doggo": {"authority_used": "NONE", "effects_produced": "NONE"},
        }

    def test_accepts_inference_with_visible_derivation(self):
        self.assertTrue(self.validator.is_valid(self.report))

    def test_rejects_reference_only_inference(self):
        del self.report["claims"]["inferred"][0]["derivation"]
        self.assertFalse(self.validator.is_valid(self.report))

    def test_rejects_empty_or_blank_derivation(self):
        for value in ("", " ", "\n\t"):
            with self.subTest(value=value):
                self.report["claims"]["inferred"][0]["derivation"] = value
                self.assertFalse(self.validator.is_valid(self.report))

    def test_rejects_empty_inference_basis(self):
        self.report["claims"]["inferred"][0]["basis"] = []
        self.assertFalse(self.validator.is_valid(self.report))

    def test_rejects_observation_without_provenance(self):
        self.report["claims"]["observed"] = [
            {"statement": "Three probes failed.", "evidence_refs": []}
        ]
        self.assertFalse(self.validator.is_valid(self.report))

    def test_rejects_authority_effect_and_execution_fields(self):
        # Start from an otherwise valid carrier, so rejection has a clear cause.
        for field in ("authority_used", "effects_produced"):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.report)
                candidate["doggo"][field] = "WRITE"
                self.assertFalse(self.validator.is_valid(candidate))
        candidate = copy.deepcopy(self.report)
        candidate["execution"] = {"command": "repair"}
        self.assertFalse(self.validator.is_valid(candidate))

    def test_accepts_report_without_inferred_claims(self):
        self.report["claims"]["inferred"] = []
        self.assertTrue(self.validator.is_valid(self.report))


if __name__ == "__main__":
    unittest.main()
