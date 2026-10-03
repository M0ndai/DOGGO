#!/usr/bin/env python3
"""Contract conformance for the landscape observation chain.

Every check here is adversarial. A test that only feeds conforming documents
proves nothing about a contract whose job is to refuse non-conforming ones.
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import jsonschema

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts" / "landscape"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "landscape"

OBSERVATION_SCHEMA = json.loads((CONTRACTS / "landscape-observation.v0.1.schema.json").read_text())
SNAPSHOT_SCHEMA = json.loads((CONTRACTS / "landscape-snapshot.v0.1.schema.json").read_text())
OBS_BINDING_SCHEMA = json.loads(
    (CONTRACTS / "landscape-observation-identity-binding.v0.1.schema.json").read_text()
)
SNAP_BINDING_SCHEMA = json.loads(
    (CONTRACTS / "landscape-snapshot-identity-binding.v0.1.schema.json").read_text()
)

GOOD_OBSERVATION = json.loads((FIXTURES / "valid" / "observation.json").read_text())
GOOD_SNAPSHOT = json.loads((FIXTURES / "valid" / "snapshot.json").read_text())
GOOD_OBS_BINDING = json.loads((FIXTURES / "valid" / "observation-identity-binding.json").read_text())


def observation_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(OBSERVATION_SCHEMA)


def snapshot_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(SNAPSHOT_SCHEMA)


def first_error(validator: jsonschema.Draft202012Validator, document: object) -> str | None:
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    return errors[0].message if errors else None


class PositiveFixtures(unittest.TestCase):
    def test_observation_is_valid(self) -> None:
        self.assertIsNone(first_error(observation_validator(), GOOD_OBSERVATION))

    def test_snapshot_is_valid(self) -> None:
        self.assertIsNone(first_error(snapshot_validator(), GOOD_SNAPSHOT))

    def test_observation_binding_is_valid(self) -> None:
        validator = jsonschema.Draft202012Validator(OBS_BINDING_SCHEMA)
        self.assertIsNone(first_error(validator, GOOD_OBS_BINDING))

    def test_observation_carries_no_snapshot_reference(self) -> None:
        """Membership is one-way. An observation must not reference a snapshot."""

        self.assertNotIn("snapshot_ref", GOOD_OBSERVATION)
        self.assertEqual(OBSERVATION_SCHEMA.get("additionalProperties"), False)

    def test_freshness_makes_no_probabilistic_claim(self) -> None:
        freshness = GOOD_OBSERVATION["freshness"]
        self.assertEqual(freshness["status"], "FRESH_AT_OBSERVATION")
        self.assertEqual(freshness["decay_model"], "NONE")
        self.assertNotIn("probability", json.dumps(freshness))

    def test_authority_and_effect_are_none(self) -> None:
        for document in (GOOD_OBSERVATION, GOOD_SNAPSHOT, GOOD_OBS_BINDING):
            if "authority" in document:
                self.assertEqual(document["authority"], "NONE")
            if "effect" in document:
                self.assertEqual(document["effect"], "NONE")


class ObservationRejections(unittest.TestCase):
    """Each case is a near-miss that must fail closed."""

    def assertRejected(self, mutate, expected_fragment: str) -> None:
        document = copy.deepcopy(GOOD_OBSERVATION)
        mutate(document)
        message = first_error(observation_validator(), document)
        self.assertIsNotNone(message, "contract accepted a document it must refuse")
        self.assertIn(expected_fragment.lower(), message.lower())

    def test_authority_request_is_rejected(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("authority", "APPLY"), "NONE")

    def test_effect_command_is_rejected(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("effect", "WRITE"), "NONE")

    def test_second_precision_timestamp_is_rejected(self) -> None:
        self.assertRejected(
            lambda d: d["freshness"].__setitem__("observed_at", "2026-09-28T22:40:24Z"),
            "does not match",
        )

    def test_timezone_offset_is_rejected(self) -> None:
        self.assertRejected(
            lambda d: d["freshness"].__setitem__("observed_at", "2026-09-28T22:40:24+02:00"),
            "does not match",
        )

    def test_missing_limits_is_rejected(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("limits", []), "non-empty")

    def test_float_claim_value_is_rejected(self) -> None:
        self.assertRejected(
            lambda d: d["claims"][0].__setitem__("integer_value", 37.5), "not of type"
        )

    def test_claim_without_any_typed_value_is_rejected(self) -> None:
        def mutate(document: dict) -> None:
            for key in ("integer_value", "string_value", "boolean_value"):
                document["claims"][0].pop(key, None)

        self.assertRejected(mutate, "valid")

    def test_claim_with_two_typed_values_is_rejected(self) -> None:
        def mutate(document: dict) -> None:
            document["claims"][0]["string_value"] = "also"

        self.assertRejected(mutate, "valid")

    def test_observation_without_observations_is_rejected(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("observations", []), "non-empty")

    def test_inference_must_cite_an_observation(self) -> None:
        self.assertRejected(
            lambda d: d["inferences"].append(
                {"statement": "likely a service", "basis_observation_indices": []}
            ),
            "non-empty",
        )

    def test_decay_model_must_be_none(self) -> None:
        self.assertRejected(
            lambda d: d["freshness"].__setitem__("decay_model", "EXPONENTIAL"), "NONE"
        )

    def test_project_id_must_be_derived_not_named(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("project_id", "BloodMoon"), "does not match")

    def test_unknown_field_is_rejected(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("semantic_dimensions", {}), "Additional")


class SnapshotRejections(unittest.TestCase):
    def assertRejected(self, mutate, expected_fragment: str) -> None:
        document = copy.deepcopy(GOOD_SNAPSHOT)
        mutate(document)
        message = first_error(snapshot_validator(), document)
        self.assertIsNotNone(message, "contract accepted a document it must refuse")
        self.assertIn(expected_fragment.lower(), message.lower())

    def test_duplicate_observation_ref_is_rejected(self) -> None:
        def mutate(document: dict) -> None:
            document["project_observation_refs"].append(document["project_observation_refs"][0])

        self.assertRejected(mutate, "unique")

    def test_empty_membership_is_rejected(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("project_observation_refs", []), "non-empty")

    def test_missing_limits_is_rejected(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("limits", []), "non-empty")

    def test_exclusion_claiming_enumeration_is_rejected(self) -> None:
        def mutate(document: dict) -> None:
            document["completeness"]["exclusions"][0]["enumerated"] = "YES"

        self.assertRejected(mutate, "NOT_ENUMERATED")

    def test_observation_ref_type_is_constrained(self) -> None:
        """A snapshot may only claim membership over project observations."""

        def mutate(document: dict) -> None:
            document["project_observation_refs"][0]["type"] = "SomethingElse/v0.1"

        self.assertRejected(mutate, "was expected")

    def test_authority_is_rejected(self) -> None:
        self.assertRejected(lambda d: d.__setitem__("authority", "GRANT"), "NONE")


class BindingRejections(unittest.TestCase):
    def test_binding_to_wrong_projection_is_rejected(self) -> None:
        document = copy.deepcopy(GOOD_OBS_BINDING)
        document["identity_projection"] = "FULL_DOGGO_SECURITY_OBSERVATION_V0_1"
        validator = jsonschema.Draft202012Validator(OBS_BINDING_SCHEMA)
        self.assertIsNotNone(first_error(validator, document))

    def test_binding_to_wrong_type_is_rejected(self) -> None:
        document = copy.deepcopy(GOOD_OBS_BINDING)
        document["content_ref"]["type"] = "LandscapeSnapshot/v0.1"
        validator = jsonschema.Draft202012Validator(OBS_BINDING_SCHEMA)
        self.assertIsNotNone(first_error(validator, document))

    def test_snapshot_binding_binds_snapshot_type(self) -> None:
        document = json.loads((FIXTURES / "valid" / "snapshot-identity-binding.json").read_text())
        validator = jsonschema.Draft202012Validator(SNAP_BINDING_SCHEMA)
        self.assertIsNone(first_error(validator, document))


if __name__ == "__main__":
    unittest.main(verbosity=2)
