"""Run the gate against a stub generator that fails, then complies.

    python examples/basic_gate.py
"""

import asyncio

from ztgkt import ContentValidationPipeline, GateConfig, PipelineFailure

RESPONSES = [
    "I think the queue might be a bit slow.",          # pronoun + hedging + no anchor
    "The queue is slow.",                              # no anchor
    "Queue depth rose to 412 because the drain stalled.",  # clean
]


async def stub_generator(prompt: str) -> str:
    if "[RECALIBRATION_FEEDBACK]" in prompt:
        stub_generator.calls += 1
    return RESPONSES[min(stub_generator.calls, len(RESPONSES) - 1)]


stub_generator.calls = 0


async def main() -> None:
    gate = ContentValidationPipeline(
        stub_generator,
        GateConfig(signing_key=b"example-key-not-for-production", max_attempts=5),
    )

    try:
        result = await gate.execute("Report queue depth.")
    except PipelineFailure as exc:
        print("gate refused after", len(exc.attempts), "attempts")
        for attempt in exc.attempts:
            print(f"  {attempt.iteration}: {attempt.failures}")
        return

    print("accepted on attempt", result.retry_attempts)
    print("content   :", result.validated_content)
    print("signature :", result.payload_signature[:32], "...")
    print("latency   :", result.latency_duration_ms, "ms")
    print()
    print("attempt log:")
    for attempt in result.attempts:
        status = "PASS" if attempt.passed else "FAIL"
        print(f"  {attempt.iteration} {status} {attempt.failures}")


if __name__ == "__main__":
    asyncio.run(main())
