# Threat Model

Primary risks addressed by genesis:

- authority leakage through ambiguous recommendations
- discovery-based scope expansion
- hidden writes or side effects
- epistemic collapse between observation and inference
- silent handling of missing evidence

Primary mitigations:

- explicit observation scope
- fail-closed behavior on insufficient scope
- evidence-bounded reporting
- explicit separation of observed, inferred, and unknown claims
- explicit `authority_used: NONE`
- explicit `effects_produced: NONE`
