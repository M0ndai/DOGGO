# D.O.G.G.O.

> A bounded, evidence-driven observer with zero authority and zero effect capability.

D.O.G.G.O. is a passive watchdog / observer.

```text
AUTHORITY = NONE
EFFECT_CAPABILITY = NONE

OBSERVE → DETECT → COMPARE → REPORT → NO ACTION
```

D.O.G.G.O. may detect, compare, characterize, and report bounded evidence.
D.O.G.G.O. does not mutate, execute on, or otherwise act on the observed system.

## Genesis boundary

The foundational contract is
[contracts/doggo-genesis-v0.1.json](contracts/doggo-genesis-v0.1.json).
Its closed v0.1 surface and tests remain intact; new fields require an explicit,
versioned revision. Report carrier v0.2 is a separate instance contract and does
not grant authority or effect capability to the Genesis contract.

Observation is directly supported by supplied evidence; inference stays separately
labelled and derived. Missing evidence remains visible, and scope must not be
widened implicitly. D.O.G.G.O. must not mutate canonical state, execute work,
authorize work, or promote a result.


The public repository starts from a deliberately strict genesis specification:

- explicit observation scope is required
- evidence, inference, and limits stay visibly separated
- external effects are forbidden
- canonical-state writes are forbidden
- recommendations never imply authorization or execution

See `GENESIS.md` for the core contract and `NON_GOALS.md` for the negative
specification.

For the detailed repository contract, see:

- `spec/` for the focused identity, authority, scope, epistemics, report, and invariant notes
- `schemas/` for the machine-readable observation scope and observation report contracts

The report carrier is v0.2: inferred claims require both evidence references and
a visible derivation. See `spec/report.md` for the explicit compatibility change
and the limits of schema validation. Scope timing also requires the pure
companion check documented in `spec/observation-scope.md`.

The repository supplies declarative contracts, schemas and pure validation
checks. It supplies no executor, authorization path, persistence mechanism or
canonical-state owner.

## Verify

The seven foundational Genesis tests use only the standard library.
The full suite additionally tests the report schema and scope timing.
Tests use Python's `unittest` and the test-only JSON Schema engine declared in
`requirements-test.txt`. The timing validator itself uses only the standard
library. With the test dependency available, run from the repository root:

```sh
python3 -B -m unittest discover -s tests -p 'test_*.py'
```

Missing test dependencies fail explicitly; tests are not silently skipped.
These checks validate carriers and timing rules. They do not execute an observer
or prove runtime authority/effect isolation.
