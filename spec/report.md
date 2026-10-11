# Report

Minimum report carrier, v0.2:

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
      derivation: ...  # visible explanation of the inference
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
fixed-value fields. Validation proves only that the carrier declares `NONE`;
it does not prove the producer's actual authority or effects. Runtime boundaries
need independent verification.

The v0.2 schema has the versioned identifier
`https://doggo.dev/schemas/v0.2/observation-report.schema.json`; the repository
file remains `schemas/observation-report.schema.json`. No network retrieval is
required for local validation, and this identifier does not attest domain ownership.
Each inference requires evidence references in `basis` and a nonblank
`derivation` explaining the conclusion. This is an explicit carrier revision:
v0.1 inferences with references alone are rejected. Producers must supply an
actual derivation, not generate placeholder explanations to pass validation.
Reports without inferred claims keep the same instance shape.

Schema validation does not resolve scope/evidence references, bind subjects,
prove evidence truth or inference soundness, or enforce status selection.
Consumers must check those semantics separately; no such checks are supplied
by this schema. `NOMINAL` must not be interpreted as evidence-backed merely
because the carrier validates.
