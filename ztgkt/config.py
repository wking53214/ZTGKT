"""Configuration for a ZTGKT gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .patterns import DEFAULT_PATTERNS, PatternSet

__all__ = ["GateConfig"]


@dataclass
class GateConfig:
    """Tunables for :class:`ztgkt.pipeline.ContentValidationPipeline`.

    Defaults reproduce the archived behavior exactly.

    Attributes:
        max_attempts: Regeneration budget. Exhausting it raises
            :class:`ztgkt.pipeline.PipelineFailure`.
        patterns: Vocabulary registry driving the guards.
        signing_key: HMAC key. ``None`` uses a random per-instance key and
            emits a warning; the published archive key is never a default.
        minimum_latency_ms: Throttle floor.
        maximum_latency_ms: Throttle ceiling.
        seconds_per_word: Throttle slope before scaling.
        scaling_coefficient: Throttle scale factor.
        normalize: Apply :class:`ztgkt.filters.TextNormalizer` before validating.
        detect_duplicates: Reject a regeneration byte-identical to one already
            rejected in this call. Guards against a model looping on the same
            rejected output until the attempt budget runs out.
    """

    max_attempts: int = 5
    patterns: PatternSet = field(default_factory=lambda: DEFAULT_PATTERNS)
    signing_key: Optional[bytes | str] = None
    minimum_latency_ms: float = 15.0
    maximum_latency_ms: float = 200.0
    seconds_per_word: float = 0.002
    scaling_coefficient: float = 0.815
    normalize: bool = True
    detect_duplicates: bool = True

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")
