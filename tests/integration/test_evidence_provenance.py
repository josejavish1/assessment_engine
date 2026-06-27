# golden-path: ignore
from __future__ import annotations

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from assessment_engine.domain.schemas.evidence import EvidenceFragment
from assessment_engine.infrastructure import ai_client


def test_evidence_fragment_content_addressable_hashing():
    source_uri = "source_docs/reference_reports/anexos_as_is/anexo_a_cpd_v1.2.pdf"
    content = "El Centro de Datos principal cuenta con dos acometidas de energía independientes."

    # 1. Instantiate with bare minimum fields (content and source_uri only)
    frag1 = EvidenceFragment(source_uri=source_uri, content=content)

    # Calculate expected hashes
    expected_content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    expected_fragment_id = hashlib.sha256(
        f"{source_uri}|{content}".encode("utf-8")
    ).hexdigest()

    # Assert that hashes are populated automatically and match expectations
    assert frag1.content_hash == expected_content_hash
    assert frag1.fragment_id == expected_fragment_id

    # 2. Assert that identical content produces the exact same ID (Deduplication)
    frag2 = EvidenceFragment(source_uri=source_uri, content=content)
    assert frag1.fragment_id == frag2.fragment_id
    assert frag1.content_hash == frag2.content_hash

    # 3. Assert that different content produces a completely different ID (Collision-free)
    different_content = (
        "El sistema de aire acondicionado del CPD secundario se encuentra obsoleto."
    )
    frag3 = EvidenceFragment(source_uri=source_uri, content=different_content)
    assert frag3.fragment_id != frag1.fragment_id
    assert frag3.content_hash != frag1.content_hash


@pytest.mark.asyncio
async def test_ai_client_network_resilience_retry():
    # Setup mock AdkApp and stream query
    mock_app = MagicMock()

    # We will simulate the model succeeding on the 4th attempt after 3 consecutive failures (like HTTP 429 Rate Limits)
    call_count = 0

    class MockAsyncIterator:
        def __init__(self, items):
            self.items = items
            self.index = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            nonlocal call_count
            if call_count < 3:
                call_count += 1
                raise RuntimeError(
                    "HTTP Error 429: Too Many Requests / Rate Limit Exceeded"
                )

            if self.index >= len(self.items):
                raise StopAsyncIteration
            item = self.items[self.index]
            self.index += 1
            call_count += 1
            return item

    # Valid event payload representing the successful response on the 4th run
    successful_events = [
        {"content": {"parts": [{"text": "Technical Compliance Audit Complete"}]}}
    ]

    def mock_query(user_id, message):
        return MockAsyncIterator(successful_events)

    mock_app.async_stream_query = mock_query

    # Temporarily patch wait to speed up the test execution so tenacity doesn't delay
    with patch("tenacity.wait_exponential.__call__", return_value=0.01):
        result_text, lines = await ai_client._execute_query_with_retry(
            app=mock_app,
            user_id="user_test",
            message="Run compliance audit",
        )

        # Assertions
        assert result_text == "Technical Compliance Audit Complete"
        assert len(lines) == 1
        # The function must have run 4 times (3 failures, 1 success)
        assert call_count == 4


@pytest.mark.asyncio
async def test_evidence_snapshotter_download_resilience(tmp_path: Path):
    """Verify that EvidenceSnapshotter handles network errors and corrupted downloads gracefully.
    
    This is a Google Practice standard test case that asserts our system rejects
    evidence URLs that fail to download, return non-200 HTTP statuses, or time out,
    preventing corrupted data from contaminating the downstream RAGE pipelines.
    """
    from assessment_engine.infrastructure.evidence_governance import EvidenceSnapshotter
    import httpx
    
    # 1. --- ARRANGE ---
    snapshotter = EvidenceSnapshotter(tmp_path)
    
    # Mock httpx.AsyncClient.get to raise a network connection error
    async def mock_client_get_error(*args, **kwargs):
        raise httpx.ConnectError("Connection refused by target server")
        
    with patch("httpx.AsyncClient.get", side_effect=mock_client_get_error):
        # 2. --- ACT ---
        # Capture a snapshot of a binary PDF URL that fails to download
        binary_url = "https://example.com/missing_ens_report.pdf"
        result = await snapshotter.capture_snapshot(binary_url)
        
        # 3. --- ASSERT ---
        # The result must be None (failed capture as both binary download and playwright fallbacks failed)
        assert result is None
        
        # Verify that process_urls properly discards this broken URL under its governance rules
        text_with_broken_link = f"Read the report here: {binary_url}"
        claims = await snapshotter.process_urls(text_with_broken_link)
        assert len(claims) == 0, "Broken URLs must be filtered out and discarded under governance rules."


@pytest.mark.asyncio
async def test_evidence_snapshotter_empty_and_corrupt_pdf_validation(tmp_path: Path):
    """Verify that EvidenceSnapshotter throws ValueError / returns None when getting empty files or files without %PDF- magic bytes."""
    from assessment_engine.infrastructure.evidence_governance import EvidenceSnapshotter
    import httpx
    
    # 1. --- ARRANGE ---
    snapshotter = EvidenceSnapshotter(tmp_path)
    
    # --- ACT & ASSERT ---
    # Case A: Server returns HTTP 200 but content is empty (0 bytes)
    mock_empty_resp = httpx.Response(200, content=b"")
    with patch("httpx.AsyncClient.get", return_value=mock_empty_resp):
        result_empty = await snapshotter.capture_snapshot("https://example.com/empty_report.pdf")
        assert result_empty is None, "Empty downloads must be rejected and return None."
        
    # Case B: Server returns HTTP 200 but content is HTML camouflaged as a PDF (missing PDF signature)
    mock_corrupt_resp = httpx.Response(200, content=b"<html>This is disguised HTML, not a PDF document!</html>")
    with patch("httpx.AsyncClient.get", return_value=mock_corrupt_resp):
        result_corrupt = await snapshotter.capture_snapshot("https://example.com/disguised_report.pdf")
        assert result_corrupt is None, "Corrupted/disguised PDFs must be rejected and return None."
