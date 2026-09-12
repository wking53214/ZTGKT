"""Domain-signal validation: the half ZTGKT should never have owned.

The archive records the defect plainly. The original gate rejected hedging
("may", "might", "could") everywhere. Applied to a clinical signal that is
exactly backwards: hedging is the clinician's calibrated uncertainty, and
stripping it destroys information a downstream reader needs.

The fix was to split the concern. Presentation polish kept the old rules and
became optional (:mod:`ztgkt.polish`). Domain validation became a separate,
mandatory check with the opposite polarity: it demands anchors (when, how much,
about what) and treats hedging as a signal to preserve, not a defect to strip.

:class:`ClinicalSignalValidator` preserves the archived clinical marker set.
:class:`DomainSignalValidator` is the same mechanism with a caller-supplied
marker set, for domains other than the clinical one.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Tuple

__all__ = ["DomainSignalValidator", "ClinicalSignalValidator", "CLINICAL_MARKERS"]


CLINICAL_MARKERS: Dict[str, re.Pattern] = {
    "temporal_specificity": re.compile(
        r"\b(\d{1,2}:\d{2}|hour|minute|second|onset)\b", re.IGNORECASE
    ),
    "numeric_value": re.compile(
        r"\b\d+(\.\d+)?(?:\s*(?:bpm|mmHg|beats|percent|%|SpO2|O2|sats))\b", re.IGNORECASE
    ),
    "clinical_context": re.compile(
        r"\b(patient|neonate|infant|pediatric|vital|monitor|alert|abnormal)\b", re.IGNORECASE
    ),
}

MARKER_FAILURES: Dict[str, str] = {
    "temporal_specificity": "Missing temporal specificity (when did this occur?)",
    "numeric_value": "Missing quantitative values (vital signs, measurements)",
    "clinical_context": "Missing clinical context (what patient/system?)",
}

# Hedging is retained rather than rejected. Kept as a named pattern so callers
# can report on it, never to gate on it.
CALIBRATED_UNCERTAINTY = re.compile(
    r"\b(may|might|could|possibly|uncertain|unclear|suggest)\b", re.IGNORECASE
)


class DomainSignalValidator:
    """Requires a signal to carry its own anchors. Never strips uncertainty."""

    def __init__(
        self,
        markers: Mapping[str, re.Pattern],
        failure_messages: Mapping[str, str] | None = None,
        profile_name: str = "domain",
        log_sample_chars: int = 100,
    ) -> None:
        self.markers = dict(markers)
        self.failure_messages = dict(failure_messages or {})
        self.profile_name = profile_name
        self.log_sample_chars = log_sample_chars
        self.validation_log: List[Dict[str, Any]] = []

    def _message(self, key: str) -> str:
        return self.failure_messages.get(key, f"Missing required marker: {key}")

    def validate_signal(self, signal_text: str) -> Tuple[bool, List[str]]:
        """Returns ``(is_valid, failures)``. Absent markers are the only failures."""
        failures = [
            self._message(key)
            for key, pattern in self.markers.items()
            if not pattern.search(signal_text)
        ]
        is_valid = not failures

        self.validation_log.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "profile": self.profile_name,
                "signal_sample": signal_text[: self.log_sample_chars],
                "is_valid": is_valid,
                "failures": failures,
                "carries_calibrated_uncertainty": bool(CALIBRATED_UNCERTAINTY.search(signal_text)),
            }
        )
        return is_valid, failures


class ClinicalSignalValidator(DomainSignalValidator):
    """Domain validator carrying the archived clinical marker set.

    ``REQUIRED_CLINICAL_MARKERS`` and ``HEDGING_IS_GOOD`` are retained as class
    attributes under their archive names.
    """

    REQUIRED_CLINICAL_MARKERS = CLINICAL_MARKERS
    HEDGING_IS_GOOD = CALIBRATED_UNCERTAINTY

    def __init__(self, profile_name: str = "clinical") -> None:
        super().__init__(CLINICAL_MARKERS, MARKER_FAILURES, profile_name=profile_name)
