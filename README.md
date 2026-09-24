# D.O.G.G.O.

**D.O.G.G.O.** is a watchdog and observer. Its Genesis contract is deliberately
non-authoritative: it observes an explicitly supplied scope, detects and
compares evidence-bound conditions, then reports its result and takes no
action.

## Genesis boundary

The first contract is [contracts/doggo-genesis-v0.1.json](contracts/doggo-genesis-v0.1.json).
It defines the following non-negotiable boundary:

```text
OBSERVE -> DETECT -> COMPARE -> REPORT -> NO_ACTION
```

- `AUTHORITY = NONE`
- `EFFECT_CAPABILITY = NONE`
- Observation is a directly evidenced statement; inference is a separately
  labelled derived statement and must never be presented as observation.
- Missing evidence remains visible in the report. It is not silently filled in.
- Scope is explicit and may not be widened implicitly.
- The v0.1 contract surface is closed: a new field requires an explicit,
  versioned contract revision rather than silently adding a capability.
- D.O.G.G.O. must not mutate canonical state, execute work, authorize work, or
  promote a result.

This repository currently supplies only the declarative Genesis contract and
its tests. It supplies no executor, authorization path, persistence mechanism,
or canonical-state owner.

## ChatGPT/Codex Plugin

The root `plugin.json` and `skills/bounded-observation/SKILL.md` package the
Genesis observation procedure as a Skills-only Plugin. The Skill requires a
user-supplied scope and evidence and stops after an evidence-bound report.
It adds no watchdog daemon, integrations, execution, or authority. A portable
package includes `plugin.json`, `skills/`, and the Genesis contract; it excludes
`.git/`, tests, and local caches.

## Verify

The contract test relies only on Python's standard library:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```
