"""Binding between the successor implementation and the Genesis identity core.

Genesis (`contracts/doggo-genesis-v0.1.json`) is the identity authority: it fixes
the name, the role, `authority: NONE`, `effect_capability: NONE`, the lifecycle
ending in `NO_ACTION`, the evidence rules, the scope rules, and the four
prohibited actions.

The successor adds observation and landscape contracts. Adding contracts must not
be able to weaken Genesis, so this module asserts the binding rather than trusting
that nobody edited a field.

CONTENT_SUCCESSOR != SHARED_GIT_HISTORY. The successor tree shares no Git object
with the Genesis history; this file binds them by content, not by ancestry.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GENESIS_PATH = REPO_ROOT / "contracts" / "doggo-genesis-v0.1.json"
CONTRACTS_DIR = REPO_ROOT / "contracts"

#: Every schema the successor contributes.
SUCCESSOR_SCHEMAS = sorted(
    path
    for path in CONTRACTS_DIR.rglob("*.schema.json")
    if path.name != "doggo-genesis-v0.1.json"
)


def load_genesis() -> dict:
    return json.loads(GENESIS_PATH.read_text(encoding="utf-8"))


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class SuccessorGenesisBindingTests(unittest.TestCase):
    """The successor may extend Genesis. It may not contradict or erase it."""

    def test_genesis_contract_is_retained_unchanged(self) -> None:
        self.assertTrue(GENESIS_PATH.is_file(), "the Genesis contract must be retained")
        genesis = load_genesis()
        self.assertEqual(genesis["identity"]["name"], "D.O.G.G.O.")
        self.assertEqual(genesis["identity"]["role"], "WATCHDOG_OBSERVER")
        self.assertEqual(genesis["authority"], "NONE")
        self.assertEqual(genesis["effect_capability"], "NONE")
        self.assertEqual(genesis["lifecycle"][-1], "NO_ACTION")

    def test_successor_contributes_schemas(self) -> None:
        self.assertTrue(
            SUCCESSOR_SCHEMAS,
            "the successor is expected to contribute at least one contract schema",
        )

    def test_every_observation_schema_is_non_authoritative(self) -> None:
        """authority=NONE in Genesis must hold for every successor observation too.

        This is the actual seam: the successor expresses the same boundary
        machine-readably, so an escalation would be visible here rather than
        only in prose.
        """
        for path in SUCCESSOR_SCHEMAS:
            with self.subTest(schema=path.name):
                properties = load_schema(path).get("properties", {})
                if "authority" in properties:
                    self.assertEqual(
                        properties["authority"].get("const"),
                        "NONE",
                        f"{path.name} grants authority; Genesis forbids it",
                    )
                if "effect" in properties:
                    self.assertEqual(
                        properties["effect"].get("const"),
                        "NONE",
                        f"{path.name} claims an effect capability; Genesis forbids it",
                    )

    def test_no_successor_schema_permits_execution(self) -> None:
        """No successor schema may open an action, effect, or execution path."""
        forbidden = ("EXECUTION", "AUTHORIZATION", "PROMOTION", "CANONICAL_STATE_MUTATION")
        for path in SUCCESSOR_SCHEMAS:
            with self.subTest(schema=path.name):
                raw = path.read_text(encoding="utf-8")
                for action in forbidden:
                    self.assertNotIn(
                        f'"{action}"',
                        raw,
                        f"{path.name} names {action}, which Genesis prohibits",
                    )

    def test_identity_binding_schemas_disclaim_authority(self) -> None:
        """Binding to a Corpus identity profile must not become Corpus authority."""
        for path in SUCCESSOR_SCHEMAS:
            if "identity-binding" not in path.name:
                continue
            with self.subTest(schema=path.name):
                description = load_schema(path).get("description", "").lower()
                self.assertIn(
                    "not authority",
                    description,
                    f"{path.name} must disclaim authority in its own description",
                )

    def test_genesis_prohibitions_are_not_contradicted_by_successor_text(self) -> None:
        """Prose must not claim an authority the machine-readable core denies."""
        for name in ("README.md", "DOGGO_PERSONA.md", "AGENTS.md"):
            path = REPO_ROOT / name
            if not path.is_file():
                continue
            with self.subTest(document=name):
                text = path.read_text(encoding="utf-8")
                lowered = text.lower()
                self.assertNotIn(
                    "authority: write",
                    lowered,
                    f"{name} must not describe D.O.G.G.O. as holding write authority",
                )

    def test_observation_output_paths_are_caller_supplied(self) -> None:
        """The collector writes only where it is told, never into observed trees.

        Genesis forbids EXECUTION and CANONICAL_STATE_MUTATION. The available
        seam for proving that is the collector: its outputs are explicit CLI
        arguments, so a read-only run cannot pick a destination of its own.
        """
        source = (REPO_ROOT / "collector" / "landscape_collect.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("--observations-out", source)
        self.assertIn("--snapshot-out", source)
        self.assertIn(
            "never writes to the observed source tree",
            source,
            "the collector must state its read-only boundary where it is implemented",
        )

    def test_successor_does_not_shadow_the_genesis_contract(self) -> None:
        """No successor file may reuse the Genesis id or claim to replace it."""
        genesis = load_genesis()
        self.assertEqual(genesis["schema_version"], "0.1")
        for path in SUCCESSOR_SCHEMAS:
            with self.subTest(schema=path.name):
                self.assertNotEqual(
                    path.name,
                    "doggo-genesis-v0.1.json",
                    "a successor schema must not be named as the Genesis contract",
                )
                properties = load_schema(path).get("properties", {})
                self.assertNotEqual(
                    properties.get("schema", {}).get("const"),
                    "doggo-genesis/v0.1",
                    "a successor schema must not declare the Genesis schema id",
                )


if __name__ == "__main__":
    unittest.main()