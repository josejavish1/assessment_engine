import pytest
from pydantic import ValidationError

from assessment_engine.schemas.commercial import CommercialPayload
from assessment_engine.schemas.global_report import GlobalReportPayload
from tests.artifact_helpers import ROOT, load_json, require_artifact

SMOKE_DIR = ROOT / "working" / "smoke_ivirma"


def test_global_report_payload_schema():
    """Valida el esquema del Informe Global contra el payload real generado."""
    payload_file = require_artifact(SMOKE_DIR / "global_report_payload.json")
    data = load_json(payload_file)

    try:
        payload = GlobalReportPayload.model_validate(data)
        assert payload.meta.client == "smoke_ivirma"
        assert len(payload.tower_bottom_lines) > 0
    except ValidationError as e:
        pytest.fail(f"GlobalReportPayload validation failed: {e}")


def test_commercial_report_payload_schema():
    """Valida el esquema del Account Action Plan contra el payload real generado."""
    payload_file = require_artifact(SMOKE_DIR / "commercial_report_payload.json")
    data = load_json(payload_file)

    try:
        payload = CommercialPayload.model_validate(data)
        assert payload.meta.client == "smoke_ivirma"
        assert len(payload.opportunities_pipeline) > 0
        assert len(payload.proactive_proposals) > 0
    except ValidationError as e:
        pytest.fail(f"CommercialPayload validation failed: {e}")
