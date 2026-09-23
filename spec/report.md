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

proposal:
  external_actions:
    - actor: ...
      action: ...
      rationale: ...

doggo:
  authority_used: NONE
  effects_produced: NONE
```
