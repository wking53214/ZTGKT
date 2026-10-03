# Known gaps

Defects preserved from the archive, each with the case for keeping it. Nothing
here was widened silently; where behavior is wrong, it is wrong on purpose and
documented.

## 1. Hardcoded signing key

The archive embedded its HMAC key as a source literal:

```python
self._signing_key = b"GENERIC_PIPELINE_HMAC_SECRET_KEY_SHA384_815"
```

A key committed to source is not a secret. Anyone with read access to the
repository can forge a signature, which makes the attestation worthless
against exactly the adversary it exists to stop.

**Status: fixed, with the old value retained.** `GateConfig.signing_key` is
the supported path. The literal survives as `ARCHIVE_DEFAULT_KEY` so archived
signatures can be replayed and verified when it is passed explicitly. It is
never a default: constructing a `PayloadSigner` without a key uses a random
per-instance key (changed 2026-09-24; before that the archive key was the
default) and emits a `UserWarning`. Pass a real key in any deployment where
the signature is treated as evidence.

## 2. Guards do not match inflected forms

Every pattern is word-bounded on a bare stem. `\b(...optimize...)\b` does not
match `optimized`, `optimizing`, or `optimization`. The same holds for the
hedging list: `seems` is listed, `seem` is not.

**Status: preserved.** Two reasons. Widening the patterns changes what passes
the gate, which changes the archived behavior this repository exists to
reconstruct. And stemming has its own false positives, which is a policy
decision for a deployment rather than for the reconstruction. Supply your own
`PatternSet` if you want broader coverage.

`tests/test_filters.py::test_normalizer_does_not_catch_inflected_forms` pins
this so it cannot regress into an accidental "fix".

## 3. Guards are not an adversarial control

The vocabularies are fixed word lists. A generator that is merely careless
will trip them; a generator that is steered to evade them will not. Synonyms,
unicode homoglyphs, and rephrasing all pass.

**Status: by design, stated plainly.** ZTGKT is a formatting and record-quality
policy. Treating it as a safety boundary would be a category error. If you need
an adversarial control, it belongs at a different layer.

## 4. `EmpiricalValidationFilter` accepts any digit

`numeric_metrics` is `\b\d+(\.\d+)?%|\b\d+\b`. A bare `1` anywhere in the text
satisfies the "has metrics" branch, including a list index, a year, or an ID.

**Status: preserved.** The filter's job is to reject an *unanchored* claim,
and the archive's threshold for "anchored" is deliberately low: it is a smoke
test, not a proof. Tightening it would reject legitimate prose that cites a
date or an identifier.

## 5. The throttle's proportional band is narrow

At default settings the ceiling binds at about 123 words and the floor at
about 9. Most real payloads therefore pace at the flat 200 ms cap, and the
length-proportional behavior the design describes applies only to a narrow
middle range.

**Status: preserved, constants exposed.** The archived constants are the
defaults. `seconds_per_word`, `scaling_coefficient`, and both bounds are
constructor arguments on `ExecutionPacer` and fields on `GateConfig`, so the
band can be widened without editing the package.

## 6. The throttle is not a rate limiter

It paces a single accepted payload. It keeps no cross-call budget and will not
protect a downstream service under sustained load.

**Status: by design.** Named here because "throttle" invites the other
reading.

## 7. Attempt budget is per call, and the generator is trusted to vary

If the generator is deterministic, every attempt returns the same rejected
text and the budget burns for nothing. Duplicate detection catches this and
reports it, but cannot fix it.

**Status: mitigated, not solved.** `detect_duplicates` surfaces the loop in
`PipelineFailure.attempts`, so the failure is diagnosable rather than opaque.
Varying the generation (temperature, sampling) is the caller's responsibility.
