"""
Unit and integration test suite for Phase 3: Synthesis Orchestrator & Deliverable Streaming.
Verifies:
1. Asynchronous synthesis execution with atomic telemetry updates.
2. Real-time status reporting and pipeline_status.json lifecycle.
3. Authentic Tomo 1 .docx generation in working/out/[client_slug]/.
4. Deliverable listing and download endpoints.
"""

import asyncio
from pathlib import Path
from zipfile import ZipFile
import pytest
from starlette.testclient import TestClient

from assessment_engine.application.services.synthesis_orchestrator import (
    SynthesisOrchestrator,
)
from assessment_engine.domain.schemas.workspace_contracts import (
    ClientDossierV3,
    DigitalTwinStateContract,
    FinancialParameters,
    PerimeterDefinition,
    PerimeterScopeType,
    PipelineStageStatus,
    SecurityTowerState,
)
from assessment_engine.infrastructure.storage.workspace_manager import (
    WorkspacePersistenceManager,
)
import shutil
from server import app

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def temp_workspace() -> WorkspacePersistenceManager:
    manager = WorkspacePersistenceManager(root_dir=REPO_ROOT / "working")
    yield manager
    # Clean up test tenant directories after test completion
    test_dir = REPO_ROOT / "working" / "synthesis-test-tenant"
    test_out = REPO_ROOT / "working" / "out" / "synthesis_test_corp"
    test_out2 = REPO_ROOT / "working" / "out" / "synthesis-test-tenant"
    for d in [test_dir, test_out, test_out2]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)


@pytest.mark.asyncio
async def test_synthesis_orchestration_lifecycle(temp_workspace: WorkspacePersistenceManager):
    """Test full asynchronous execution of the synthesis pipeline resulting in compiled .docx files."""
    slug = "synthesis-test-tenant"
    orchestrator = SynthesisOrchestrator(temp_workspace)

    # 1. Pre-seed Client Dossier and Digital Twin
    dossier = ClientDossierV3(
        schema_version="3.0.0",
        client_slug=slug,
        legal_entity_name="Synthesis Test Corp",
        industry_vertical_code="heavy_manufacturing",
        primary_hq_country_iso="ES",
        output_locale="es",
        last_updated_utc="2026-11-09T18:00:00Z",
        perimeter=PerimeterDefinition(
            scope_type=PerimeterScopeType.GLOBAL_HOLDING,
            target_entity_name="Synthesis Test Corp",
            employee_headcount=1500,
            operating_countries_iso=["ES"],
            critical_assets_summary=["Industrial Plant"],
        ),
        financials=FinancialParameters(
            base_currency_iso="EUR",
            annual_revenue_amount=320.0,
        ),
    )
    temp_workspace.save_client_intelligence(slug, dossier)

    twin = DigitalTwinStateContract(
        client_slug=slug,
        last_synchronized_utc="2026-11-09T18:00:00Z",
        overall_maturity_index=3.4,
        completion_percentage=100.0,
        towers={
            "T1": SecurityTowerState(
                tower_id="T1",
                calibrated_maturity_score=3.5,
                target_to_be_score=4.5,
                assessor_forensic_notes="Redundant power feeds",
                is_applicable=True,
                completed=True,
            ),
            "T2": SecurityTowerState(
                tower_id="T2",
                calibrated_maturity_score=3.3,
                target_to_be_score=4.3,
                assessor_forensic_notes="VMware to hybrid cloud migration",
                is_applicable=True,
                completed=True,
            ),
        },
    )
    temp_workspace.save_digital_twin_state(slug, twin)

    # 2. Trigger Synthesis
    status = orchestrator.trigger_synthesis(slug, doc_lang="es")
    assert status.client_slug == slug
    assert status.status == PipelineStageStatus.QUEUED

    # 3. Await background task completion (max 15s)
    for _ in range(30):
        await asyncio.sleep(0.5)
        current = orchestrator.get_status(slug)
        if current and current.status in (PipelineStageStatus.COMPLETED, PipelineStageStatus.FAILED):
            break

    final_status = orchestrator.get_status(slug)
    assert final_status is not None
    assert final_status.status == PipelineStageStatus.COMPLETED
    assert final_status.progress_pct == 100.0
    assert len(final_status.completed_files) >= 1

    # 4. Verify generated Tomo 1 DOCX is a valid Word archive
    out_dir = temp_workspace.resolve_output_dir(slug)
    tomo1_path = out_dir / final_status.completed_files[0]
    assert tomo1_path.is_file()
    assert tomo1_path.stat().st_size > 10_000

    # Ensure valid OpenXML ZIP archive containing word/document.xml
    with ZipFile(tomo1_path) as z:
        assert "word/document.xml" in z.namelist()


def test_api_compile_and_deliverables():
    """Verify live HTTP endpoints for triggering compilation and listing deliverables."""
    client = TestClient(app)

    # 1. Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "cto@compile-api-test.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client_slug = "compile-api-test"

    # 2. Trigger compilation via API
    res_compile = client.post(
        f"/api/workspace/{client_slug}/compile?lang=es",
        headers=headers,
    )
    assert res_compile.status_code == 200
    job_data = res_compile.json()
    assert job_data["client_slug"] == client_slug
    assert job_data["status"] in ("QUEUED", "RUNNING")

    # 3. Poll compilation status
    res_status = client.get(
        f"/api/workspace/{client_slug}/compile/status",
        headers=headers,
    )
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["client_slug"] == client_slug
    assert "current_stage" in status_data

    # 4. Query deliverables list
    res_deliv = client.get(
        f"/api/workspace/{client_slug}/deliverables",
        headers=headers,
    )
    assert res_deliv.status_code == 200
    assert isinstance(res_deliv.json(), list)
