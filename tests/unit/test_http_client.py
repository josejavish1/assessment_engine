# golden-path: ignore
"""Unit Test Suite for SovereignHttpClient (Tier-1 SOTA Resilience)."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from assessment_engine.infrastructure.chassis.context import TraceContext, set_current_trace_context
from assessment_engine.infrastructure.http_client import (
    DEFAULT_TIMEOUT_SECONDS,
    MAX_ALLOWED_TIMEOUT_SECONDS,
    SovereignHttpClient,
    TimeoutBoundExceededError,
    http_client,
)


def test_default_timeout_initialization() -> None:
    client = SovereignHttpClient()
    assert client.default_timeout == DEFAULT_TIMEOUT_SECONDS


def test_exceeding_max_allowed_timeout_raises_error() -> None:
    with pytest.raises(TimeoutBoundExceededError):
        SovereignHttpClient(default_timeout=35.0)


def test_timeout_resolution_clamps_to_max() -> None:
    client = SovereignHttpClient(default_timeout=10.0)
    assert client._resolve_timeout(None) == 10.0
    assert client._resolve_timeout(5.0) == 5.0
    assert client._resolve_timeout(45.0) == MAX_ALLOWED_TIMEOUT_SECONDS
    assert client._resolve_timeout(0.01) == 0.1


def test_w3c_trace_context_injection() -> None:
    client = SovereignHttpClient()
    ctx = TraceContext.generate_new(sampled=True)
    token = set_current_trace_context(ctx)

    try:
        headers = client._inject_trace_headers({"X-Custom": "test"})
        assert "traceparent" in headers
        assert headers["traceparent"] == ctx.to_w3c_header()
        assert headers["X-Custom"] == "test"
    finally:
        set_current_trace_context(None)


def test_request_enforces_timeout_on_underlying_session() -> None:
    client = SovereignHttpClient(default_timeout=12.0)
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(client.session, "request", return_value=mock_response) as mock_req:
        resp = client.get("https://api.example.com/data")
        assert resp.status_code == 200
        mock_req.assert_called_once()
        _, kwargs = mock_req.call_args
        assert kwargs["timeout"] == 12.0
