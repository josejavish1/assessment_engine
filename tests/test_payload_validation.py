import pytest
import json
from pathlib import Path
from pydantic import ValidationError

from assessment_engine.schemas.global_report import GlobalReportPayload
from assessment_engine.schemas.commercial import CommercialPayload

ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = ROOT / "working" / "smoke_ivirma"

def test_global_report_payload_schema():
    """Valida el esquema del Informe Global contra el payload real generado."""
    payload_file = SMOKE_DIR / "global_report_payload.json"
    if not payload_file.exists():
        pytest.skip("No global_report_payload.json found. Run smoke test first.")
        
    data = json.loads(payload_file.read_text(encoding="utf-8"))
    
    try:
        payload = GlobalReportPayload.model_validate(data)
        assert payload.meta.client == "smoke_ivirma"
        assert len(payload.tower_bottom_lines) > 0
    except ValidationError as e:
        pytest.fail(f"GlobalReportPayload validation failed: {e}")

def test_commercial_report_payload_schema():
    """Valida el esquema del Account Action Plan contra el payload real generado."""
    payload_file = SMOKE_DIR / "commercial_report_payload.json"
    if not payload_file.exists():
        pytest.skip("No commercial_report_payload.json found. Run smoke test first.")
        
    data = json.loads(payload_file.read_text(encoding="utf-8"))
    
    try:
        payload = CommercialPayload.model_validate(data)
        assert payload.meta.client == "smoke_ivirma"
        assert len(payload.opportunities_pipeline) > 0
        assert len(payload.proactive_proposals) > 0
    except ValidationError as e:
        pytest.fail(f"CommercialPayload validation failed: {e}")
