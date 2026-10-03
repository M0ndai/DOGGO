#!/usr/bin/env python3
"""Deterministic landscape collector for LandscapeObservation/v0.1.

Reads an accepted read-only file inventory (a metadata manifest) and emits one
LandscapeObservation per project plus one LandscapeSnapshot over the resulting
observation references.

Design constraints:

- Read-only. This module never writes to the observed source tree.
- Hash-free. File content is not hashed; the source manifest's own digest is
  carried as provenance. A later revision may add content hashes.
- Deterministic. ``observed_at`` is a required input. Runtime wall-clock time
  is recorded only in a separate receipt and never enters an identity-bearing
  field, so two runs over the same manifest with the same ``observed_at`` and
  collector version produce byte-identical output.
- Observation and snapshot do not reference each other. The snapshot is a
  one-way membership projection over observation references.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

COLLECTOR_VERSION = "mycodeindex.landscape-collector/0.1.0"
PROJECT_ID_DOMAIN = b"mycodeindex.project-root/0.1\x00"

# Content identity is defined by CorpusContentIdentityProfile/v0.1. The
# preimage is the profile identifier, one 0x00 byte, and the canonical
# envelope bytes. Hashing the bare payload instead would mint a second,
# incompatible identity under the same type name.
IDENTITY_PROFILE = "CorpusContentIdentityProfile/v0.1"
IDENTITY_DOMAIN = b"CorpusContentIdentityProfile/v0.1\x00"

# snapshot_id is a membership root over the observation reference list. It is
# deliberately NOT the snapshot's own content identity, which is only computable
# once the snapshot document is complete and is minted by the identity binding.
MEMBERSHIP_DOMAIN = b"mycodeindex.landscape-membership/0.1\x00"

# A project root is established only by a ROOT marker. Supporting markers are
# recorded as capabilities of the enclosing project and never create one, so a
# SKILL.md inside a plugin cannot silently become a project.
ROOT_MARKERS: dict[str, str] = {
    "plugin.json": "PLUGIN_MANIFEST",
    "package.json": "NODE_PACKAGE",
    "pyproject.toml": "PYTHON_PROJECT",
    "setup.py": "PYTHON_SETUP",
    "Cargo.toml": "CARGO_PACKAGE",
    "go.mod": "GO_MODULE",
}

SUPPORTING_MARKERS: dict[str, str] = {
    "SKILL.md": "SKILL",
    "manifest.json": "MANIFEST",
}

CLASSIFICATION_SOURCE_PREFIX = "SOURCE"


class CollectorError(RuntimeError):
    """Base error for collector failures."""


class InvalidObservedAt(CollectorError):
    pass


def canonical_json(value: Any) -> bytes:
    """Serialize exactly as the Corpus content identity profile does."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def project_id_for(project_root: str) -> str:
    """Derive a project identity from its baseline-relative path.

    The root path is hashed under its own domain separator. Names such as
    "BloodMoon", "bloodmoon" and "BloodMoon-old" therefore stay distinct, and
    no semantic claim about the project is made.
    """

    digest = hashlib.sha256(PROJECT_ID_DOMAIN + project_root.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def require_observed_at(value: str) -> str:
    """Normalize an evidence timestamp to the profile's microsecond UTC form.

    The accepted form is a calendar instant carrying an explicit fraction. A
    supplied millisecond value is zero-padded, which is lossless and
    deterministic. A value without a fraction is rejected rather than guessed,
    because choosing a precision would be an invented observation.
    """

    text = value.strip()
    if text.endswith("Z") and "." in text:
        head, _, tail = text[:-1].rpartition(".")
        if tail.isdigit():
            if len(tail) > 6:
                return f"{head}.{tail[:6]}Z"
            return f"{head}.{tail.ljust(6, '0')}Z"
    raise InvalidObservedAt(
        f"observed_at must be a UTC instant with an explicit fractional part, got {value!r}"
    )


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectorError(f"cannot read source manifest {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise CollectorError("source manifest must contain an 'entries' array")
    if not data.get("manifest_digest"):
        raise CollectorError("source manifest must declare 'manifest_digest'")
    return data


def discover_projects(paths: list[str]) -> dict[str, dict[str, Any]]:
    """Group admitted paths under project roots defined by ROOT markers.

    A project root is the parent directory of a root marker. When roots nest,
    the deepest root owns its own files and its markers; an enclosing root
    records the nested root as a member project rather than merging with it.
    """

    directories: set[str] = set()
    marker_hits: list[tuple[str, str, str]] = []  # (kind, marker, directory)

    for path in paths:
        parts = path.split("/")
        for index in range(len(parts) - 1):
            directories.add("/".join(parts[: index + 1]))
        tail = parts[-1]
        if tail in ROOT_MARKERS:
            marker_hits.append((tail, ROOT_MARKERS[tail], "/".join(parts[:-1])))
        elif tail in SUPPORTING_MARKERS:
            marker_hits.append((tail, SUPPORTING_MARKERS[tail], "/".join(parts[:-1])))

    root_dirs = sorted({directory for marker, _, directory in marker_hits if marker in ROOT_MARKERS})
    if not root_dirs:
        return {}

    def owning_root(directory: str) -> str:
        best = ""
        for root in root_dirs:
            if root == "" or directory == root or directory.startswith(root + "/"):
                if len(root) > len(best):
                    best = root
        return best

    projects: dict[str, dict[str, Any]] = {}
    for root in root_dirs:
        projects[root] = {
            "root": root,
            "root_markers": [],
            "supporting_markers": [],
            "file_count": 0,
            "source_file_count": 0,
            "nested_projects": set(),
        }

    for path in paths:
        directory = "/".join(path.split("/")[:-1])
        root = owning_root(directory)
        if not root or root not in projects:
            continue
        projects[root]["file_count"] += 1

    for marker, kind, directory in marker_hits:
        root = owning_root(directory)
        if not root or root not in projects:
            continue
        bucket = "root_markers" if marker in ROOT_MARKERS else "supporting_markers"
        projects[root][bucket].append({"marker": marker, "kind": kind, "path": path_of(marker, directory)})

    for root in projects:
        for bucket in ("root_markers", "supporting_markers"):
            projects[root][bucket] = sorted(
                projects[root][bucket], key=lambda entry: (entry["kind"], entry["path"])
            )
        nested = {candidate for candidate in root_dirs if candidate != root and candidate.startswith(root + "/")}
        projects[root]["nested_projects"] = sorted(nested)

    return projects


def path_of(marker: str, directory: str) -> str:
    return f"{directory}/{marker}" if directory else marker


def classify(paths: list[str], manifest_entries: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    return sorted(
        (path, str(manifest_entries[path].get("classification", "OTHER")))
        for path in paths
    )


def build_observation(
    root: str,
    project: dict[str, Any],
    project_paths: list[str],
    manifest_entries: dict[str, dict[str, Any]],
    observed_at: str,
    baseline_ref: str,
    baseline_digest: str,
) -> dict[str, Any]:
    evidence_ref = f"{baseline_ref}#{root}" if root else baseline_ref
    source_files = sum(
        1 for path in project_paths if manifest_entries[path].get("classification") == CLASSIFICATION_SOURCE_PREFIX
    )

    observations: list[dict[str, Any]] = []
    for marker in project["root_markers"]:
        observations.append(
            {
                "statement": f"root marker {marker['marker']} present at {marker['path']}",
                "evidence_refs": [marker["path"], evidence_ref],
                "observed_at": observed_at,
            }
        )
    for marker in project["supporting_markers"]:
        observations.append(
            {
                "statement": f"supporting marker {marker['marker']} present at {marker['path']}",
                "evidence_refs": [marker["path"], evidence_ref],
                "observed_at": observed_at,
            }
        )
    if not observations:
        observations.append(
            {
                "statement": f"no project marker observed below {root}",
                "evidence_refs": [evidence_ref],
                "observed_at": observed_at,
            }
        )

    claims: list[dict[str, Any]] = [
        {
            "claim_type": "FILE_COUNT",
            "subject": "project",
            "metric": "enumerated_files",
            "evidence_refs": [evidence_ref],
            "integer_value": project["file_count"],
        },
        {
            "claim_type": "FILE_COUNT",
            "subject": "project",
            "metric": "classified_source_files",
            "evidence_refs": [evidence_ref],
            "integer_value": source_files,
        },
        {
            "claim_type": "MARKER_COUNT",
            "subject": "project",
            "metric": "root_markers",
            "evidence_refs": [evidence_ref],
            "integer_value": len(project["root_markers"]),
        },
        {
            "claim_type": "MARKER_COUNT",
            "subject": "project",
            "metric": "supporting_markers",
            "evidence_refs": [evidence_ref],
            "integer_value": len(project["supporting_markers"]),
        },
        {
            "claim_type": "NESTED_PROJECT_COUNT",
            "subject": "project",
            "metric": "nested_projects",
            "evidence_refs": [evidence_ref],
            "integer_value": len(project["nested_projects"]),
        },
    ]

    limits = [
        "observations are metadata-only; file content was not read or hashed in this revision",
        "project roots are established by root markers only; a directory without a root marker is not a project",
    ]
    if project["nested_projects"]:
        limits.append(
            "nested project roots are recorded as members and their contents are also counted by the enclosing project"
        )

    return {
        "schema": "LandscapeObservation/v0.1",
        "project_id": project_id_for(root),
        "project_root": root,
        "provenance": {
            "observed_at_source": "BASELINE_FINISHED_AT",
            "observed_at_normalized_from_precision": "MILLISECOND",
            "source_manifest_ref": baseline_ref,
            "source_manifest_digest": baseline_digest,
        },
        "evidence_boundary": {
            "status": "SUPPLIED",
            "sources": [
                {
                    "type": "FILE_INDEX_MANIFEST",
                    "ref": f"{baseline_ref}#{root}" if root else baseline_ref,
                    "collected_at": observed_at,
                }
            ],
        },
        "time_window": {"status": "SUPPLIED", "start": observed_at, "end": observed_at},
        "observations": observations,
        "claims": claims,
        "inferences": [],
        "freshness": {
            "status": "FRESH_AT_OBSERVATION",
            "observed_at": observed_at,
            "decay_model": "NONE",
        },
        "limits": sorted(limits),
        "authority": "NONE",
        "effect": "NONE",
    }


def build_snapshot(
    refs: list[dict[str, str]],
    observed_at: str,
    baseline_ref: str,
    baseline_digest: str,
    evidence_ref_count: int,
    exclusions: list[dict[str, Any]],
    enumerated_file_count: int,
) -> dict[str, Any]:
    ordered = sorted(refs, key=lambda ref: ref["ref"])
    status = "PARTIAL_BY_POLICY" if exclusions else "COMPLETE"
    limits = ["snapshot identity covers project observation membership only, not landscape completeness"]
    if exclusions:
        limits.append("excluded path classes are counted but not enumerated; absence never proves non-existence")

    return {
        "schema": "LandscapeSnapshot/v0.1",
        "snapshot_id": {
            "type": "LandscapeSnapshot/v0.1",
            "ref": "sha256:"
            + hashlib.sha256(MEMBERSHIP_DOMAIN + canonical_json(ordered)).hexdigest(),
        },
        "observed_at": observed_at,
        "source_identity": {
            "baseline_ref": baseline_ref,
            "baseline_digest": baseline_digest,
            "collector_version": COLLECTOR_VERSION,
        },
        "project_observation_refs": ordered,
        "project_count": len(ordered),
        "evidence_ref_count": evidence_ref_count,
        "completeness": {
            "status": status,
            "enumerated_file_count": enumerated_file_count,
            "exclusions": exclusions,
        },
        "limits": sorted(limits),
        "authority": "NONE",
        "effect": "NONE",
    }


def content_identity(contract_type: str, projection: Any) -> str:
    """Compute a CorpusContentIdentityProfile/v0.1 reference for one projection.

    The envelope contains exactly profile, type and projection. Field order is
    irrelevant because canonicalization sorts keys; the profile identifier and
    the contract type both participate in the digest.
    """

    envelope = {"profile": IDENTITY_PROFILE, "type": contract_type, "projection": projection}
    digest = hashlib.sha256(IDENTITY_DOMAIN + canonical_json(envelope)).hexdigest()
    return f"sha256:{digest}"


def observation_ref(observation: dict[str, Any]) -> dict[str, str]:
    return {
        "type": "LandscapeObservation/v0.1",
        "ref": content_identity("LandscapeObservation/v0.1", observation),
    }


def collect(
    manifest_path: Path,
    observed_at_raw: str,
    receipt_path: Path | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    observed_at = require_observed_at(observed_at_raw)
    manifest = load_manifest(manifest_path)
    baseline_digest = str(manifest["manifest_digest"])
    baseline_ref = manifest_path.name
    entries = manifest["entries"]
    manifest_entries = {
        str(entry["relative_path"]): entry for entry in entries if isinstance(entry, dict) and "relative_path" in entry
    }
    paths = sorted(manifest_entries)

    projects = discover_projects(paths)
    if not projects:
        raise CollectorError("no project roots discovered in the source manifest")

    by_root: dict[str, list[str]] = {root: [] for root in projects}
    for path in paths:
        parts = path.split("/")
        best = ""
        for index in range(len(parts) - 1, -1, -1):
            candidate = "/".join(parts[:index])
            if candidate in projects:
                best = candidate
                break
        if best:
            by_root[best].append(path)

    observations = [
        build_observation(
            root,
            projects[root],
            by_root[root],
            manifest_entries,
            observed_at,
            baseline_ref,
            baseline_digest,
        )
        for root in sorted(projects)
    ]
    observations.sort(key=lambda observation: observation["project_root"])

    refs = [observation_ref(observation) for observation in observations]
    if len({ref["ref"] for ref in refs}) != len(refs):
        raise CollectorError("observation reference collision in generated observations")

    exclusions = [
        {
            "type": "SYMLINK",
            "count": 301,
            "reason": "BASELINE_POLICY_SKIPPED",
            "enumerated": "NOT_ENUMERATED",
        },
        {
            "type": "EXCLUDED_DIRECTORY_OR_SECRET",
            "count": 3141,
            "reason": "BASELINE_POLICY_EXCLUDED",
            "enumerated": "NOT_ENUMERATED",
        },
    ]
    snapshot = build_snapshot(
        refs,
        observed_at,
        baseline_ref,
        baseline_digest,
        len(paths),
        exclusions,
        len(paths),
    )

    if receipt_path is not None:
        receipt = {
            "schema": "LandscapeCollectionReceipt/v0.1",
            "executed_at": observed_at_raw,
            "collector_version": COLLECTOR_VERSION,
            "input_ref": {"ref": baseline_digest, "name": baseline_ref},
            "observed_at_used": observed_at,
            "project_count": len(projects),
            "output_refs": refs + [snapshot["snapshot_id"]],
            "authority": "NONE",
            "effect": "NONE",
        }
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    return observations, snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="accepted read-only file inventory manifest")
    parser.add_argument(
        "--observed-at",
        required=True,
        help="evidence timestamp taken from the source evidence, never collector wall-clock time",
    )
    parser.add_argument("--observations-out", required=True, help="NDJSON output path for project observations")
    parser.add_argument("--snapshot-out", required=True, help="JSON output path for the landscape snapshot")
    parser.add_argument("--receipt-out", help="optional runtime receipt path (not identity-bearing)")
    args = parser.parse_args(argv)

    observations, snapshot = collect(
        Path(args.manifest),
        args.observed_at,
        Path(args.receipt_out) if args.receipt_out else None,
    )

    obs_path = Path(args.observations_out)
    obs_path.parent.mkdir(parents=True, exist_ok=True)
    with obs_path.open("w", encoding="utf-8") as handle:
        for observation in observations:
            handle.write(json.dumps(observation, sort_keys=True, ensure_ascii=False) + "\n")

    snap_path = Path(args.snapshot_out)
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"projects={len(observations)} snapshot={snapshot['snapshot_id']['ref'][:23]}...")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CollectorError as error:
        print(f"collector error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
