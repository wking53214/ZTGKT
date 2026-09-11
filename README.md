# ZTGKT

**Zero-Trust Guardrails & Kinetic Throttle**

An execution-boundary layer for text generation. ZTGKT sits between a caller
and a generator and lets nothing through that fails its guards.

This repository is a reconstruction. ZTGKT was designed and refined across the
author's AI conversation history between roughly April and August 2026, but
only ever existed as a section inside a larger single-file system
(`UGPIS-Ω`). It was never broken out into a repository of its own. This is
that repository, rebuilt from the archived source. See
[PROVENANCE.md](PROVENANCE.md) for what is verbatim and what is reconstructed.

---

## What it does

Two halves, per the name.

**Zero-Trust Guardrails.** Every generation is re-validated from scratch. A
clean result earns no standing credit; the next output is checked exactly as
hard as the first. The gate cannot edit content into compliance. It either
accepts what the generator produced or asks for another attempt, with feedback
naming each rule that failed.

**Kinetic Throttle.** Accepted output is paced by length before release, with
a floor and a ceiling. This smooths burst release rather than capping
throughput.

Accepted content is signed with HMAC-SHA384, so a downstream consumer can
prove it received exactly what the gate accepted.

## The three guards

| Guard | Rejects | Rationale from the archive |
|---|---|---|
| `PersonalPronounFilter` | first-person language | Output is a system record, not a participant's account |
| `SpeculativeLanguageFilter` | hedging vocabulary | A governance record should assert or stay silent |
| `EmpiricalValidationFilter` | claims with neither a stated cause nor a number | An unfalsifiable claim is not a record |

`TextNormalizer` runs first and collapses a family of vague improvement verbs
(`optimize`, `enhance`, `leverage`, ...) onto the single verb `use`. The
normalized text is what gets validated, signed, and returned.

## Install

```bash
pip install -e ".[dev]"
```

No runtime dependencies. Python 3.9+.

## Use

```python
import asyncio
from ztgkt import ContentValidationPipeline, GateConfig

async def generate(prompt: str) -> str:
    ...  # your model call

gate = ContentValidationPipeline(
    generate,
    GateConfig(signing_key=b"a-real-key", max_attempts=5),
)

result = asyncio.run(gate.execute("Report the latency change."))
print(result.validated_content)
print(result.payload_signature)
print(result.retry_attempts)
```

On budget exhaustion the gate raises `PipelineFailure`, which carries the
per-attempt record so you can see what kept failing:

```python
from ztgkt import PipelineFailure

try:
    result = await gate.execute(prompt)
except PipelineFailure as exc:
    for attempt in exc.attempts:
        print(attempt.iteration, attempt.failures)
```

## The split

ZTGKT's guards carry a domain assumption: hedging is a defect. That is correct
for a governance record and **wrong for a clinical signal**, where hedging is
the clinician's calibrated uncertainty and stripping it destroys information.
The archive caught this and split the component in two.

- [`ztgkt.polish`](ztgkt/polish.py) keeps the original rules, now **optional**
  and scoped to operator-facing output.
- [`ztgkt.domain`](ztgkt/domain.py) is the **mandatory** half, with the
  opposite polarity: it requires anchors (when, how much, about what) and
  treats hedging as a signal to preserve.

Both are shipped. The reasoning is in [docs/LINEAGE.md](docs/LINEAGE.md).

## Layout

```
ztgkt/
  patterns.py   regex registries (VALIDATION_PATTERNS, EVALUATION_PATTERNS)
  filters.py    the three guards plus TextNormalizer
  throttle.py   ExecutionPacer, the kinetic half
  signing.py    HMAC-SHA384 attestation
  pipeline.py   ContentValidationPipeline, the gate itself
  polish.py     ContentPolishPipeline, the post-split presentation path
  domain.py     ClinicalSignalValidator, the post-split domain path
  config.py     GateConfig
docs/
  ARCHITECTURE.md      how the gate works and why
  LINEAGE.md           the evolution and the defect that drove the split
  INTEGRATION.md       ZTGKT's position in the UGPIS-Ω pipeline
  KNOWN_GAPS.md        preserved defects, with the case for each
reference/
  verbatim archive extracts, not imported
tests/
  47 tests
```

## Tests

```bash
python -m pytest -q
```

## Security notes

Read [docs/KNOWN_GAPS.md](docs/KNOWN_GAPS.md) before deploying. In short:

- The archive hardcoded its HMAC key in source. That key is preserved only as
  `ARCHIVE_DEFAULT_KEY` for replaying archived signatures, and using it emits a
  warning. Pass your own `signing_key`.
- Guard vocabularies are fixed word lists. They are a formatting policy, not an
  adversarial control. Do not rely on them against a motivated evader.
