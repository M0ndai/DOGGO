# Report

Minimum report carrier:

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
      basis: [...]  # observed-claim refs and/or evidence refs supporting the derivation
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
Likewise, `doggo.authority_used` and `doggo.effects_produced` remain explicit
fixed-value fields so validators can prove the report stayed non-authoritative
and non-effectful.
