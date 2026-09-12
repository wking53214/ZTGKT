"""The "Kinetic Throttle" half: deliberate pacing of accepted output.

The pacer inserts a delay proportional to output length before an accepted
generation is released. The delay is clamped at both ends, so it is a pacing
governor rather than a rate limiter: it smooths burst release, it does not cap
throughput over a window.

Constants are preserved from the archive:

- ``minimum_latency_ms = 15.0`` floor
- ``scaling_coefficient = 0.815`` (the recurring "815" tag in this system family)
- ``0.002`` seconds per word
- ``0.200`` seconds ceiling

At the default coefficient the ceiling binds at roughly 123 words, so any
output longer than a short paragraph paces at the flat 200 ms cap.
"""

from __future__ import annotations

import asyncio

__all__ = ["ExecutionPacer"]


class ExecutionPacer:
    """Length-proportional release delay with a floor and a ceiling."""

    def __init__(
        self,
        minimum_latency_ms: float = 15.0,
        maximum_latency_ms: float = 200.0,
        seconds_per_word: float = 0.002,
        scaling_coefficient: float = 0.815,
    ) -> None:
        if minimum_latency_ms < 0 or maximum_latency_ms < 0:
            raise ValueError("Latency bounds must be non-negative.")
        if minimum_latency_ms > maximum_latency_ms:
            raise ValueError("minimum_latency_ms exceeds maximum_latency_ms.")
        self.minimum_latency_seconds: float = minimum_latency_ms / 1000.0
        self.maximum_latency_seconds: float = maximum_latency_ms / 1000.0
        self.seconds_per_word: float = seconds_per_word
        self.scaling_coefficient: float = scaling_coefficient

    async def calculate_delay(self, text_payload: str) -> float:
        """Delay in seconds for ``text_payload``, clamped to the configured band."""
        word_count = len(text_payload.split())
        calculated_delay = (word_count * self.seconds_per_word) * self.scaling_coefficient
        return max(
            self.minimum_latency_seconds,
            min(calculated_delay, self.maximum_latency_seconds),
        )

    @staticmethod
    async def enforce_pause(delay_duration: float) -> None:
        await asyncio.sleep(delay_duration)

    async def pace(self, text_payload: str) -> float:
        """Calculate and apply the delay. Returns the delay that was applied."""
        delay = await self.calculate_delay(text_payload)
        await self.enforce_pause(delay)
        return delay
