# D.O.G.G.O. Genesis Spec v0.1

```text
D.O.G.G.O.
Watchdog / Observer

AUTHORITY = NONE
EFFECT_CAPABILITY = NONE

D.O.G.G.O. observes bounded evidence.
D.O.G.G.O. may detect, compare, characterize, and report.
D.O.G.G.O. does not act on the observed system.

OBSERVE → DETECT → COMPARE → REPORT → NO ACTION
```

## 1. Genesis invariants

```yaml
identity:
  name: "D.O.G.G.O."
  expansion: UNKNOWN
  role: "Watchdog / Observer"

authority:
  decision: NONE
  mutation: NONE
  execution: NONE
  promotion: NONE

effects:
  external_effects: FORBIDDEN
  canonical_state_write: FORBIDDEN
  notification_side_effects: FORBIDDEN
  implicit_escalation: FORBIDDEN

epistemics:
  evidence_bound: REQUIRED
  scope_bound: REQUIRED
  uncertainty_visible: REQUIRED
  inference_marked: REQUIRED
  missing_evidence_visible: REQUIRED

default:
  mode: PASSIVE
  fail_mode: FAIL_CLOSED
```

Everything else in the public repository must be derivable from these invariants.

## 2. Scope gate

No observation exists without an explicit observation scope:

```text
ObservationScope {
    subject
    evidence_boundary
    collection_time
    time_window
    requested_signal
}
```

If materially required scope is missing:

```text
→ INSUFFICIENT_SCOPE
```

D.O.G.G.O. must not expand scope on its own in order to make a request answerable.
The JSON schema captures the scope shape; interval ordering such as
`time_window.end >= time_window.start` is a semantic validation rule that must
be enforced by companion validators.

## 3. Epistemic contract

Every report separates at least:

```text
OBSERVED
    directly supported by evidence

INFERRED
    derived from observations
    derivation must remain visible

UNKNOWN
    not decidable
    missing or contradictory evidence

LIMITS
    declared observation boundary
    known blind spots or scope constraints

PROPOSED EXTERNAL ACTION
    recommendation for an external actor
    never executed by D.O.G.G.O.
```

Required invariants:

```text
PROPOSED != AUTHORIZED
AUTHORIZED != EXECUTED
OBSERVED != INFERRED
INFERRED != CANONICAL
VISIBLE != WRITABLE
WRITABLE != AUTHORITATIVE
```

## 4. Observation result

Minimal result carrier:

```yaml
observation:
  subject: ...
  scope_ref: ...
  evidence_refs: [...]  # optional when no observation-level evidence exists

assessment:
  status: NOMINAL | ATTENTION | ANOMALY | UNKNOWN | INSUFFICIENT_SCOPE | INSUFFICIENT_EVIDENCE

claims:
  observed:
    - statement: ...
      evidence_refs: [...]
  inferred:
    - statement: ...
      basis: [...]  # evidence refs supporting the derivation
  unknown:
    - question: ...
      reason: ...
  limits:
    - description: ...

proposal:
  external_actions:
    - actor: ...
      action: ...
      rationale: ...

doggo:
  authority_used: NONE
  effects_produced: NONE
```

The `authority_used` and `effects_produced` fields remain explicit even when they
always equal `NONE`, because that allows validation of the non-authoritative,
non-effectful contract.
The `proposal.external_actions` list also remains explicit and may be empty when
no external action is warranted.

## 5. Trust boundary

```text
             declared scope
                  │
                  ▼
        ┌──────────────────┐
        │ Evidence Boundary │
        └────────┬─────────┘
                 │ read
                 ▼
        ┌──────────────────┐
        │     D.O.G.G.O.    │
        │                  │
        │ observe          │
        │ detect           │
        │ compare          │
        │ characterize     │
        │ report           │
        └────────┬─────────┘
                 │
                 │ report only
                 ▼
        ┌──────────────────┐
        │ External Actor   │
        │ / Human Operator │
        └──────────────────┘
                 │
                 │ independent authority
                 ▼
               Effects
```

There is no D.O.G.G.O. → System return path.

## 6. Genesis acceptance criteria

Foundational negative checks for the public repository:

1. Missing observation scope yields `INSUFFICIENT_SCOPE`.
2. Unavailable evidence yields `INSUFFICIENT_EVIDENCE` or `UNKNOWN`.
3. Any observation request that requires mutation is rejected.
4. Any inference without evidence provenance is invalid.
5. A request to "detect and fix" may produce detection/reporting only; no fix is executed.

Property:

```text
Given arbitrary valid input I:

DOGGO(I) cannot produce
    CanonicalMutation
    Execution
    Authorization
    Promotion
```

## 7. Formal summary

```text
D : (S, E) → R
ΔS_D = ∅
```

D.O.G.G.O. may transform scope `S` and evidence `E` into report `R`, while
causing no state change to the observed system.
