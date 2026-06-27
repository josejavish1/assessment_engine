from __future__ import annotations

import socket
from typing import Any, Dict
import pytest


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch):
    """Disable all external network connections during tests to ensure complete hermeticity."""
    original_connect = socket.socket.connect
    
    def mocked_connect(self, address):
        host = address[0]
        # Allow localhost / loopback for local service mock/mem bindings
        if host in ("127.0.0.1", "localhost", "::1"):
            try:
                return original_connect(self, address)
            except Exception:
                pass
        raise RuntimeError(
            f"❌ [SECURITY BLOCK] External network connection attempt blocked to host: {host}. "
            f"All integration and unit tests must be 100% hermetic (using VCR/Semantic cassettes or local mocks)."
        )
        
    monkeypatch.setattr(socket.socket, "connect", mocked_connect)


@pytest.fixture
def sample_payload() -> Dict[str, Any]:
    return {
        "tower_id": "T2",
        "tower_name": "Hybrid Compute & Platforms",
        "sections": {},
    }
