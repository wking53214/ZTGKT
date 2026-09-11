from ztgkt import ClinicalSignalValidator, DomainSignalValidator
import re

GOOD = "At 14:22 the patient SpO2 reading fell to 88 percent."


def test_complete_clinical_signal_validates():
    ok, failures = ClinicalSignalValidator().validate_signal(GOOD)
    assert ok is True and failures == []


def test_missing_time_anchor_fails():
    ok, failures = ClinicalSignalValidator().validate_signal("The patient SpO2 fell to 88 percent.")
    assert ok is False
    assert any("temporal" in f for f in failures)


def test_missing_measurement_fails():
    ok, failures = ClinicalSignalValidator().validate_signal("At 14:22 the patient was monitored.")
    assert ok is False
    assert any("quantitative" in f for f in failures)


def test_missing_context_fails():
    ok, failures = ClinicalSignalValidator().validate_signal("At 14:22 a reading of 88 percent.")
    assert ok is False
    assert any("clinical context" in f for f in failures)


def test_hedging_is_preserved_not_penalised():
    """The defect that caused the split: hedging must never fail a domain signal."""
    hedged = "At 14:22 the patient SpO2 of 88 percent may indicate desaturation."
    validator = ClinicalSignalValidator()
    ok, failures = validator.validate_signal(hedged)
    assert ok is True and failures == []
    assert validator.validation_log[-1]["carries_calibrated_uncertainty"] is True


def test_validation_log_records_each_call():
    validator = ClinicalSignalValidator()
    validator.validate_signal(GOOD)
    validator.validate_signal("nothing useful")
    assert len(validator.validation_log) == 2
    assert [e["is_valid"] for e in validator.validation_log] == [True, False]


def test_generic_validator_accepts_a_custom_marker_set():
    validator = DomainSignalValidator(
        {"ticket": re.compile(r"\b[A-Z]+-\d+\b")},
        {"ticket": "Missing ticket reference"},
        profile_name="ops",
    )
    assert validator.validate_signal("Rollback for OPS-4412 completed.")[0] is True
    assert validator.validate_signal("Rollback completed.")[1] == ["Missing ticket reference"]
