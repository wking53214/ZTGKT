"""Regex pattern registries used by the ZTGKT guardrail filters.

Two registries are preserved from the archive:

``VALIDATION_PATTERNS``
    Drives the enforcement path. A generation is rejected when it trips a
    prohibited pattern.

``EVALUATION_PATTERNS``
    A scoring-only superset used by the audit path. It adds passive-voice
    detection and a wider hedging vocabulary. It never blocks generation.

Both registries are module-level and mutable in the archive source. This
module keeps the same default values but exposes them through
:class:`PatternSet` so a caller can supply a different vocabulary without
mutating global state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Mapping

__all__ = [
    "VALIDATION_PATTERNS",
    "EVALUATION_PATTERNS",
    "PatternSet",
    "DEFAULT_PATTERNS",
    "AUDIT_PATTERNS",
]


VALIDATION_PATTERNS: Dict[str, re.Pattern] = {
    "first_person_tokens": re.compile(
        r"\b(i|me|my|mine|myself|we|us|our|ours|ourselves)\b",
        re.IGNORECASE,
    ),
    "hedging_tokens": re.compile(
        r"\b(may|might|could|seems|generally|potentially|likely|perhaps|maybe)\b",
        re.IGNORECASE,
    ),
    "prohibited_verbs": re.compile(
        r"\b(improve|optimize|enhance|enable|support|strengthen|utilize|leverage)\b",
        re.IGNORECASE,
    ),
    "causal_connectives": re.compile(
        r"\b(because|due to|driven by|resulting from|caused by)\b",
        re.IGNORECASE,
    ),
    "numeric_metrics": re.compile(r"\b\d+(\.\d+)?%|\b\d+\b"),
}

EVALUATION_PATTERNS: Dict[str, re.Pattern] = {
    "first_person_tokens": re.compile(
        r"\b(i|me|my|mine|myself|we|us|our|ours|ourselves)\b", re.IGNORECASE
    ),
    "hedging_tokens": re.compile(
        r"\b(may|might|could|seems|generally|potentially|likely|perhaps|probably|I think)\b",
        re.IGNORECASE,
    ),
    "passive_voice_forms": re.compile(
        r"\b(am|is|are|was|were|be|been|being)\b\s+\w+(ed|en)\b", re.IGNORECASE
    ),
    "numeric_metrics": re.compile(r"\b\d+(\.\d+)?%|\b\d+\b"),
    "causal_connectives": re.compile(
        r"\b(because|due to|driven by|resulting from|caused by|therefore|consequently)\b",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class PatternSet:
    """An immutable view over a pattern registry.

    ``patterns`` is copied on construction, so later mutation of the source
    mapping cannot change an already-built filter chain.
    """

    patterns: Mapping[str, re.Pattern] = field(default_factory=lambda: dict(VALIDATION_PATTERNS))

    def __post_init__(self) -> None:
        object.__setattr__(self, "patterns", dict(self.patterns))

    def __getitem__(self, key: str) -> re.Pattern:
        return self.patterns[key]

    def get(self, key: str) -> re.Pattern | None:
        return self.patterns.get(key)

    def matches(self, key: str, text: str) -> bool:
        """True when pattern ``key`` is present in ``text``.

        A pattern that is absent from the registry never matches. That keeps a
        trimmed-down registry usable rather than raising mid-validation.
        """
        pattern = self.patterns.get(key)
        return bool(pattern.search(text)) if pattern else False


DEFAULT_PATTERNS = PatternSet(VALIDATION_PATTERNS)
AUDIT_PATTERNS = PatternSet(EVALUATION_PATTERNS)
