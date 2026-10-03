# Landscape observation contract

`LandscapeObservation/v0.1` and `LandscapeSnapshot/v0.1` observe a bounded,
read-only local source landscape. They carry no authority and permit no effect.

## Boundary

```text
accepted file inventory (metadata, read-only)
  -> LandscapeCollector (deterministic, hash-free)
  -> LandscapeObservation/v0.1   one per project root
  -> LandscapeSnapshot/v0.1      one membership projection
```

Every record fixes `authority` and `effect` to `NONE`. Nothing here dispatches
work, mutates a source tree, grants approval, or establishes landscape truth.

## One-way membership

`LandscapeObservation/v0.1` contains **no** snapshot reference. The snapshot
references observation content hashes; observations never reference a snapshot.

```text
observation A ──┐
observation B ──┼──> LandscapeSnapshot/v0.1 ──> snapshot membership root
observation C ──┘
```

Both content hashes are computable because neither record depends on the other.
A project was observed; a snapshot then states that those observations together
describe one landscape state. If a reverse reference is ever needed, it belongs
in a separate `ObservationSnapshotMembership/v0.1` record, never inside
identity-bearing observation content.

`snapshot_id` is the membership root over the reference list, deliberately not
the snapshot's own content identity, which is minted by the identity binding
after the document is complete.

## Three semantic levels

```text
observation  "pyproject.toml exists at X"          evidence statement
claim        "enumerated_files = 37"                deterministic derivation
inference    "likely a Python service"              interpretation
```

A claim is reconstructable by an algorithm from the observations and the source
manifest. An inference is not, and never carries authority. In V0 `inferences`
is expected to be empty: no semantic judgment is admitted yet.

```text
observation + algorithm ──> claim
claim ──X────────────────> authority
```

## Identity

Content identity is `CorpusContentIdentityProfile/v0.1` and is owned by
Corpus-alpha. This contract does not define a second identity mechanism.

```text
preimage = UTF8("CorpusContentIdentityProfile/v0.1") + 0x00 + canonical_envelope
envelope = {"profile": ..., "type": ..., "projection": ...}
canonical = JSON, keys sorted, no whitespace, UTF-8
```

Hashing the bare payload instead of the envelope would mint a different
identity under the same type name. `typed_content_ref()` in
`corpus_snapshot_core.content_identity` is the reference implementation.

`project_id` is a separate derivation over the baseline-relative project root
under its own domain separator. It is a path identity, not a name: `BloodMoon`,
`bloodmoon` and `BloodMoon-old` stay distinct because no shared identity has
been proven.

The source manifest reference is deliberately **not** a Corpus typed content
ref. An external file inventory is evidence, not Corpus-admitted content, and
its own schema string is not held to the Corpus contract-type grammar.

## Timestamps

The content identity profile does **not** police timestamps; its canonical
timestamp helper is optional and unenforced. A second-precision timestamp is
admitted by the profile and still hashed successfully. These contracts
therefore anchor the constraint in the schema itself:

```text
^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$
```

Second precision and UTC offsets are refused here rather than by convention.

`observed_at` is taken from the source evidence, never from collector wall-clock
time. It is a required collector input. A supplied millisecond value is
zero-padded to microseconds, which is lossless and deterministic; a value with
no fractional part is rejected rather than guessed. Runtime execution time is
recorded only in a separate non-identity-bearing receipt, so that two runs over
the same manifest with the same `observed_at` and collector version produce
byte-identical output.

## Freshness

V0 makes no probabilistic freshness claim.

```json
"freshness": {"status": "FRESH_AT_OBSERVATION", "observed_at": "...", "decay_model": "NONE"}
```

An observation states when the underlying state was observed. It does not state
that the state is still fresh with any probability. A later revision may add
`age = now - observed_at` and a decay term, where the time constants are
versioned policy and never a model output.

## Completeness

`completeness.exclusions[]` records path classes that were deliberately not
observed, with `enumerated: NOT_ENUMERATED` when only the count is recoverable.
Absence from the snapshot therefore never proves non-existence; it proves only
that the path was not observed. The current baseline reports 301 skipped
symlinks and 3.141 excluded entries whose individual paths are not enumerated.

## Project discovery

A project root is the parent directory of a **root marker**:

```text
plugin.json  package.json  pyproject.toml  setup.py  Cargo.toml  go.mod
```

`SKILL.md` and `manifest.json` are **supporting markers**: recorded as project
capabilities, never allowed to create a project root. Otherwise every skill
directory would become a project. When roots nest, the deepest root owns its
files and an enclosing root records the nested root as a member rather than
merging with it.

## Not in V0

Content hashes per file, semantic judgments, decay, freshness probability,
`overlaps_with` and `supersedes` relations, and any write path.

## Verify

```sh
python3 -m unittest discover -s tests -v
find contracts fixtures -name '*.json' -exec python3 -m json.tool {} /dev/null \;
```
