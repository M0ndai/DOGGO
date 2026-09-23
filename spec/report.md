# Report

Minimum report carrier:

```yaml
observation:
  subject: ...
  scope_ref: ...
  evidence_refs: [...]

assessment:
  status: NOMINAL | ATTENTION | ANOMALY | UNKNOWN | INSUFFICIENT_EVIDENCE

claims:
  observed:
    - statement: ...
      evidence_refs: [...]
  inferred:
    - statement: ...
      basis: [...]
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

`proposal.external_actions` may be empty when no recommendation is warranted;
the proposal section remains explicit to preserve a fixed report shape.
