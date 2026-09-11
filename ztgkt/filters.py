"""The four linguistic guards that make up the "Zero-Trust Guardrails" half.

Three of them are predicates: they answer "is this text clean?" without
changing it. The fourth, :class:`TextNormalizer`, rewrites text in place.

Zero-trust here means every generation is re-checked on every attempt. A
passing result from a previous iteration grants no credit to the next one.
"""

from __future__ import annotations

from typing import List, Protocol

from .patterns import DEFAULT_PATTERNS, PatternSet

__all__ = [
    "Guard",
    "PersonalPronounFilter",
    "SpeculativeLanguageFilter",
    "EmpiricalValidationFilter",
    "TextNormalizer",
    "default_guards",
]


class Guard(Protocol):
    """A named predicate over generated text."""

    name: str
    failure_message: str

    def is_clean(self, text: str) -> bool: ...


class _PatternGuard:
    name = "guard"
    failure_message = "Guard failed."

    def __init__(self, patterns: PatternSet | None = None) -> None:
        self.patterns = patterns or DEFAULT_PATTERNS

    def is_clean(self, text: str) -> bool:  # pragma: no cover - overridden
        raise NotImplementedError


class PersonalPronounFilter(_PatternGuard):
    """Rejects first-person language.

    The stack this came from routes operator-facing output, where a system
    speaking as "I" or "we" is treated as a provenance defect: the text should
    read as a system record, not as a participant's account.
    """

    name = "personal_pronoun"
    failure_message = "First-person language signature registered."

    def is_clean(self, text: str) -> bool:
        return not self.patterns.matches("first_person_tokens", text)


class SpeculativeLanguageFilter(_PatternGuard):
    """Rejects hedging vocabulary.

    Note the domain assumption baked in here: hedging is a defect. That is
    correct for a governance record and wrong for a clinical signal, which is
    what eventually split this component in two. See ``docs/LINEAGE.md``.
    """

    name = "speculative_language"
    failure_message = "Qualifying or ambiguous statements registered."

    def is_clean(self, text: str) -> bool:
        return not self.patterns.matches("hedging_tokens", text)


class EmpiricalValidationFilter(_PatternGuard):
    """Requires a causal connective or a numeric value.

    This is the only guard that demands something be present rather than
    absent. A claim with neither a stated cause nor a number is treated as
    unfalsifiable and rejected.
    """

    name = "empirical_validation"
    failure_message = "Missing explicit rationales or metrics."

    def is_clean(self, text: str) -> bool:
        has_causality = self.patterns.matches("causal_connectives", text)
        has_metrics = self.patterns.matches("numeric_metrics", text)
        return has_causality or has_metrics


class TextNormalizer:
    """Collapses a family of vague improvement verbs onto the single verb "use".

    This runs before the guards, so normalization is what gets validated,
    signed and returned. The substitution is deliberately blunt: the archive
    treats "optimize"/"enhance"/"leverage" as interchangeable filler.
    """

    def __init__(self, patterns: PatternSet | None = None, replacement: str = "use") -> None:
        self.patterns = patterns or DEFAULT_PATTERNS
        self.replacement = replacement

    def process(self, text: str) -> str:
        pattern = self.patterns.get("prohibited_verbs")
        return pattern.sub(self.replacement, text) if pattern else text


def default_guards(patterns: PatternSet | None = None) -> List[Guard]:
    """The stock guard chain, in the order the archive applies it."""
    patterns = patterns or DEFAULT_PATTERNS
    return [
        PersonalPronounFilter(patterns),
        SpeculativeLanguageFilter(patterns),
        EmpiricalValidationFilter(patterns),
    ]
