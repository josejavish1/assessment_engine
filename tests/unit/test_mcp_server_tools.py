"""Top-Tier-1 unit test suite for FastMCP Server tools and artifact inspectors."""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel, Field, ValidationError

import assessment_engine.mcp_server as mcp_mod
from assessment_engine.domain.schemas.annex_synthesis import AnnexPayload
from assessment_engine.domain.schemas.blueprint import BlueprintPayload

# --- HELPER & INSPECTOR TESTS ---

def test_read_json_file(tmp_path: Path):
    """Verify _read_json_file correctly handles UTF-8 BOM and standard JSON."""
    file = tmp_path / "data.json"
    file.write_text('{"greeting": "hola"}', encoding="utf-8-sig")
    res = mcp_mod._read_json_file(file)
    assert res == {"greeting": "hola"}


def test_summarize_validation_error():
    """Verify _summarize_validation_error extracts hierarchical error locations."""
    class DummyModel(BaseModel):
        name: str
        count: int = Field(gt=0)

    try:
        DummyModel.model_validate({"name": 123, "count": -5})
    except ValidationError as err:
        summary = mcp_mod._summarize_validation_error(err)
        assert len(summary) >= 1
        assert any("count" in s for s in summary)


def test_inspect_payload_artifact_missing_and_corrupt(tmp_path: Path):
    """Verify _inspect_payload_artifact reports missing, load error, and invalid schema."""
    # 1. Missing
    missing_path = tmp_path / "nonexistent.json"
    state = mcp_mod._inspect_payload_artifact(missing_path, BlueprintPayload, "Blueprint")
    assert state["status"] == "missing"

    # 2. Corrupt JSON
    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("{invalid_json", encoding="utf-8")
    state = mcp_mod._inspect_payload_artifact(corrupt_path, BlueprintPayload, "Blueprint")
    assert state["status"] == "error"
    assert "could not be loaded" in state["message"]

    # 3. Invalid schema
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps({"invalid_key": "val"}), encoding="utf-8")
    state = mcp_mod._inspect_payload_artifact(invalid_path, BlueprintPayload, "Blueprint")
    assert state["status"] == "invalid"
    assert "validation_errors" in state


def test_inspect_payload_artifact_valid_blueprint_and_annex():
    """Verify _inspect_payload_artifact reports valid status for both blueprint and annex schemas."""
    bp_fixture = Path("tests/test_data/blueprint_t2_payload.json")
    assert bp_fixture.exists()

    bp_state = mcp_mod._inspect_payload_artifact(bp_fixture, BlueprintPayload, "Blueprint")
    assert bp_state["status"] == "valid"
    assert bp_state["tower_code"] == "T2"

    annex_fixture = Path("tests/test_data/approved_annex_t2.template_payload.json")
    assert annex_fixture.exists()

    annex_state = mcp_mod._inspect_payload_artifact(annex_fixture, AnnexPayload, "Annex")
    assert annex_state["status"] == "valid"
    assert annex_state["tower_code"] == "T2"


def test_inspect_docx_artifact(tmp_path: Path):
    """Verify _inspect_docx_artifact identifies existing and missing DOCX patterns."""
    # Missing
    res = mcp_mod._inspect_docx_artifact("*.docx", tmp_path)
    assert res["status"] == "missing"

    # Present
    doc_file = tmp_path / "Blueprint_Transformacion_T1.docx"
    doc_file.write_bytes(b"dummy docx content")
    res = mcp_mod._inspect_docx_artifact("Blueprint_Transformacion_*.docx", tmp_path)
    assert res["status"] == "present"
    assert str(doc_file) in res["path"]


def test_canonical_overall_status_matrix():
    """Verify status calculation across permutations of valid, invalid, and missing."""
    assert mcp_mod._canonical_overall_status({
        "blueprint_payload": {"status": "valid"},
        "annex_payload": {"status": "valid"},
    }) == "complete"

    assert mcp_mod._canonical_overall_status({
        "blueprint_payload": {"status": "invalid"},
        "annex_payload": {"status": "valid"},
    }) == "invalid"

    assert mcp_mod._canonical_overall_status({
        "blueprint_payload": {"status": "valid"},
        "annex_payload": {"status": "missing"},
    }) == "partial"

    assert mcp_mod._canonical_overall_status({
        "blueprint_payload": {"status": "missing"},
        "annex_payload": {"status": "missing"},
    }) == "missing"


def test_inspect_legacy_state(tmp_path: Path):
    """Verify _inspect_legacy_state handles missing, corrupt, and present legacy section outputs."""
    case_dir = tmp_path / "legacy_case"
    case_dir.mkdir()

    # 1. Corrupt asis
    (case_dir / "approved_asis.generated.json").write_text("{bad", encoding="utf-8")

    # 2. Present risks
    (case_dir / "approved_risks.generated.json").write_text(
        json.dumps({"status": "approved", "_approval_metadata": {"reviewer": "SecLead"}}),
        encoding="utf-8",
    )

    state = mcp_mod._inspect_legacy_state(case_dir)
    assert state["asis"]["status"] == "error"
    assert state["risks"]["status"] == "approved"
    assert state["gap"]["status"] == "missing"


def test_run_script_success_and_failure():
    """Verify _run_script executes subprocess and captures combined output or raises RuntimeError."""
    with patch("subprocess.run") as mock_sub:
        # Success
        mock_sub.return_value = subprocess.CompletedProcess(
            args=["python"], returncode=0, stdout="Success output", stderr=""
        )
        out = mcp_mod._run_script("dummy.module", ["--flag"])
        assert "Success output" in out

        # Failure
        mock_sub.return_value = subprocess.CompletedProcess(
            args=["python"], returncode=1, stdout="", stderr="Fatal trace"
        )
        with pytest.raises(RuntimeError) as exc_info:
            mcp_mod._run_script("dummy.module", ["--flag"])
        assert "Fatal trace" in str(exc_info.value)


# --- MCP TOOL WRAPPER TESTS ---

def test_build_tower_payload_tool():
    """Verify build_tower_payload MCP tool formats output."""
    with patch("assessment_engine.mcp_server._run_script", return_value="Synthesizer output OK") as mock_run:
        res = mcp_mod.build_tower_payload("input.json", "output.json", "Client Acme", "short")
        assert "Payload construido con éxito" in res
        assert "Synthesizer output OK" in res
        mock_run.assert_called_once_with(
            "assessment_engine.application.run_executive_annex_synthesizer",
            ["input.json", "output.json", "Client Acme", "short"],
        )


def test_render_tower_docx_tool():
    """Verify render_tower_docx MCP tool delegates to renderer."""
    with patch("assessment_engine.mcp_server._run_script", return_value="Rendered OK"):
        res = mcp_mod.render_tower_docx("payload.json", "template.docx", "out.docx")
        assert "Documento de Torre renderizado con éxito" in res


def test_generate_radar_chart_tool():
    """Verify generate_radar_chart MCP tool calls chart generator."""
    with patch("assessment_engine.mcp_server._run_script", return_value="Chart OK"):
        res = mcp_mod.generate_radar_chart("payload.json")
        assert "Gráfico generado con éxito" in res


def test_render_commercial_docx_tool():
    """Verify render_commercial_docx MCP tool delegates to commercial reporter."""
    with patch("assessment_engine.mcp_server._run_script", return_value="Commercial OK"):
        res = mcp_mod.render_commercial_docx("payload.json", "template.docx", "out.docx")
        assert "Reporte comercial renderizado" in res


def test_get_tower_state_nonexistent_and_valid(tmp_path: Path):
    """Verify get_tower_state returns error on missing directory and JSON for valid."""
    # 1. Nonexistent
    err_res = mcp_mod.get_tower_state(str(tmp_path / "ghost_dir"))
    assert "no encontrado" in err_res

    # 2. Valid empty directory
    valid_dir = tmp_path / "valid_tower"
    valid_dir.mkdir()
    res_str = mcp_mod.get_tower_state(str(valid_dir))
    data = json.loads(res_str)
    assert "canonical" in data
    assert "legacy" in data
    assert data["canonical"]["mode"] == "blueprint-first"


@pytest.mark.asyncio
async def test_start_and_check_plan_generation_flow(tmp_path: Path):
    """Verify async plan generation dispatch and status polling."""
    plan_dir = tmp_path / "generated_plan"
    plan_dir.mkdir()
    (plan_dir / "plan.json").write_text(json.dumps({"title": "Strategic Plan"}), encoding="utf-8")

    orchestrator_log = f'{{"message": "Plan generado en {plan_dir}"}}\n'

    with patch("assessment_engine.mcp_server._run_script", return_value=orchestrator_log):
        start_res = await mcp_mod.start_plan_generation("Generar plan para Banco Santander")
        start_data = json.loads(start_res)
        job_id = start_data["job_id"]
        assert start_data["status"] == "started"

        # Give async task a small moment to execute background executor
        await asyncio.sleep(0.05)

        status_res = mcp_mod.check_plan_status(job_id)
        status_data = json.loads(status_res)
        assert status_data["status"] in ("completed", "running")
        if status_data["status"] == "completed":
            assert "Strategic Plan" in status_data["result"]


@pytest.mark.asyncio
async def test_start_and_check_plan_execution_flow(tmp_path: Path):
    """Verify async execution lifecycle with mocked asyncio subprocess."""
    mock_process = AsyncMock()
    mock_process.stdout.readline.side_effect = [
        b"Step 1: Ingesting\n",
        b"Step 2: Synthesizing\n",
        b"",
    ]
    mock_process.wait.return_value = None
    mock_process.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        res = await mcp_mod.start_plan_execution(str(tmp_path), alt_index=0)
        data = json.loads(res)
        job_id = data["job_id"]
        assert data["status"] == "started"

        await asyncio.sleep(0.05)

        status_res = mcp_mod.check_execution_status(job_id)
        status_data = json.loads(status_res)
        assert status_data["status"] in ("completed", "running")
        assert "Step 1" in status_data["result"]


def test_check_action_gate_scenarios(tmp_path: Path):
    """Verify check_action_gate correctly identifies active, absent, and corrupt gates."""
    # 1. Absent
    res = json.loads(mcp_mod.check_action_gate(str(tmp_path)))
    assert res["action_gate_active"] is False

    # 2. Corrupt
    gate_file = tmp_path / "reconciliation_summary.json"
    gate_file.write_text("{malformed", encoding="utf-8")
    res = json.loads(mcp_mod.check_action_gate(str(tmp_path)))
    assert res["action_gate_active"] is False
    assert "error" in res

    # 3. Active
    gate_file.write_text(json.dumps({"diagnosis": {"blast_radius": ["file.py"]}}), encoding="utf-8")
    res = json.loads(mcp_mod.check_action_gate(str(tmp_path)))
    assert res["action_gate_active"] is True
    assert res["data"]["diagnosis"]["blast_radius"] == ["file.py"]


def test_authorize_action_gate_flow(tmp_path: Path):
    """Verify authorize_action_gate patches plan.json, creates feedback, and unlinks summary."""
    # 1. No active gate
    res_no = json.loads(mcp_mod.authorize_action_gate(str(tmp_path)))
    assert res_no["success"] is False
    assert "No hay Action Gate activo" in res_no["message"]

    # 2. Active gate with alternatives
    summary_data = {
        "task_id": "TASK-001",
        "raw_error": "Violation of naming convention",
        "diagnosis": {
            "blast_radius": ["src/module.py"],
            "required_invariant_breach": "STRICT_NAMING",
            "proposed_cure": "Apply camelCase conversion",
        },
    }
    (tmp_path / "reconciliation_summary.json").write_text(json.dumps(summary_data), encoding="utf-8")

    plan_data = {
        "alternatives": [
            {
                "in_scope": ["src/other.py"],
                "invariants": ["STRICT_NAMING", "NO_RAW_SQL"],
            }
        ]
    }
    (tmp_path / "plan.json").write_text(json.dumps(plan_data), encoding="utf-8")

    res_auth = json.loads(mcp_mod.authorize_action_gate(str(tmp_path), alt_index=0))
    assert res_auth["success"] is True

    # Verify reconciliation_summary was unlinked
    assert not (tmp_path / "reconciliation_summary.json").exists()

    # Verify authorized_feedback was written
    fb = json.loads((tmp_path / "authorized_feedback.json").read_text(encoding="utf-8"))
    assert fb["task_id"] == "TASK-001"
    assert "CURA AUTORIZADA" in fb["feedback"]

    # Verify plan.json patched
    patched_plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    active = patched_plan["alternatives"][0]
    assert "src/module.py" in active["in_scope"]
    assert any("EXCEPTION AUTHORIZED" in inv for inv in active["invariants"])


def test_abort_and_revert_tool():
    """Verify abort_and_revert executes git reset and clean safely."""
    with patch("subprocess.run") as mock_sub:
        mock_sub.return_value = subprocess.CompletedProcess(args=["git"], returncode=0)
        res = json.loads(mcp_mod.abort_and_revert())
        assert res["success"] is True
        assert "git reset --hard" in res["message"]

        # Failure path
        mock_sub.side_effect = subprocess.CalledProcessError(1, ["git", "clean"])
        res_fail = json.loads(mcp_mod.abort_and_revert())
        assert res_fail["success"] is False
        assert "Error al revertir" in res_fail["message"]
