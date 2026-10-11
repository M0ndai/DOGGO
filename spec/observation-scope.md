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
ordering rule is checked by the pure function
`validators.observation_scope.validate_scope_time(scope)` outside JSON Schema.
Consumers must validate the schema and then call this function, rejecting any
nonempty error list before observation. It validates timing only and cannot
replace the structural schema or a caller's independent scope authorization.
`collection_time` records when the evidence snapshot was collected, while
`time_window` describes the interval under analysis.

The timing checker requires calendar-valid RFC 3339 timestamps with known
offsets. Lowercase `t`/`z` and fractions up to six decimal places are supported.
Unknown `-00:00` offsets, leap seconds and finer precision are unsupported and
rejected; they are never silently normalized or truncated. Interval comparison
uses absolute instants, accepts equal endpoints, and does not require
`collection_time` to lie inside the analysis interval.

The function only reads the supplied object and returns errors. It performs no
collection, reference resolution, scope expansion, authorization or dispatch.
Selecting an `INSUFFICIENT_SCOPE` response belongs to the consumer; the function
does not manufacture a report or replace missing identities with placeholders.
