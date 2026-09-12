# Architecture

## The gate loop

```
        caller prompt
              |
              v
   +---------------------+
   |  execution_gateway  |  <--- your generator
   +---------------------+
              |  raw text
              v
   +---------------------+
   |   TextNormalizer    |  collapse vague verbs onto "use"
   +---------------------+
              |  normalized text
              v
   +---------------------+
   |    guard chain      |  pronoun / speculation / empirical
   +---------------------+
              |
      pass?  / \  fail
            /   \
           v     v
   +----------+  +------------------------+
   | throttle |  | hash, record, feedback |
   +----------+  +------------------------+
        |                    |
        v                    | rebuild prompt from ORIGINAL + feedback
   +----------+              |
   |  sign    |              +--> retry, until budget exhausted
   +----------+
        |
        v
   GateResult
```

## Why "zero trust"

Three properties, each load-bearing.

**No standing credit.** Validation state is per-attempt. Nothing a generator
did earlier makes the current output more acceptable. The gate holds no
reputation model.

**No laundering authority.** Beyond the verb normalization, the gate cannot
rewrite a response into passing. If output fails, the generator produces a new
one. This matters because a gate that could edit its way to compliance would
be the thing producing the record, not the thing checking it.

**Feedback is rebuilt, not stacked.** Each retry prompt is
`original_prompt + feedback`, never `previous_retry_prompt + feedback`. The
prompt cannot grow without bound across attempts, and attempt *n* is not
biased by the wording of attempt *n-1*'s complaint.

## Why "kinetic throttle"

`ExecutionPacer` delays release of accepted content in proportion to its
length, clamped:

```
delay = clamp(word_count * 0.002 * 0.815, 15ms, 200ms)
```

The `0.815` coefficient is the recurring "815" tag from this system family.
Note the clamp geometry: at the default slope the ceiling binds at about 123
words, so anything longer than a short paragraph paces at the flat 200 ms cap.
The floor binds below about 9 words. The proportional band is narrow by
design.

This is a pacing governor, not a rate limiter. It smooths the release of a
single accepted payload. It does not track a budget across calls and will not
protect a downstream service from sustained load.

## Attestation

The signature is HMAC-SHA384 over the UTF-8 bytes of the returned content,
computed after normalization and after the guards pass. A consumer holding the
key can confirm two things: the bytes are unmodified, and they were released by
a holder of the key. Verification uses `hmac.compare_digest`, so a mismatch
leaks no timing information.

Two different hashes appear in this codebase and they do different jobs:

| | `hashlib.md5` in `pipeline.py` | `hmac.new(..., sha384)` in `signing.py` |
|---|---|---|
| Purpose | detect the generator looping on its own rejected output | attest accepted content to a downstream consumer |
| Scope | one `execute()` call, in-process | crosses a trust boundary |
| Keyed | no | yes |
| Security-relevant | no | yes |

MD5 is correct for the first job and would be wrong for the second. It is
called with `usedforsecurity=False` to say so explicitly and to keep the
package importable on FIPS-restricted builds.

## Extension points

`GateConfig` covers the tunables. Beyond that:

- **Custom vocabulary.** Build a `PatternSet` from your own registry and pass
  it as `GateConfig.patterns`. `PatternSet` snapshots its source on
  construction, so later mutation of the source mapping cannot change a live
  filter chain.
- **Custom guards.** Pass `guards=[...]` to the pipeline. A guard is anything
  with `name`, `failure_message`, and `is_clean(text) -> bool`. The
  `failure_message` is what lands in the retry prompt, so write it as an
  instruction the generator can act on.
- **Disable a stage.** `normalize=False` and `detect_duplicates=False` turn
  off the two non-guard behaviors independently.
