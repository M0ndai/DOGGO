# Architecture

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

There is no system-write path from D.O.G.G.O. back into the observed system.
