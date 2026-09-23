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
  observed: [...]
  inferred: [...]
  unknown: [...]

proposal:
  external_actions: []

doggo:
  authority_used: NONE
  effects_produced: NONE
```
