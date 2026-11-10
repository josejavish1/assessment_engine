"""
Unit and integration test suite for Phase 2: Dual-Mode Ingestion Service.
Tests parsing and ingestion of:
1. Real context transcripts (.docx, .txt) -> evidence_vault.json & client_intelligence.json
2. Real assessment matrices (.xlsx, .txt) -> digital_twin_state.json
3. Multipart HTTP endpoints on the live FastAPI app.
"""

from io import BytesIO
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from assessment_engine.application.services.ingestion_service import (
    AssessmentMatrixParserService,
    DocumentIngestionService,
)
from assessment_engine.infrastructure.storage.workspace_manager import (
    WorkspacePersistenceManager,
)
from server import app

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def temp_workspace(tmp_path: Path) -> WorkspacePersistenceManager:
    return WorkspacePersistenceManager(root_dir=tmp_path / "working")


def test_real_molins_matrix_excel_parsing(temp_workspace: WorkspacePersistenceManager):
    """Test parsing the authentic client Excel matrix from source_docs/molins/."""
    excel_path = REPO_ROOT / "source_docs" / "molins" / "Preguntas Fast Assessment Molins contestadas cliente.xlsx"
    if not excel_path.is_file():
        pytest.skip(f"Test asset not present: {excel_path}")

    service = AssessmentMatrixParserService(temp_workspace)
    client_slug = "molins-test"

    twin = service.ingest_assessment_matrix(
        client_slug=client_slug,
        source_path=excel_path,
        source_filename=excel_path.name,
    )

    assert twin.client_slug == client_slug
    assert len(twin.towers) >= 5
    assert "T1" in twin.towers
    assert twin.towers["T1"].calibrated_maturity_score >= 1.0
    assert twin.overall_maturity_index >= 1.0
    assert twin.completion_percentage > 50.0

    # Verify physical file was written to disk
    persisted = temp_workspace.load_digital_twin_state(client_slug)
    assert persisted is not None
    assert persisted.overall_maturity_index == twin.overall_maturity_index


def test_real_molins_matrix_txt_parsing(temp_workspace: WorkspacePersistenceManager):
    """Test parsing the authentic client text response file from source_docs/molins/."""
    txt_path = REPO_ROOT / "source_docs" / "molins" / "261014 Respuestas Test Molins.txt"
    if not txt_path.is_file():
        pytest.skip(f"Test asset not present: {txt_path}")

    service = AssessmentMatrixParserService(temp_workspace)
    client_slug = "molins-txt-test"

    twin = service.ingest_assessment_matrix(
        client_slug=client_slug,
        source_path=txt_path,
        source_filename=txt_path.name,
    )

    assert twin.client_slug == client_slug
    assert "T1" in twin.towers
    assert "T2" in twin.towers
    assert len(twin.towers["T1"].question_responses) > 0


def test_real_molins_transcript_docx_parsing(temp_workspace: WorkspacePersistenceManager):
    """Test parsing the authentic context interview transcript from source_docs/molins/."""
    docx_path = REPO_ROOT / "source_docs" / "molins" / "260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx"
    if not docx_path.is_file():
        pytest.skip(f"Test asset not present: {docx_path}")

    service = DocumentIngestionService(temp_workspace)
    client_slug = "molins-transcript-test"

    vault = service.ingest_context_transcript(
        client_slug=client_slug,
        source_path=docx_path,
        source_filename=docx_path.name,
    )

    assert vault.client_slug == client_slug
    assert vault.total_fragments > 5
    assert len(vault.fragments) == vault.total_fragments
    assert any("T1" in f.mapped_domain_ids or "T2" in f.mapped_domain_ids for f in vault.fragments)

    # Verify physical file on disk
    persisted = temp_workspace.load_evidence_vault(client_slug)
    assert persisted is not None
    assert persisted.total_fragments == vault.total_fragments


def test_api_multipart_ingestion_endpoints():
    """Verify live HTTP endpoints for uploading context documents and assessment matrices."""
    client = TestClient(app)

    # 1. Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "cto@multipart-test.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client_slug = "multipart-test"

    # 2. Upload Context Document (.txt)
    mock_transcript = (
        "Enterprise Context Interview Session\n\n"
        "We operate a primary datacenter with UPS electrical redundancy and certified generators.\n\n"
        "Our compute tier is migrating to AWS EKS with multi-cloud failover.\n\n"
        "Storage is managed on NetApp arrays with disaster recovery RPO under 15 minutes."
    ).encode("utf-8")

    res_doc = client.post(
        f"/api/workspace/{client_slug}/ingest/context-document",
        files={"file": ("interview_transcript.txt", BytesIO(mock_transcript), "text/plain")},
        headers=headers,
    )
    assert res_doc.status_code == 200
    doc_data = res_doc.json()
    assert doc_data["status"] == "INGESTED"
    assert doc_data["total_fragments"] >= 3

    # 3. Upload Assessment Matrix (.txt)
    mock_matrix = (
        "T1.P1.K1.PR1    4.0\n"
        "T1.P1.K2.PR1    3.5\n"
        "T2.P1.K1.PR1    4.5\n"
        "T2.P1.K2.PR1    4.0\n"
    ).encode("utf-8")

    res_matrix = client.post(
        f"/api/workspace/{client_slug}/ingest/assessment-matrix",
        files={"file": ("responses.txt", BytesIO(mock_matrix), "text/plain")},
        headers=headers,
    )
    assert res_matrix.status_code == 200
    matrix_data = res_matrix.json()
    assert matrix_data["status"] == "INGESTED"
    assert matrix_data["towers_ingested"] >= 2
    assert "T1" in matrix_data["towers"]
    assert "T2" in matrix_data["towers"]

    # 4. Query live digital twin state from disk
    res_twin = client.get(f"/api/workspace/{client_slug}/digital-twin", headers=headers)
    assert res_twin.status_code == 200
    twin_data = res_twin.json()
    assert twin_data["client_slug"] == client_slug
    assert "T1" in twin_data["towers"]
