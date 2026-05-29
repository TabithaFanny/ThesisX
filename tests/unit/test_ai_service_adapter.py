"""Tests for the web AI service adapter."""

from __future__ import annotations

import pytest

from thesisx_api.adapters.ai_service_adapter import AiServiceAdapter, AiServiceConfig


@pytest.mark.asyncio
async def test_mock_mode_without_config_returns_mock_response():
    adapter = AiServiceAdapter(
        AiServiceConfig(api_url="", api_key="", model=""),
        run_mode="mock",
    )

    result = await adapter.send_message([{"role": "user", "content": "hello"}])

    assert result.startswith("[Mock]")


@pytest.mark.asyncio
async def test_real_mode_without_config_raises_clear_error():
    adapter = AiServiceAdapter(
        AiServiceConfig(api_url="", api_key="", model=""),
        run_mode="real",
    )

    with pytest.raises(ValueError, match="Missing: api_url, api_key, model"):
        await adapter.send_message([{"role": "user", "content": "hello"}])


@pytest.mark.asyncio
async def test_mock_stream_without_config_yields_chunks():
    adapter = AiServiceAdapter(
        AiServiceConfig(api_url="", api_key="", model=""),
        run_mode="mock",
    )

    chunks = [chunk async for chunk in adapter.stream_response([{"role": "user", "content": "hello"}])]

    assert chunks
    assert "".join(chunks).startswith("[Mock]")
