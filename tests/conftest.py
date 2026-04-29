import sys
from pathlib import Path

# Añadimos 'src' al path para que los tests encuentren el paquete 'assessment_engine'
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir / "src"))

import pytest

@pytest.fixture
def sample_payload():
    return {
        "tower_id": "T2",
        "tower_name": "Hybrid Compute & Platforms",
        "sections": {}
    }
