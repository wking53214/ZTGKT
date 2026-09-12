import pytest

from ztgkt import ExecutionPacer


@pytest.mark.asyncio
async def test_short_text_hits_the_floor():
    pacer = ExecutionPacer()
    assert await pacer.calculate_delay("one two") == pytest.approx(0.015)


@pytest.mark.asyncio
async def test_long_text_hits_the_ceiling():
    pacer = ExecutionPacer()
    assert await pacer.calculate_delay("word " * 5000) == pytest.approx(0.200)


@pytest.mark.asyncio
async def test_midband_scales_with_word_count():
    pacer = ExecutionPacer()
    fifty = await pacer.calculate_delay("word " * 50)
    hundred = await pacer.calculate_delay("word " * 100)
    assert fifty == pytest.approx(50 * 0.002 * 0.815)
    assert hundred > fifty


@pytest.mark.asyncio
async def test_pace_returns_the_delay_it_applied():
    pacer = ExecutionPacer(minimum_latency_ms=0.0, maximum_latency_ms=1.0)
    assert await pacer.pace("word " * 500) == pytest.approx(0.001)


def test_inverted_bounds_are_rejected():
    with pytest.raises(ValueError):
        ExecutionPacer(minimum_latency_ms=500.0, maximum_latency_ms=200.0)
