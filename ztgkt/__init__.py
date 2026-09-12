"""ZTGKT: Zero-Trust Guardrails & Kinetic Throttle.

An execution-boundary layer for text generation. It sits between a caller and
a generator, and lets nothing through that fails its guards.

Two halves, per the name:

- **Zero-Trust Guardrails** re-validate every generation from scratch. A pass
  earns no standing credit; the next output is checked as hard as the first.
- **Kinetic Throttle** paces accepted output by length before release.

Accepted content is signed (HMAC-SHA384), so a downstream consumer can prove
it received exactly what the gate accepted.

Quick start::

    import asyncio
    from ztgkt import ContentValidationPipeline, GateConfig

    async def generate(prompt: str) -> str:
        return "Latency fell 18 percent because the cache was warmed."

    gate = ContentValidationPipeline(generate, GateConfig(signing_key=b"..."))
    result = asyncio.run(gate.execute("Report the latency change."))
    print(result.validated_content, result.payload_signature)
"""

from __future__ import annotations

from .config import GateConfig
from .domain import ClinicalSignalValidator, DomainSignalValidator
from .filters import (
    EmpiricalValidationFilter,
    Guard,
    PersonalPronounFilter,
    SpeculativeLanguageFilter,
    TextNormalizer,
    default_guards,
)
from .patterns import (
    AUDIT_PATTERNS,
    DEFAULT_PATTERNS,
    EVALUATION_PATTERNS,
    VALIDATION_PATTERNS,
    PatternSet,
)
from .pipeline import (
    ContentValidationPipeline,
    GateResult,
    PipelineFailure,
    ValidationAttempt,
)
from .polish import ContentPolishPipeline
from .signing import ARCHIVE_DEFAULT_KEY, PayloadSigner
from .throttle import ExecutionPacer

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "ContentValidationPipeline",
    "ContentPolishPipeline",
    "GateConfig",
    "GateResult",
    "PipelineFailure",
    "ValidationAttempt",
    "Guard",
    "PersonalPronounFilter",
    "SpeculativeLanguageFilter",
    "EmpiricalValidationFilter",
    "TextNormalizer",
    "default_guards",
    "ExecutionPacer",
    "PayloadSigner",
    "ARCHIVE_DEFAULT_KEY",
    "PatternSet",
    "DEFAULT_PATTERNS",
    "AUDIT_PATTERNS",
    "VALIDATION_PATTERNS",
    "EVALUATION_PATTERNS",
    "DomainSignalValidator",
    "ClinicalSignalValidator",
    "CLINICAL_MARKERS",
]

from .domain import CLINICAL_MARKERS  # noqa: E402  (re-export after __all__)
