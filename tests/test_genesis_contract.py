"""Contract tests for the intentionally non-authoritative DOGGO Genesis slice."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path


CONTRACT_PATH = (
    Path(__file__).resolve().parents[1]
    / "contracts"
    / "doggo-genesis-v0.1.json"
)
LIFECYCLE = ["OBSERVE", "DETECT", "COMPARE", "REPORT", "NO_ACTION"]
PROHIBITED_ACTIONS = {
    "CANONICAL_STATE_MUTATION",
    "EXECUTION",
    "AUTHORIZATION",
    "PROMOTION",
}
TOP_LEVEL_FIELDS = {
    "schema_version",
    "identity",
    "authority",
    "effect_capability",
    "lifecycle",
    "evidence",
    "scope",
    "prohibited_actions",
}
DOGGO_ADVERSARIAL_PROBES = (
    (
        "DOGGO-P001 capability injection",
        lambda contract: contract.update({"allowed_actions": ["EXECUTION"]}),
        "unexpected contract fields: allowed_actions",
    ),
    (
        "DOGGO-P002 identity replacement",
        lambda contract: contract["identity"].update({"name": "PUPPY"}),
        "identity.name must be D.O.G.G.O.",
    ),
    (
        "DOGGO-P003 malformed identity",
        lambda contract: contract.update({"identity": []}),
        "identity must be an object",
    ),
    (
        "DOGGO-P004 malformed evidence",
        lambda contract: contract.update({"evidence": []}),
        "evidence must be an object",
    ),
    (
        "DOGGO-P005 malformed scope",
        lambda contract: contract.update({"scope": []}),
        "scope must be an object",
    ),
    (
        "DOGGO-P006 malformed prohibition list",
        lambda contract: contract.update({"prohibited_actions": [{}]}),
        "prohibited_actions must be a list of strings",
    ),
)


def load_contract() -> dict:
    with CONTRACT_PATH.open(encoding="utf-8") as contract_file:
        return json.load(contract_file)


def object_field(container: dict, field: str, errors: list[str]) -> dict:
    value = container.get(field)
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return {}
    return value


def validate_contract(contract: dict) -> list[str]:
    """Return every Genesis-boundary violation without granting any authority."""
    errors = []

    if not isinstance(contract, dict):
        return ["contract must be an object"]

    if contract.get("schema_version") != "0.1":
        errors.append("schema_version must be 0.1")
    unexpected_fields = set(contract) - TOP_LEVEL_FIELDS
    if unexpected_fields:
        errors.append(
            "unexpected contract fields: " + ", ".join(sorted(unexpected_fields))
        )

    identity = object_field(contract, "identity", errors)
    if identity.get("name") != "D.O.G.G.O.":
        errors.append("identity.name must be D.O.G.G.O.")
    if identity.get("role") != "WATCHDOG_OBSERVER":
        errors.append("identity.role must be WATCHDOG_OBSERVER")
    if contract.get("authority") != "NONE":
        errors.append("authority must be NONE")
    if contract.get("effect_capability") != "NONE":
        errors.append("effect_capability must be NONE")
    if contract.get("lifecycle") != LIFECYCLE:
        errors.append("lifecycle must end with NO_ACTION after REPORT")

    evidence = object_field(contract, "evidence", errors)
    observation = object_field(evidence, "observation", errors)
    if observation.get("evidence_required") is not True:
        errors.append("observation must require evidence")
    inference = object_field(evidence, "inference", errors)
    if inference.get("label_required") is not True:
        errors.append("inference must be labelled")
    if inference.get("must_not_be_presented_as_observation") is not True:
        errors.append("inference must remain distinct from observation")
    missing_evidence = object_field(evidence, "missing_evidence", errors)
    if missing_evidence.get("report_visibility") != "REQUIRED":
        errors.append("missing evidence must be visible in reports")

    scope = object_field(contract, "scope", errors)
    if scope.get("explicit_scope_required") is not True:
        errors.append("scope must be explicit")
    if scope.get("implicit_expansion") != "FORBIDDEN":
        errors.append("implicit scope expansion must be forbidden")

    raw_prohibited_actions = contract.get("prohibited_actions")
    if not isinstance(raw_prohibited_actions, list) or not all(
        isinstance(action, str) for action in raw_prohibited_actions
    ):
        errors.append("prohibited_actions must be a list of strings")
        raw_prohibited_actions = []
    prohibited_actions = set(raw_prohibited_actions)
    missing_prohibitions = PROHIBITED_ACTIONS - prohibited_actions
    if missing_prohibitions:
        errors.append(
            "missing prohibited actions: " + ", ".join(sorted(missing_prohibitions))
        )

    return errors


class GenesisContractTests(unittest.TestCase):
    def test_current_contract_satisfies_genesis_boundary(self) -> None:
        self.assertEqual(validate_contract(load_contract()), [])

    def test_rejects_any_authority_or_effect_capability(self) -> None:
        for field in ("authority", "effect_capability"):
            with self.subTest(field=field):
                candidate = copy.deepcopy(load_contract())
                candidate[field] = "WRITE"
                self.assertIn(f"{field} must be NONE", validate_contract(candidate))

    def test_rejects_lifecycle_that_acts_after_reporting(self) -> None:
        candidate = copy.deepcopy(load_contract())
        candidate["lifecycle"][-1] = "EXECUTE"
        self.assertIn(
            "lifecycle must end with NO_ACTION after REPORT",
            validate_contract(candidate),
        )

    def test_doggo_adversarial_probes_are_rejected(self) -> None:
        for probe_id, mutate, expected_violation in DOGGO_ADVERSARIAL_PROBES:
            with self.subTest(probe=probe_id):
                candidate = copy.deepcopy(load_contract())
                mutate(candidate)
                self.assertIn(expected_violation, validate_contract(candidate))

    def test_rejects_hidden_missing_evidence_or_scope_expansion(self) -> None:
        candidate = copy.deepcopy(load_contract())
        candidate["evidence"]["missing_evidence"]["report_visibility"] = "OPTIONAL"
        candidate["scope"]["implicit_expansion"] = "ALLOWED"
        errors = validate_contract(candidate)
        self.assertIn("missing evidence must be visible in reports", errors)
        self.assertIn("implicit scope expansion must be forbidden", errors)

    def test_rejects_unlabelled_or_disguised_inference(self) -> None:
        candidate = copy.deepcopy(load_contract())
        candidate["evidence"]["inference"]["label_required"] = False
        candidate["evidence"]["inference"]["must_not_be_presented_as_observation"] = False
        errors = validate_contract(candidate)
        self.assertIn("inference must be labelled", errors)
        self.assertIn("inference must remain distinct from observation", errors)

    def test_rejects_removal_of_each_prohibited_action(self) -> None:
        for action in PROHIBITED_ACTIONS:
            with self.subTest(action=action):
                candidate = copy.deepcopy(load_contract())
                candidate["prohibited_actions"].remove(action)
                self.assertIn(
                    f"missing prohibited actions: {action}",
                    validate_contract(candidate),
                )


if __name__ == "__main__":
    unittest.main()
