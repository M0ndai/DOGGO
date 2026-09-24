---
name: bounded-observation
description: Use when the user asks DOGGO to observe a specifically bounded system, artifact, or state and report evidence-bound conditions without changing anything.
---

# DOGGO bounded observation

Apply the bundled `references/doggo-genesis-v0.1.json` as the source contract. This Skill provides a reporting procedure, not an automated watchdog, authorization system, or execution capability.

1. Establish an explicit target, time or version boundary where relevant, supplied evidence, and comparison criteria. If any are missing, report the gap and limit the analysis to what is actually decidable. Do not silently widen scope.
2. **OBSERVE:** Record only statements directly supported by evidence. For each observation, identify the exact supplied source or observed tool result. Treat source claims as claims when their truth has not been independently checked.
3. **DETECT:** Identify conditions within the stated scope and criteria. A detected condition must link to observations; label uncertain conditions `UNKNOWN`.
4. **COMPARE:** Compare only with explicit baselines or criteria. Never invent a baseline. Mark any derived conclusion `INFERENCE` and show the supporting observations and assumptions.
5. **REPORT:** Give the scope, evidence and provenance, observations, labelled inferences, comparison outcomes, missing evidence, and limitations. Distinguish `OBSERVED`, `INFERRED`, and `UNKNOWN` in the result.
6. **NO_ACTION:** Stop after the report. Do not mutate canonical state, execute remediation or other work, authorize work, or promote a result. A recommendation, if requested, is a labelled proposal without effect or authority.

If a host can read files or query a source, use read-only capabilities only within the supplied scope and report what was actually read. The Skill does not grant access to files, services, or tools. Never claim an observation from an unavailable source. The Genesis contract is closed; changing its fields or capabilities requires a separately versioned contract revision.
