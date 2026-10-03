# DOGGO successor reconciliation — decision record

Status: `CANDIDATE / NON-AUTHORITATIVE / PUBLISHED-BRANCH`

Branch: `reconcile/doggo-successor-0`
Base: `M0ndai/DOGGO` `main` @ `754b11a2f75830a890113077a6d0daaac0201aa4`
Successor source: local `DOGGO` @ `9c4278ece5767d049e7ba37a0536da5ca3ce67eb`
  (preservation commit over `b93703fc7127b83eaf53c817100f6039da7a10ad`)

```text
CONTENT_SUCCESSOR != SHARED_GIT_HISTORY
```

The two trees share **zero Git objects**. Every commit below is a content
relation, established by inspection. No history was grafted, merged, or
rewritten to manufacture ancestry.

## Authority assignment

| State | Role |
|---|---|
| remote `main` genesis contract | **IDENTITY GENESIS AUTHORITY** |
| local `b93703f` / `9c4278e` | **SUCCESSOR IMPLEMENTATION CANDIDATE** |
| this branch | **RECONCILED SUCCESSOR CANDIDATE** — not `main`, not canonical |

Neither tree was declared wholly canonical. Genesis keeps the machine-readable
identity core; the successor contributes implementation. Neither replaces the
other.

## Semantic identity evidence

Ranked by evidence strength, strongest first.

1. **Explicit contract.** `contracts/doggo-genesis-v0.1.json` fixes
   `identity.name = "D.O.G.G.O."`, `identity.role = "WATCHDOG_OBSERVER"`,
   `authority = "NONE"`, `effect_capability = "NONE"`.
   The successor expresses the same boundary machine-readably:
   three observation schemas carry
   `properties.authority.const = "NONE"` and `properties.effect.const = "NONE"`,
   and the identity-binding schema's own description disclaims
   "authority, effect, eligibility, admission, canonicality, freshness".

2. **Architecture continuity.** Both trees define one observation-only role with
   no effect path. The successor's collector is read-only over observed trees and
   takes every output path as an explicit CLI argument.

3. **Prose agreement.** `DOGGO_PERSONA.md` and `README.md` state
   "Watchdog / Observer", "observation-only", `authority` is `NONE`.

Directory name agreement was *not* used as evidence. It is the weakest signal
available and, on its own, would not support a successor claim.

## Genesis invariants vs successor

| Genesis invariant | Successor status |
|---|---|
| `identity.name == D.O.G.G.O.` | PRESERVED |
| `identity.role == WATCHDOG_OBSERVER` | PRESERVED |
| `authority == NONE` | PRESERVED (prose + 3 schemas) |
| `effect_capability == NONE` | PRESERVED (3 schemas) |
| `lifecycle` ends `NO_ACTION` | NOT_REPRESENTED machine-readably |
| `evidence.observation.evidence_required` | NOT_REPRESENTED |
| `evidence.inference.label_required` | NOT_REPRESENTED |
| `evidence.missing_evidence.report_visibility` | REFINED_COMPATIBLY in prose |
| `scope.explicit_scope_required` | NOT_REPRESENTED |
| `scope.implicit_expansion == FORBIDDEN` | REFINED_COMPATIBLY in prose |
| `prohibited_actions` (4 entries) | NOT_REPRESENTED as a machine list |

**No contradiction was found.** The successor is strictly weaker in coverage and
equal in posture: everything Genesis states as machine-readable, the successor
either repeats machine-readably or states in prose. Nothing in the successor
grants authority, effect, eligibility, or canonicality.

The `NOT_REPRESENTED` rows are recorded as open, not silently closed. They are
genesis constraints the successor does not yet express; `tests/test_successor_genesis_binding.py`
asserts the ones that are expressed, so an escalation becomes visible, but a
constraint that was never expressed cannot be enforced by that test.

## Content delta matrix

| Artifact | Genesis | Successor | Relation | Action |
|---|---|---|---|---|
| `contracts/doggo-genesis-v0.1.json` | yes | no | GENESIS_ONLY | **retained unchanged** |
| `tests/test_genesis_contract.py` | yes | no | GENESIS_ONLY | **retained unchanged** |
| `README.md` | stub | full | OBSOLETE_GENESIS_ARTIFACT | superseded by successor |
| `contracts/doggo-security-observation.v0.1.schema.json` | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `contracts/doggo-security-observation-identity-binding.v0.1.schema.json` | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `contracts/landscape/*.json` (4 schemas) | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `contracts/landscape/README.md` | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `DOGGO_PERSONA.md`, `DOGGO_LORE_v0.md` | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `collector/landscape_collect.py` | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `fixtures/**` | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `AGENTS.md`, `docs/agents/**` | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `assets/README.md`, `requirements-dev.txt`, `.gitignore` | no | yes | LOCAL_ONLY_EXTENSION | ported |
| `contracts/SUCCESSOR.md` | — | — | reconciliation artifact | successor `contracts/README.md`, renamed to avoid colliding with the genesis dir listing |

### Genesis retention

The genesis contract and its seven tests were **retained, not replaced**. The
remote `README.md` stub was the only artifact treated as obsolete, because the
successor README states the same identity with strictly more detail. No genesis
evidence was deleted or weakened to make the port fit.

`contracts/SUCCESSOR.md` keeps the successor's own contract documentation under a
distinct name, so the genesis contract remains the single machine-readable
identity authority rather than competing with a second README in `contracts/`.

## Rejected local artifacts

None rejected. Every successor artifact was either ported or, in the README
case, superseded by a strictly more specific version of the same statement.

Local state excluded from the port: `.broodhood-data/`, `var/` (none present),
and `tests/__pycache__/`.

## Adversarial verification

Eleven genesis mutations and six successor escalations were each detected:

| Probe | Detected |
|---|---|
| `identity.name = PUPPY` | yes |
| `identity.role = EXECUTOR` | yes |
| `authority = WRITE` | yes |
| `effect_capability = WRITE` | yes |
| `lifecycle` ends `EXECUTE` | yes |
| `inference.label_required = false` | yes |
| `scope.implicit_expansion = ALLOWED` | yes |
| drop `EXECUTION` prohibition | yes |
| malformed `identity` | yes |
| capability injection (`allowed_actions`) | yes |
| genesis contract deleted | yes |
| successor schema `authority = WRITE` | yes |
| successor schema `effect = WRITE` | yes |
| successor adds `EXECUTION` | yes |
| binding schema claims authority in prose | yes |
| successor impersonates genesis schema id | yes |
| README claims write authority | yes |

## Test counts

| Suite | Collected | Result |
|---|---|---|
| remote genesis baseline (`754b11a`) | 7 | OK |
| local successor baseline (`9c4278e`) | 62 + 25 subtests | passed |
| reconciled candidate | 77 | OK |

## Unresolved

1. Six genesis invariants are `NOT_REPRESENTED` in the successor's
   machine-readable contracts. Expressing them is successor work, not
   reconciliation work, and is not decided here.
2. The remote repository has no `.gitignore`, so `tests/__pycache__/` appears as
   untracked after any test run. Out of scope here; recorded so it is not
   mistaken for reconciliation residue.
3. `M0ndai/DOGGO` carries four additional remote branches (`plugin/doggo-observer-v0.1`,
   `copilot/d-o-g-g-o-genesis-spec-v0-1`, `add-openhands-issue-to-pr-workflow`,
   plus `pr/*` refs). None was inspected or modified. Whether
   `plugin/doggo-observer-v0.1` is a third line of work is unresolved.
4. Merge to `main` is not authorized and not performed.