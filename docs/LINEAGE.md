# Lineage

ZTGKT changed identity more than once. The archive preserves at least four
expansions of the acronym, and they are not consistent with each other:

| Expansion | Where it appears |
|---|---|
| **Zero-Trust Guardrails & Kinetic Throttle** | UGPIS-Ω single-file headers, component inventories. The dominant form, and the one this repository uses. |
| Zero Trust Governance Knowledge Tunnel | chat-classification prompts, system registries |
| Zero-Trust Gatekeeper Tool | post-mortem analyses |
| (unexpanded) "linguistic pipeline" / "validation pipeline" | most inventory listings |

The drift itself is informative. The name was stable on its initials and
unstable on its meaning, which tracks a component whose *position* in the
stack was fixed long before its *responsibility* was settled.

## Phase 1: the gate

ZTGKT enters the archive as the first stage of the UGPIS-Ω pipeline: a
mandatory validation layer standing in front of all generation. The
implementation is `ContentValidationPipeline`, wired as
`self._ztgkt_pipeline` in `UGPISOmegaController`, reached through a private
`_guarded_generator` so that no other component can call the model directly.

That wiring is the whole design thesis. ZTGKT is not a filter you may call.
It is the only door.

## Phase 2: the defect

The archive records the failure in direct terms:

> These legacy components aggressively censored clinical signals by flagging
> hedging (e.g., "might", "may") and sycophancy incorrectly.

And, on the root cause:

> Formerly conflated linguistic polish with clinical signal validation.

The gate had one vocabulary and two jobs. Rejecting "may" is right when the
output is a governance record, where a hedge is evasion. It is wrong when the
output is a clinical signal, where a hedge is the clinician's calibrated
uncertainty and carries information a downstream reader needs. A single
component enforcing one rule in both positions had to be wrong in one of them.

This is a general failure mode worth naming: **a validator that encodes a
domain assumption cannot be positioned as universal infrastructure.** The
assumption travels with it into every position it occupies.

## Phase 3: the split

The archive's fix separates the two jobs by polarity:

```
        ZTGKT (mandatory, universal)
                   |
        +----------+----------+
        |                     |
ContentPolishPipeline   ClinicalSignalValidator
   (optional)              (mandatory)
   external-facing         domain-facing
   hedging = defect        hedging = signal
   strips uncertainty      preserves uncertainty
```

Related changes in the same pass: `HTTP` (Hyper Text Truth Protocol) was
replaced by an optional `ToneNormalizationPipeline`, and `CITADEL`'s quality
routing was folded into the domain validator "with clearer intent".

Both halves ship in this repository. Neither supersedes the other. They are
the same mechanism configured for opposite jobs, and the point of keeping both
under one roof is that the pairing is the lesson.

## Phase 4: the arbitration problem

The archive then identifies a problem the split created rather than solved.
By that point four components each answered some version of "is this content
acceptable?":

```
ZTGKT says PASS
      |
HTTP says FAIL
      |
DIT says MODIFY
      |
CITADEL says REWRITE
```

The archived conclusion is that a single governance arbitration layer is
required. A `GovernanceEngine` appears in later inventories as the replacement
that "accurately separates sycophancy filtration from objective clinical
coherence checks".

That layer is **out of scope here**. It is a stack-level concern that
supersedes ZTGKT rather than extending it, and building it would make this
repository something other than a reconstruction of ZTGKT. It is noted so the
boundary is explicit rather than accidental.
