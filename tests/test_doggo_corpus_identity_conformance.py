from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import unittest
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).parents[1]
OBSERVATION_SCHEMA_PATH = (
    ROOT / "contracts" / "doggo-security-observation.v0.1.schema.json"
)
BINDING_SCHEMA_PATH = (
    ROOT
    / "contracts"
    / "doggo-security-observation-identity-binding.v0.1.schema.json"
)
VALID_FIXTURES = ROOT / "fixtures" / "valid"
IDENTITY_FIXTURES = ROOT / "fixtures" / "identity"
GOLDEN_PATH = IDENTITY_FIXTURES / "nominal.corpus-v0.1.golden.json"
BINDING_PATH = IDENTITY_FIXTURES / "nominal.corpus-v0.1.identity-binding.json"

PROFILE_ID = "CorpusContentIdentityProfile/v0.1"
DOMAIN_SEPARATOR = b"CorpusContentIdentityProfile/v0.1\x00"
OBSERVATION_TYPE = "DOGGOSecurityObservation/v0.1"
BINDING_TYPE = "DOGGOSecurityObservationIdentityBinding/v0.1"
PROJECTION_ID = "FULL_DOGGO_SECURITY_OBSERVATION_V0_1"
MIN_INTEGER = -(2**63)
MAX_INTEGER = 2**63 - 1
UTC_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def canonical_json_bytes(value: object) -> bytes:
    def validate(node: object, path: str = "projection") -> None:
        if node is None or isinstance(node, bool):
            return
        if isinstance(node, str):
            node.encode("utf-8", errors="strict")
            return
        if isinstance(node, int):
            if not MIN_INTEGER <= node <= MAX_INTEGER:
                raise ValueError(f"{path} integer is outside signed 64-bit range")
            return
        if isinstance(node, float):
            raise ValueError(f"{path} floats are not admitted")
        if isinstance(node, list):
            for index, item in enumerate(node):
                validate(item, f"{path}[{index}]")
            return
        if isinstance(node, dict):
            for key, item in node.items():
                if not isinstance(key, str):
                    raise ValueError(f"{path} object keys must be strings")
                key.encode("utf-8", errors="strict")
                validate(item, f"{path}.{key}")
            return
        raise ValueError(f"{path} contains a non-JSON profile value")

    validate(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def local_legacy_ref(observation: dict) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(observation)).hexdigest()


def identity_envelope(observation: dict, *, contract_type: str = OBSERVATION_TYPE) -> dict:
    return {
        "profile": PROFILE_ID,
        "type": contract_type,
        "projection": observation,
    }


def corpus_profile_ref(observation: dict, *, contract_type: str = OBSERVATION_TYPE) -> str:
    envelope = identity_envelope(observation, contract_type=contract_type)
    preimage = DOMAIN_SEPARATOR + canonical_json_bytes(envelope)
    return "sha256:" + hashlib.sha256(preimage).hexdigest()


def validate_timestamp(value: object) -> None:
    if not isinstance(value, str) or UTC_TIMESTAMP.fullmatch(value) is None:
        raise ValueError("identity-bearing timestamp is not canonical UTC with six fractional digits")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise ValueError("identity-bearing timestamp is not a valid UTC instant") from exc


def validate_projection_timestamps(observation: dict) -> None:
    evidence_boundary = observation["evidence_boundary"]
    if evidence_boundary.get("status") == "SUPPLIED":
        for source in evidence_boundary["sources"]:
            validate_timestamp(source["collected_at"])

    time_window = observation["time_window"]
    if time_window.get("status") == "SUPPLIED":
        validate_timestamp(time_window["start"])
        validate_timestamp(time_window["end"])

    for item in observation["observations"]:
        validate_timestamp(item["observed_at"])


class DOGGOCorpusIdentityConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.observation_schema = load_json(OBSERVATION_SCHEMA_PATH)
        cls.binding_schema = load_json(BINDING_SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.observation_schema)
        Draft202012Validator.check_schema(cls.binding_schema)
        cls.observation_validator = Draft202012Validator(
            cls.observation_schema,
            format_checker=FormatChecker(),
        )
        cls.binding_validator = Draft202012Validator(cls.binding_schema)

    def validate_identity_projection(self, observation: dict) -> None:
        self.observation_validator.validate(observation)
        validate_projection_timestamps(observation)
        canonical_json_bytes(observation)

    def test_binding_schema_is_closed_identity_metadata_only(self) -> None:
        properties = self.binding_schema["properties"]
        self.assertFalse(self.binding_schema["additionalProperties"])
        self.assertEqual(properties["schema"]["const"], BINDING_TYPE)
        self.assertEqual(properties["identity_profile"]["const"], PROFILE_ID)
        self.assertEqual(properties["identity_projection"]["const"], PROJECTION_ID)
        self.assertEqual(
            properties["content_ref"]["properties"]["type"]["const"],
            OBSERVATION_TYPE,
        )
        for forbidden in ("authority", "effect", "handoff", "admission", "canonical"):
            self.assertNotIn(forbidden, properties)

    def test_golden_vector_reproduces_exact_corpus_profile_identity(self) -> None:
        vector = load_json(GOLDEN_PATH)
        observation = vector["logical_observation"]
        self.validate_identity_projection(observation)

        envelope = identity_envelope(observation)
        canonical = canonical_json_bytes(envelope)
        preimage = DOMAIN_SEPARATOR + canonical
        digest = hashlib.sha256(preimage).hexdigest()
        typed_ref = {"type": OBSERVATION_TYPE, "ref": f"sha256:{digest}"}
        binding = {
            "schema": BINDING_TYPE,
            "identity_profile": PROFILE_ID,
            "identity_projection": PROJECTION_ID,
            "content_ref": typed_ref,
        }

        self.assertEqual(vector["identity_envelope"], envelope)
        self.assertEqual(vector["canonical_text"], canonical.decode("utf-8"))
        self.assertEqual(vector["canonical_utf8_hex"], canonical.hex())
        self.assertEqual(vector["preimage_hex"], preimage.hex())
        self.assertEqual(vector["digest"], digest)
        self.assertEqual(vector["typed_ref"], typed_ref)
        self.assertEqual(vector["binding"], binding)
        self.assertEqual(load_json(BINDING_PATH), binding)
        self.binding_validator.validate(binding)

    def test_existing_refs_remain_legacy_and_are_not_profile_bindings(self) -> None:
        for observation_path in sorted(VALID_FIXTURES.glob("*.observation.json")):
            with self.subTest(fixture=observation_path.name):
                observation = load_json(observation_path)
                legacy_ref = load_json(
                    observation_path.with_name(
                        observation_path.name.replace(".observation.json", ".ref.json")
                    )
                )
                self.assertEqual(legacy_ref["ref"], local_legacy_ref(observation))
                self.assertNotEqual(legacy_ref["ref"], corpus_profile_ref(observation))
                self.assertEqual(set(legacy_ref), {"type", "ref"})
                with self.assertRaises(ValidationError):
                    self.binding_validator.validate(legacy_ref)

    def test_legacy_timestamp_precision_is_explicitly_not_silently_normalized(self) -> None:
        nonconforming: set[str] = set()
        for path in sorted(VALID_FIXTURES.glob("*.observation.json")):
            observation = load_json(path)
            self.observation_validator.validate(observation)
            try:
                validate_projection_timestamps(observation)
            except ValueError:
                nonconforming.add(path.name)

        self.assertEqual(
            nonconforming,
            {"anomaly-proposed.observation.json", "nominal.observation.json"},
        )

    def test_binding_rejects_missing_wrong_and_additional_profile_context(self) -> None:
        binding = load_json(BINDING_PATH)
        invalid_bindings = []

        missing_profile = copy.deepcopy(binding)
        del missing_profile["identity_profile"]
        invalid_bindings.append(missing_profile)

        wrong_profile = copy.deepcopy(binding)
        wrong_profile["identity_profile"] = "DOGGOLocalIdentity/v0.1"
        invalid_bindings.append(wrong_profile)

        extra_field = copy.deepcopy(binding)
        extra_field["authority"] = "NONE"
        invalid_bindings.append(extra_field)

        wrong_type = copy.deepcopy(binding)
        wrong_type["content_ref"]["type"] = "DOGGOSecurityObservation/v0.2"
        invalid_bindings.append(wrong_type)

        for candidate in invalid_bindings:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValidationError):
                    self.binding_validator.validate(candidate)

    def test_binding_rejects_uppercase_short_and_long_digests(self) -> None:
        binding = load_json(BINDING_PATH)
        for digest in ("A" * 64, "a" * 63, "a" * 65):
            candidate = copy.deepcopy(binding)
            candidate["content_ref"]["ref"] = f"sha256:{digest}"
            with self.subTest(digest=digest):
                with self.assertRaises(ValidationError):
                    self.binding_validator.validate(candidate)

    def test_projection_is_full_document_without_field_or_default_rewriting(self) -> None:
        observation = load_json(GOLDEN_PATH)["logical_observation"]

        incomplete = copy.deepcopy(observation)
        del incomplete["limits"]
        with self.assertRaises(ValidationError):
            self.observation_validator.validate(incomplete)

        silent_default = copy.deepcopy(observation)
        silent_default["delivery_status"] = "NONE"
        with self.assertRaises(ValidationError):
            self.observation_validator.validate(silent_default)

        explicit_null = copy.deepcopy(observation)
        explicit_null["external_recommendation"] = None
        self.assertNotEqual(corpus_profile_ref(observation), corpus_profile_ref(explicit_null))
        with self.assertRaises(ValidationError):
            self.observation_validator.validate(explicit_null)

    def test_array_order_and_unicode_scalar_sequence_remain_identity_bearing(self) -> None:
        observation = load_json(GOLDEN_PATH)["logical_observation"]
        first = copy.deepcopy(observation)
        first["limits"] = ["first", "second"]
        second = copy.deepcopy(first)
        second["limits"].reverse()
        self.validate_identity_projection(first)
        self.validate_identity_projection(second)
        self.assertNotEqual(corpus_profile_ref(first), corpus_profile_ref(second))

        composed = copy.deepcopy(observation)
        composed["requested_signal"]["signal"] = "caf\u00e9"
        decomposed = copy.deepcopy(observation)
        decomposed["requested_signal"]["signal"] = "cafe\u0301"
        self.assertNotEqual(corpus_profile_ref(composed), corpus_profile_ref(decomposed))

    def test_profile_rejects_floats_nonfinite_and_out_of_range_integers(self) -> None:
        observation = load_json(GOLDEN_PATH)["logical_observation"]
        for value in (1.0, -0.0, math.nan, math.inf, -math.inf):
            candidate = copy.deepcopy(observation)
            candidate["inferences"] = [
                {"statement": "invalid numeric form", "basis_observation_indices": [value]}
            ]
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "floats"):
                    corpus_profile_ref(candidate)

        for value in (MIN_INTEGER - 1, MAX_INTEGER + 1):
            candidate = copy.deepcopy(observation)
            candidate["inferences"] = [
                {"statement": "invalid integer range", "basis_observation_indices": [value]}
            ]
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "signed 64-bit"):
                    corpus_profile_ref(candidate)

    def test_offset_timestamp_is_not_silently_normalized(self) -> None:
        observation = load_json(GOLDEN_PATH)["logical_observation"]
        offset = copy.deepcopy(observation)
        offset["time_window"]["start"] = "2026-09-27T14:00:00.000000+02:00"
        self.observation_validator.validate(offset)
        with self.assertRaisesRegex(ValueError, "canonical UTC"):
            validate_projection_timestamps(offset)

    def test_contract_type_is_bound_into_the_digest(self) -> None:
        observation = load_json(GOLDEN_PATH)["logical_observation"]
        self.assertNotEqual(
            corpus_profile_ref(observation),
            corpus_profile_ref(
                observation,
                contract_type="DOGGOSecurityObservation/v0.2",
            ),
        )


if __name__ == "__main__":
    unittest.main()
