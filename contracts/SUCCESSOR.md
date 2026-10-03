# DOGGO security observation contract

`doggo-security-observation.v0.1.schema.json` is the machine-readable
`DOGGOSecurityObservation/v0.1` contract.  It is a JSON Schema Draft 2020-12
document and remains subordinate to the observation-only boundary in
`DOGGO_PERSONA.md`.

## Boundary

The contract records a subject, evidence boundary, time window, requested
signal, observations, inferences, and limits.  It keeps two closed and
independent status axes:

- `observation_status`: `NOMINAL`, `ATTENTION`, `ANOMALY`, `UNKNOWN`,
  `INSUFFICIENT_EVIDENCE`, or `INSUFFICIENT_SCOPE`;
- `handoff_status`: `NONE`, `PROPOSED`, or `BLOCKED_AUTHORITY`.

Every observation fixes `authority` and `effect` to `NONE`.  A proposed
external action is data for an external owner.  It is not an AuthorityRequest,
incident decision, mandate, remediation instruction, notification request, or
effect command, and it is never forwarded automatically by this contract.

Scope components are always present.  A missing input is represented
explicitly with `status: MISSING`; it is not silently omitted, guessed, or
replaced with `null`.  An `INSUFFICIENT_SCOPE` result requires at least one
such marker.  Other observation statuses require all four scope components to
be supplied.

## Content reference

`$defs.DOGGOSecurityObservationRef` defines the typed reference shape:

```json
{
  "type": "DOGGOSecurityObservation/v0.1",
  "ref": "sha256:<64 lowercase hexadecimal characters>"
}
```

The reference hashes the observation payload, never the reference wrapper.
The fixture test currently projects the JSON payload as UTF-8 with sorted
object keys and no insignificant whitespace, rejects non-finite numbers, and
preserves array order, field absence, and explicit `null`.  This is a local
v0.1 compatibility rule.  The existing `fixtures/valid/*.ref.json` files are
therefore **legacy DOGGO-local references**.  Their two-field shape does not
prove conformance to any later identity profile, and their values are not
migrated or reinterpreted by this contract.

## Corpus identity binding

`doggo-security-observation-identity-binding.v0.1.schema.json` defines a
separate `DOGGOSecurityObservationIdentityBinding/v0.1`.  It binds a new
content reference to all three of the following facts:

- `identity_profile` is exactly `CorpusContentIdentityProfile/v0.1`;
- `identity_projection` is exactly
  `FULL_DOGGO_SECURITY_OBSERVATION_V0_1`;
- `content_ref.type` is exactly `DOGGOSecurityObservation/v0.1`.

The DOGGO-owned projection is the complete, already validated
`DOGGOSecurityObservation/v0.1` document.  `schema`, `authority: NONE`,
`effect: NONE`, scope, observations, inferences, limits, statuses, and any
valid optional handoff proposal all remain present exactly as supplied.  The
projection adds no defaults and removes no fields.  Absent remains distinct
from `null`; object key order is canonicalized, while array order remains
identity-bearing.

The exact Corpus profile envelope is:

```json
{
  "profile": "CorpusContentIdentityProfile/v0.1",
  "type": "DOGGOSecurityObservation/v0.1",
  "projection": "<complete validated DOGGOSecurityObservation/v0.1>"
}
```

Its preimage is the UTF-8 bytes of
`CorpusContentIdentityProfile/v0.1`, one `0x00` byte, and the compact,
key-sorted UTF-8 JSON bytes of that closed envelope.  The admitted value
domain contains JSON null, booleans, Unicode scalar strings, signed-64-bit
integers, arrays, and string-keyed objects.  Floats, non-finite values, sets,
implicit defaults, and silent Unicode normalization are not admitted.

All identity-bearing DOGGO timestamp fields must already use the exact form
`YYYY-MM-DDTHH:MM:SS.ffffffZ`.  They are not converted from offsets or from a
different fractional precision during projection.  Where the original v0.1
fixtures contain timestamps, those values use second precision.  The fixtures
remain valid observation fixtures and legacy-reference evidence, but the two
time-bearing documents do not satisfy this stricter identity-projection
precondition.  The profile-conformant golden vector under
`fixtures/identity/` is a separate, schema-valid observation with six-digit
UTC timestamps; no legacy fixture is overwritten.

The binding is identity metadata only:

```text
Corpus-conformant identity
!= canonical status
!= admission
!= authority
!= effect
!= successful observation

identity binding
!= migration
!= legacy equivalence
```

It defines no runtime dependency on a Corpus checkout and no registry,
forwarding, authority request, mandate, verification receipt, admission,
handoff, or effect operation.

## Fixtures and verification

`fixtures/valid/` contains conforming observations and their typed content
references.  `fixtures/invalid/` contains near-valid payloads showing that the
contract rejects an AuthorityRequest, incident decision, mandate, remediation
instruction, and effect command.

Run:

```sh
python3 -m unittest -v
find contracts fixtures -type f -name '*.json' -exec python3 -m json.tool {} /dev/null \;
git diff --check
```

The focused tests require the development dependency recorded in
`requirements-dev.txt`.  They validate both schemas, all positive and
negative fixtures, legacy typed refs, the Corpus-conformant golden vector,
closed binding behavior, and deterministic identities.  No runtime, network,
notification, JV, ABH, ticket, migration, or remediation path is exercised.
