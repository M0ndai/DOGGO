# Observation Scope

Every observation request must declare:

```text
ObservationScope {
    subject
    evidence_boundary
    collection_time
    time_window
    requested_signal
}
```

If materially required scope is missing, the result is `INSUFFICIENT_SCOPE`.
The observer must not widen its own scope.
The declared `time_window` is only valid when its end is not earlier than its
start. The repository JSON schema captures the structural shape only; this
ordering rule is enforced by companion validation outside JSON Schema.
`collection_time` records when the evidence snapshot was collected, while
`time_window` describes the interval under analysis.
