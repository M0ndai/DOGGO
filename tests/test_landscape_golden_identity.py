#!/usr/bin/env python3
"""Verify the landscape golden identity vectors.

This suite freezes identity values and re-derives them. It is the regression
net for the exact failure the chain originally hit: hashing a bare payload
instead of the closed envelope mints a different, incompatible identity under
the same contract type name. Every vector here is reproduced from the committed
fixture documents, and each binding is validated against its own schema.
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any

import jsonschema

REPO = Path(__file__).resolve().parents[1]
CONTRACTS = REPO / "contracts" / "landscape"
FIXTURES = REPO / "fixtures" / "landscape"
CORPUS_SRC = Path("/home/blackmonolith/Corpus/Corpus-alpha/src")

GOLDEN = json.loads((FIXTURES / "landscape-identity.golden.json").read_text())
OBSERVATION = json.loads((FIXTURES / "valid" / "observation.json").read_text())
SNAPSHOT = json.loads((FIXTURES / "valid" / "snapshot.json").read_text())

PROFILE = "CorpusContentIdentityProfile/v0.1"
DOMAIN = b"CorpusContentIdentityProfile/v0.1\x00"
MEMBERSHIP_DOMAIN = b"mycodeindex.landscape-membership/0.1\x00"
OBS_TYPE = "LandscapeObservation/v0.1"
SNAP_TYPE = "LandscapeSnapshot/v0.1"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def local_identity(contract_type: str, projection: Any) -> str:
    envelope = {"profile": PROFILE, "type": contract_type, "projection": projection}
    return "sha256:" + hashlib.sha256(DOMAIN + canonical(envelope)).hexdigest()


def corpus_identity(contract_type: str, projection: Any) -> str:
    if str(CORPUS_SRC) not in sys.path:
        sys.path.insert(0, str(CORPUS_SRC))
    from corpus_snapshot_core.content_identity import typed_content_ref

    return typed_content_ref(
        {"profile": PROFILE, "type": contract_type, "projection": projection}
    ).ref


class GoldenVectorsAreFrozen(unittest.TestCase):
    def test_observation_vector_is_reproducible(self) -> None:
        expected = GOLDEN["vectors"]["observation"]["typed_ref"]["ref"]
        self.assertEqual(local_identity(OBS_TYPE, OBSERVATION), expected)

    def test_snapshot_vector_is_reproducible(self) -> None:
        expected = GOLDEN["vectors"]["snapshot"]["typed_ref"]["ref"]
        self.assertEqual(local_identity(SNAP_TYPE, SNAPSHOT), expected)

    def test_membership_root_is_reproducible(self) -> None:
        expected = GOLDEN["vectors"]["membership_root"]["typed_ref"]["ref"]
        self.assertEqual(
            "sha256:"
            + hashlib.sha256(MEMBERSHIP_DOMAIN + canonical(SNAPSHOT["project_observation_refs"])).hexdigest(),
            expected,
        )

    def test_observation_and_snapshot_identities_differ(self) -> None:
        self.assertNotEqual(
            GOLDEN["vectors"]["observation"]["typed_ref"]["ref"],
            GOLDEN["vectors"]["snapshot"]["typed_ref"]["ref"],
        )

    def test_membership_root_differs_from_snapshot_content_identity(self) -> None:
        """The membership root is internal; the content identity is external."""

        self.assertNotEqual(
            GOLDEN["vectors"]["membership_root"]["typed_ref"]["ref"],
            GOLDEN["vectors"]["snapshot"]["typed_ref"]["ref"],
        )


class CrossImplementationAgreement(unittest.TestCase):
    def test_observation_matches_the_corpus_reference_implementation(self) -> None:
        self.assertEqual(
            local_identity(OBS_TYPE, OBSERVATION),
            corpus_identity(OBS_TYPE, OBSERVATION),
        )

    def test_snapshot_matches_the_corpus_reference_implementation(self) -> None:
        self.assertEqual(
            local_identity(SNAP_TYPE, SNAPSHOT),
            corpus_identity(SNAP_TYPE, SNAPSHOT),
        )


class EnvelopeIsNotPayload(unittest.TestCase):
    """The original defect: a bare-payload hash is a different identity."""

    def test_bare_payload_hash_is_not_the_profile_identity(self) -> None:
        bare = "sha256:" + hashlib.sha256(canonical(OBSERVATION)).hexdigest()
        self.assertNotEqual(bare, GOLDEN["vectors"]["observation"]["typed_ref"]["ref"])

    def test_preimage_carries_profile_and_type(self) -> None:
        preimage = bytes.fromhex(GOLDEN["vectors"]["observation"]["preimage_hex"])
        self.assertTrue(preimage.startswith(DOMAIN))
        self.assertIn(OBS_TYPE.encode("utf-8"), preimage)

    def test_profile_participates_in_the_digest(self) -> None:
        """A different profile must not produce the same ref."""

        other_domain = b"SomeOtherProfile/v0.1\x00"
        other = "sha256:" + hashlib.sha256(
            other_domain
            + canonical({"profile": "SomeOtherProfile/v0.1", "type": OBS_TYPE, "projection": OBSERVATION})
        ).hexdigest()
        self.assertNotEqual(other, GOLDEN["vectors"]["observation"]["typed_ref"]["ref"])


class BindingsMatchTheGoldenVectors(unittest.TestCase):
    def test_observation_binding_is_schema_valid_and_matches(self) -> None:
        schema = json.loads(
            (CONTRACTS / "landscape-observation-identity-binding.v0.1.schema.json").read_text()
        )
        binding = GOLDEN["vectors"]["observation"]["binding"]
        self.assertIsNone(
            next(iter(jsonschema.Draft202012Validator(schema).iter_errors(binding)), None)
        )
        self.assertEqual(
            binding["content_ref"]["ref"],
            GOLDEN["vectors"]["observation"]["typed_ref"]["ref"],
        )

    def test_snapshot_binding_is_schema_valid_and_matches(self) -> None:
        schema = json.loads(
            (CONTRACTS / "landscape-snapshot-identity-binding.v0.1.schema.json").read_text()
        )
        binding = GOLDEN["vectors"]["snapshot"]["binding"]
        self.assertIsNone(
            next(iter(jsonschema.Draft202012Validator(schema).iter_errors(binding)), None)
        )
        self.assertEqual(
            binding["content_ref"]["ref"],
            GOLDEN["vectors"]["snapshot"]["typed_ref"]["ref"],
        )

    def test_committed_fixtures_agree_with_the_golden_vectors(self) -> None:
        observation_binding = json.loads(
            (FIXTURES / "valid" / "observation-identity-binding.json").read_text()
        )
        self.assertEqual(
            observation_binding["content_ref"]["ref"],
            GOLDEN["vectors"]["observation"]["typed_ref"]["ref"],
        )
        snapshot_binding = json.loads(
            (FIXTURES / "valid" / "snapshot-identity-binding.json").read_text()
        )
        self.assertEqual(
            snapshot_binding["content_ref"]["ref"],
            GOLDEN["vectors"]["snapshot"]["typed_ref"]["ref"],
        )


class MembershipIntegrity(unittest.TestCase):
    def test_every_member_ref_resolves_to_the_golden_observation(self) -> None:
        members = SNAPSHOT["project_observation_refs"]
        self.assertEqual(len(members), 1)
        self.assertEqual(
            members[0]["ref"], GOLDEN["vectors"]["observation"]["typed_ref"]["ref"]
        )

    def test_member_refs_are_canonically_ordered(self) -> None:
        refs = [entry["ref"] for entry in SNAPSHOT["project_observation_refs"]]
        self.assertEqual(refs, sorted(refs))

    def test_snapshot_contains_no_observation_content(self) -> None:
        serialized = json.dumps(SNAPSHOT, sort_keys=True)
        self.assertNotIn(OBSERVATION["project_id"], serialized)
        self.assertNotIn(OBSERVATION["project_root"], serialized)

    def test_completeness_never_claims_enumeration_it_lacks(self) -> None:
        exclusions = SNAPSHOT["completeness"]["exclusions"]
        self.assertTrue(exclusions)
        for exclusion in exclusions:
            self.assertEqual(exclusion["enumerated"], "NOT_ENUMERATED")

    def test_boundaries_are_recorded(self) -> None:
        boundaries = GOLDEN["boundaries"]
        self.assertTrue(boundaries["content_identity != authority"])
        self.assertTrue(boundaries["content_identity != existence"])
        self.assertTrue(boundaries["membership != landscape_completeness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
