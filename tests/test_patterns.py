import re

from ztgkt import DEFAULT_PATTERNS, VALIDATION_PATTERNS, PatternSet


def test_pattern_set_snapshots_its_source():
    source = {"x": re.compile("a")}
    ps = PatternSet(source)
    source["x"] = re.compile("zzz")
    assert ps.matches("x", "a") is True


def test_unknown_pattern_never_matches():
    assert DEFAULT_PATTERNS.matches("not_a_pattern", "anything") is False


def test_archive_registry_keys_are_preserved():
    assert set(VALIDATION_PATTERNS) == {
        "first_person_tokens",
        "hedging_tokens",
        "prohibited_verbs",
        "causal_connectives",
        "numeric_metrics",
    }
