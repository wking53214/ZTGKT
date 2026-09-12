"""The ZTGKT gate: guarded generation with bounded regeneration.

Control flow, unchanged from the archive:

1. Call the downstream generator with the active prompt.
2. Normalize the response.
3. Run every guard against the normalized text.
4. Hash the normalized text and check it against this call's reject history.
5. On a clean, non-duplicate result: pace, sign, return.
6. Otherwise record the hash, build a feedback line naming each failure, append
   it to the original prompt, and retry.
7. On budget exhaustion: raise.

The gate never edits a response into compliance beyond the verb normalization.
It either accepts the generator's own output or asks for another one. That is
the zero-trust property: the gate holds no authority to launder content.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Set

from .config import GateConfig
from .filters import Guard, TextNormalizer, default_guards
from .signing import PayloadSigner
from .throttle import ExecutionPacer

__all__ = ["PipelineFailure", "ValidationAttempt", "GateResult", "ContentValidationPipeline"]

logger = logging.getLogger("ztgkt")

Generator = Callable[[str], Awaitable[str]]

RECALIBRATION_TEMPLATE = (
    "{prompt}\n[RECALIBRATION_FEEDBACK]: Prior output failed validation rules due to: "
    "{failures} Regulate generation format to meet precise syntax constraints."
)


class PipelineFailure(RuntimeError):
    """Raised when the attempt budget is exhausted without a clean generation.

    The archive raised a bare ``SystemError``. This subclasses ``RuntimeError``
    instead, so callers can catch the gate's own failure without also catching
    interpreter-level errors, and carries the per-attempt record for triage.
    """

    def __init__(self, message: str, attempts: Sequence["ValidationAttempt"]) -> None:
        super().__init__(message)
        self.attempts: List[ValidationAttempt] = list(attempts)


@dataclass
class ValidationAttempt:
    """One trip through the gate."""

    iteration: int
    content_hash: str
    passed: bool
    duplicate: bool
    failures: List[str] = field(default_factory=list)


@dataclass
class GateResult:
    """An accepted generation plus its attestation."""

    execution_status: str
    validation_parity: float
    retry_attempts: int
    latency_duration_ms: float
    payload_signature: str
    validated_content: str
    attempts: List[ValidationAttempt] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        """The archive's dict shape, for drop-in use by existing callers."""
        return {
            "execution_status": self.execution_status,
            "validation_parity": self.validation_parity,
            "retry_attempts": self.retry_attempts,
            "latency_duration_ms": self.latency_duration_ms,
            "payload_signature": self.payload_signature,
            "validated_content": self.validated_content,
        }

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]


class ContentValidationPipeline:
    """Zero-trust gate in front of a text generator.

    Args:
        execution_gateway: Async callable taking a prompt, returning text.
        config: Tunables. Defaults reproduce the archived behavior.
        guards: Override the guard chain. Defaults to
            :func:`ztgkt.filters.default_guards`.
        max_attempts: Convenience override for ``config.max_attempts``,
            accepted positionally for archive call-site compatibility.
    """

    def __init__(
        self,
        execution_gateway: Generator,
        config: Optional[GateConfig] = None,
        guards: Optional[Sequence[Guard]] = None,
        max_attempts: Optional[int] = None,
    ) -> None:
        self.config = config or GateConfig()
        if max_attempts is not None:
            self.config.max_attempts = max_attempts
        if self.config.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        self.gateway = execution_gateway
        self.max_attempts = self.config.max_attempts
        self.guards: List[Guard] = list(guards) if guards else default_guards(self.config.patterns)
        self.normalizer = TextNormalizer(self.config.patterns)
        self.pacer = ExecutionPacer(
            minimum_latency_ms=self.config.minimum_latency_ms,
            maximum_latency_ms=self.config.maximum_latency_ms,
            seconds_per_word=self.config.seconds_per_word,
            scaling_coefficient=self.config.scaling_coefficient,
        )
        self.signer = PayloadSigner(self.config.signing_key)

    @staticmethod
    def _content_hash(text: str) -> str:
        """Loop-detection digest.

        MD5 is used because the archive used it and because this is a sameness
        check on this process's own output, not an integrity control. The
        integrity control is the HMAC in :mod:`ztgkt.signing`.
        """
        return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()

    def _compute_signature(self, text: str) -> str:
        return self.signer.sign(text)

    async def execute(self, input_prompt: str) -> GateResult:
        active_prompt = input_prompt
        start_time = time.time()
        historical_hashes: Set[str] = set()
        attempts: List[ValidationAttempt] = []

        for iteration in range(1, self.max_attempts + 1):
            raw_response = await self.gateway(active_prompt)
            response = self.normalizer.process(raw_response) if self.config.normalize else raw_response

            failures = [g.failure_message for g in self.guards if not g.is_clean(response)]

            response_hash = self._content_hash(response)
            duplicate = self.config.detect_duplicates and response_hash in historical_hashes
            if duplicate:
                failures.append("Duplicate generational loop pattern registered.")

            attempt = ValidationAttempt(
                iteration=iteration,
                content_hash=response_hash,
                passed=not failures,
                duplicate=duplicate,
                failures=list(failures),
            )
            attempts.append(attempt)

            if not failures:
                delay = await self.pacer.pace(response)
                total_latency_ms = (time.time() - start_time) * 1000.0
                logger.info(
                    "ZTGKT accepted generation on attempt %d (paced %.3fs)", iteration, delay
                )
                return GateResult(
                    execution_status="SUCCESS",
                    validation_parity=1.0000,
                    retry_attempts=iteration,
                    latency_duration_ms=round(total_latency_ms, 2),
                    payload_signature=self._compute_signature(response),
                    validated_content=response,
                    attempts=attempts,
                )

            historical_hashes.add(response_hash)
            logger.debug("ZTGKT attempt %d rejected: %s", iteration, "; ".join(failures))
            active_prompt = RECALIBRATION_TEMPLATE.format(
                prompt=input_prompt, failures=", ".join(failures)
            )

        logger.error("ZTGKT exhausted %d attempts without consensus", self.max_attempts)
        raise PipelineFailure(
            "CRITICAL_PIPELINE_FAILURE: Maximum retry limits exhausted without validation consensus.",
            attempts,
        )
