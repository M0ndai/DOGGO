# D.O.G.G.O.

![D.O.G.G.O. Watchdog / Observer visual reference](assets/doggo-watchdog-observer.png)

D.O.G.G.O. is defined here as an **observation-only watchdog persona**.
It has no operational authority and no effect capability.

Start with [DOGGO_PERSONA.md](DOGGO_PERSONA.md).  The local
[AGENTS.md](AGENTS.md) makes the same boundary binding for work performed in
this directory.

This is a persona contract only.  It does not install, start, configure, or
claim the existence of a watchdog runtime.

The versioned machine-readable observation contract lives at
[`contracts/doggo-security-observation.v0.1.schema.json`](contracts/doggo-security-observation.v0.1.schema.json).
It defines evidence-bound observations and external handoff proposals only;
it does not define an authority request, incident decision, mandate,
remediation, or effect command.  See [`contracts/README.md`](contracts/README.md)
for the contract boundary, fixture layout, and verification commands.

The image is a non-normative visual reference.  Text and depicted capabilities
inside it do not grant tools, runtime state, authority, or effects.  See the
[asset record](assets/README.md) for provenance and integrity information.
