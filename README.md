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

## Genesis

The public repository starts from a deliberately strict genesis specification:

- explicit observation scope is required
- evidence, inference, and limits stay visibly separated
- external effects are forbidden
- canonical-state writes are forbidden
- recommendations never imply authorization or execution

See `GENESIS.md` for the core contract and `NON_GOALS.md` for the negative
specification.
