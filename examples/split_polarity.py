"""Show why ZTGKT had to be split: the same text, judged by both halves.

    python examples/split_polarity.py
"""

import asyncio
import logging

from ztgkt import ClinicalSignalValidator, ContentPolishPipeline, GateConfig

logging.getLogger("ztgkt").setLevel(logging.CRITICAL)

SIGNAL = "At 14:22 the patient SpO2 of 88 percent may indicate desaturation."


async def echo(prompt: str) -> str:
    return SIGNAL


async def main() -> None:
    print("signal:", SIGNAL)
    print()

    ok, failures = ClinicalSignalValidator().validate_signal(SIGNAL)
    print("domain validator  :", "ACCEPT" if ok else f"REJECT {failures}")
    print("  hedging is information here, and is preserved.")
    print()

    polish = ContentPolishPipeline(
        echo,
        GateConfig(
            signing_key=b"example-key",
            max_attempts=1,
            minimum_latency_ms=0.0,
            maximum_latency_ms=0.0,
        ),
    )
    try:
        await polish.execute("Restate the signal.")
        print("presentation gate : ACCEPT")
    except Exception as exc:  # PipelineFailure
        print("presentation gate : REJECT")
        for attempt in exc.attempts:
            for failure in attempt.failures:
                print("   -", failure)
    print()
    print("Same text. Opposite verdicts. One component could not hold both rules,")
    print("which is why the presentation path became optional and the domain path")
    print("became mandatory. See docs/LINEAGE.md.")


if __name__ == "__main__":
    asyncio.run(main())
