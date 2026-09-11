# Provenance

Everything in this repository traces to the author's own archived AI
conversation history. Nothing was invented to fill a gap. Where the archive
described a design without writing it out, the file is marked RECONSTRUCTED and
the archived description it derives from is cited.

## Source corpus

| Repository | What it holds |
|---|---|
| `wking53214/Claude_History` | Claude exports, transcripts, derived summaries |
| `wking53214/ChatGPT_History` | ChatGPT exports and transcripts |
| `wking53214/Gemini_History` | Google Takeout, including loose source files |
| `wking53214/Gemini_Extraction` | normalized message and artifact indexes |
| `wking53214/CoPilot_History` | Copilot transcripts |

ZTGKT is attested across all five. The densest sources:

| Source | ZTGKT mentions |
|---|---|
| `ChatGPT_History/transcripts/6a67ec9b-9e48-83ea-a71c-f19ad8ec3c87.md` | 26 |
| `Claude_History/transcripts/0d8f9021-a6de-438a-b6cc-0c92bdd322d6.md` | 24 |
| `Claude_History/transcripts/e8e5bb13-bb8f-42ab-a9c0-40fd2f579476.md` | 15 |
| `Claude_History/transcripts/2e330101-2220-4de0-825b-aa10db78ab30.md` | 14 |
| `Claude_History/transcripts/3c9661bd-d4d2-4ee2-ba79-160b9078f16d.md` | 12 |
| `Gemini_History/Takeout/My Activity/Gemini Apps/ugpis*.txt` | post-refactor source files |

## Classification

### VERBATIM

Reproduced unmodified. Not imported by the package.

| File | Source |
|---|---|
| `reference/ugpis_omega_ztgkt_section.py` | `ChatGPT_History/transcripts/6a67ec9b-9e48-83ea-a71c-f19ad8ec3c87.md` lines 2607-2732 |
| `reference/ugpis_omega_refactored_split.py` | `Gemini_History/Takeout/My Activity/Gemini Apps/ugpis_omega_fixed_02.txt` lines 70-196 and 416-463 |

### PRESERVED

Archived logic and constants carried over exactly. Structure changed (split
into modules, made configurable); behavior did not.

| File | Preserved from the archive |
|---|---|
| `ztgkt/patterns.py` | `VALIDATION_PATTERNS` and `EVALUATION_PATTERNS`, both registries complete and unedited |
| `ztgkt/filters.py` | `PersonalPronounFilter`, `SpeculativeLanguageFilter`, `EmpiricalValidationFilter`, `TextNormalizer` |
| `ztgkt/throttle.py` | `ExecutionPacer`, including `15.0` / `0.815` / `0.002` / `0.200` |
| `ztgkt/pipeline.py` | `ContentValidationPipeline` control flow, the `[RECALIBRATION_FEEDBACK]` template, all four failure strings, the `CRITICAL_PIPELINE_FAILURE` message, the result dict shape, MD5 duplicate detection |
| `ztgkt/polish.py` | `ContentPolishPipeline` as the optional post-split presentation path |
| `ztgkt/domain.py` | `ClinicalSignalValidator`, `REQUIRED_CLINICAL_MARKERS`, `HEDGING_IS_GOOD`, all three failure messages |
| `ztgkt/signing.py` | HMAC-SHA384 construction and the literal key, retained as `ARCHIVE_DEFAULT_KEY` |

### RECONSTRUCTED

Not present in the archive as code. Built to serve the archived design, or
added to make the package usable as a package.

| File | Basis |
|---|---|
| `ztgkt/config.py` | The archive's constructor arguments, lifted into one object. Defaults reproduce archived behavior exactly. |
| `ztgkt/__init__.py` | Package surface. No new behavior. |
| `ztgkt/pipeline.py` `PipelineFailure`, `ValidationAttempt`, `GateResult` | The archive raised a bare `SystemError` and returned a dict. These preserve both surfaces (`GateResult.as_dict()`, `result["key"]`) and add per-attempt records for triage. |
| `ztgkt/domain.py` `DomainSignalValidator` | Generalization of the archived clinical validator to a caller-supplied marker set. The clinical subclass is unchanged. |
| `ztgkt/patterns.py` `PatternSet` | Wrapper making the archived module-level registries injectable instead of global. |
| `tests/` | Written for this reconstruction. No test suite exists in the archive. |
| `pyproject.toml`, `.gitignore` | Packaging. |
| `docs/*`, `README.md` | Written for this reconstruction. Every quotation is cited to the archive; the analysis is this repository's. |

## Deliberate departures

Four, each a correction the archive itself called for or a defect it left
open. All are recorded in `docs/KNOWN_GAPS.md`.

1. **Signing key is injectable.** The archive hardcoded it. The literal is
   retained for replay and now warns on use.
2. **`PipelineFailure` replaces `SystemError`.** A `RuntimeError` subclass, so
   callers can catch the gate's failure without catching interpreter errors.
   Carries the attempt record.
3. **MD5 called with `usedforsecurity=False`.** Same digest, same behavior.
   States the intent and keeps the package importable on FIPS-restricted
   builds.
4. **Module-level pattern registries are injectable.** The archived globals are
   still exported under their original names.

## What was deliberately not built

The archive identifies a governance arbitration problem downstream of ZTGKT
(four components each answering "is this content acceptable?") and proposes a
`GovernanceEngine` to resolve it. That layer supersedes ZTGKT rather than
extending it, and building it here would make this repository something other
than a reconstruction of ZTGKT. The boundary is discussed in
`docs/LINEAGE.md`.

## Verification

To re-derive the source material:

```bash
grep -ril "ztgkt" ~/Claude_History ~/ChatGPT_History ~/Gemini_History ~/Gemini_Extraction
```
