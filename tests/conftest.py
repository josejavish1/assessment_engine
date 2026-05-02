import pytest


@pytest.fixture
def sample_payload():
    return {
        "tower_id": "T2",
        "tower_name": "Hybrid Compute & Platforms",
        "sections": {},
    }
