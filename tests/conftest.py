import pytest
from assessment_engine.scripts.lib.ai_client import _query_cache


@pytest.fixture(autouse=True)
def clear_ai_client_cache():
    """Fixture to clear the AI client cache before each test."""
    _query_cache.clear()


@pytest.fixture
def sample_payload():
    return {
        "tower_id": "T2",
        "tower_name": "Hybrid Compute & Platforms",
        "sections": {},
    }
