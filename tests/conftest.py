from __future__ import annotations

from typing import Any, Dict

import pytest


@pytest.fixture
def sample_payload() -> Dict[str, Any]:
    return {
        "tower_id": "T2",
        "tower_name": "Hybrid Compute & Platforms",
        "sections": {},
    }
