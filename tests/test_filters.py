import pytest

from ztgkt import (
    EmpiricalValidationFilter,
    PersonalPronounFilter,
    SpeculativeLanguageFilter,
    TextNormalizer,
)

CLEAN = "Throughput fell 12 percent because the queue drained slowly."


@pytest.mark.parametrize("text", ["I reviewed the log.", "We saw the spike.", "Our node failed."])
def test_pronoun_filter_rejects_first_person(text):
    assert PersonalPronounFilter().is_clean(text) is False


def test_pronoun_filter_accepts_impersonal_prose():
    assert PersonalPronounFilter().is_clean(CLEAN) is True


@pytest.mark.parametrize("text", ["The node might fail.", "Latency could rise.", "The result seems fine."])
def test_speculation_filter_rejects_hedging(text):
    assert SpeculativeLanguageFilter().is_clean(text) is False


def test_speculation_filter_accepts_assertive_prose():
    assert SpeculativeLanguageFilter().is_clean(CLEAN) is True


def test_empirical_filter_accepts_causal_connective_without_numbers():
    assert EmpiricalValidationFilter().is_clean("Throughput fell because the queue drained.") is True


def test_empirical_filter_accepts_numbers_without_causality():
    assert EmpiricalValidationFilter().is_clean("Throughput fell 12 percent.") is True


def test_empirical_filter_rejects_bare_assertion():
    assert EmpiricalValidationFilter().is_clean("Throughput fell.") is False


def test_normalizer_collapses_prohibited_verbs():
    out = TextNormalizer().process("Optimize the cache and leverage the index.")
    assert "ptimize" not in out and "everage" not in out
    assert out.count("use") == 2


def test_normalizer_does_not_catch_inflected_forms():
    """Documents a known gap in the archived regex.

    ``prohibited_verbs`` is word-bounded on the bare stem, so "optimized",
    "optimizing" and "optimization" all pass through untouched. Preserved as
    archived behavior rather than silently widened. See docs/KNOWN_GAPS.md.
    """
    text = "Writes were optimized and the index is improving."
    assert TextNormalizer().process(text) == text


def test_normalizer_leaves_other_text_untouched():
    assert TextNormalizer().process(CLEAN) == CLEAN
