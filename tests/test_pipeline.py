import pytest

from ztgkt import ContentValidationPipeline, GateConfig, PipelineFailure

CLEAN = "Throughput fell 12 percent because the queue drained slowly."
KEY = b"unit-test-key"


def fast(**kw):
    return GateConfig(
        signing_key=KEY, minimum_latency_ms=0.0, maximum_latency_ms=0.0, **kw
    )


def scripted(*responses):
    """Generator returning each response in turn, recording the prompts it saw."""
    seq = list(responses)
    seen = []

    async def gen(prompt: str) -> str:
        seen.append(prompt)
        return seq[min(len(seen) - 1, len(seq) - 1)]

    gen.prompts = seen
    return gen


@pytest.mark.asyncio
async def test_clean_output_passes_on_first_attempt():
    gate = ContentValidationPipeline(scripted(CLEAN), fast())
    result = await gate.execute("Report throughput.")
    assert result.execution_status == "SUCCESS"
    assert result.retry_attempts == 1
    assert result.validated_content == CLEAN
    assert len(result.payload_signature) == 96


@pytest.mark.asyncio
async def test_result_still_supports_archive_dict_access():
    gate = ContentValidationPipeline(scripted(CLEAN), fast())
    result = await gate.execute("Report throughput.")
    assert result["validated_content"] == CLEAN
    assert set(result.as_dict()) == {
        "execution_status",
        "validation_parity",
        "retry_attempts",
        "latency_duration_ms",
        "payload_signature",
        "validated_content",
    }


@pytest.mark.asyncio
async def test_dirty_output_is_regenerated_then_accepted():
    gen = scripted("I think latency may have moved.", CLEAN)
    result = await ContentValidationPipeline(gen, fast()).execute("Report throughput.")
    assert result.retry_attempts == 2
    assert result.validated_content == CLEAN


@pytest.mark.asyncio
async def test_feedback_names_each_failed_guard():
    gen = scripted("I think it may have moved.", CLEAN)
    await ContentValidationPipeline(gen, fast()).execute("Report throughput.")
    retry_prompt = gen.prompts[1]
    assert "[RECALIBRATION_FEEDBACK]" in retry_prompt
    assert "First-person language signature registered." in retry_prompt
    assert "Qualifying or ambiguous statements registered." in retry_prompt
    assert "Missing explicit rationales or metrics." in retry_prompt
    assert retry_prompt.startswith("Report throughput.")


@pytest.mark.asyncio
async def test_feedback_is_rebuilt_from_the_original_prompt_not_stacked():
    gen = scripted("I saw it.", "We saw it.", CLEAN)
    await ContentValidationPipeline(gen, fast()).execute("Report throughput.")
    assert gen.prompts[2].count("[RECALIBRATION_FEEDBACK]") == 1


@pytest.mark.asyncio
async def test_repeated_identical_rejection_is_flagged_as_a_loop():
    gen = scripted("Throughput fell.")
    with pytest.raises(PipelineFailure) as excinfo:
        await ContentValidationPipeline(gen, fast(max_attempts=3)).execute("Report.")
    attempts = excinfo.value.attempts
    assert len(attempts) == 3
    assert attempts[0].duplicate is False
    assert attempts[1].duplicate is True
    assert "Duplicate generational loop pattern registered." in attempts[2].failures


@pytest.mark.asyncio
async def test_duplicate_detection_can_be_disabled():
    gen = scripted("Throughput fell.")
    with pytest.raises(PipelineFailure) as excinfo:
        await ContentValidationPipeline(
            gen, fast(max_attempts=2, detect_duplicates=False)
        ).execute("Report.")
    assert all(not a.duplicate for a in excinfo.value.attempts)


@pytest.mark.asyncio
async def test_budget_exhaustion_raises_with_the_archive_message():
    gen = scripted("I might know.", "We may know.", "They could know.")
    with pytest.raises(PipelineFailure, match="CRITICAL_PIPELINE_FAILURE"):
        await ContentValidationPipeline(gen, fast(max_attempts=3)).execute("Report.")


@pytest.mark.asyncio
async def test_normalization_applies_before_validation_and_signing():
    gen = scripted("Cache latency fell 9 percent because writes optimize the log.")
    result = await ContentValidationPipeline(gen, fast()).execute("Report.")
    assert "optimize" not in result.validated_content
    assert "writes use the log" in result.validated_content


@pytest.mark.asyncio
async def test_normalization_can_be_disabled():
    gen = scripted("Cache latency fell 9 percent because writes optimize the log.")
    result = await ContentValidationPipeline(gen, fast(normalize=False)).execute("Report.")
    assert "optimize" in result.validated_content


@pytest.mark.asyncio
async def test_signature_covers_the_returned_content():
    from ztgkt import PayloadSigner

    gate = ContentValidationPipeline(scripted(CLEAN), fast())
    result = await gate.execute("Report.")
    assert PayloadSigner(KEY).verify(result.validated_content, result.payload_signature)


def test_zero_attempt_budget_is_rejected():
    with pytest.raises(ValueError):
        GateConfig(max_attempts=0)
