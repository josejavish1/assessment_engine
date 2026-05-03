"""
MCP Server Contract Tests.

These tests validate that the responses of the MCP server tools
adhere to the Pydantic schemas defined in `assessment_engine.schemas.mcp_contracts`.
This ensures that any change in the response structure is a deliberate
decision and not an accidental breaking change for API consumers.
"""
from __future__ import annotations

import json

from assessment_engine.mcp_server import get_tower_state
from assessment_engine.schemas.mcp_contracts import GetTowerStateResponse
from tests.test_mcp_server import (
    _valid_annex_payload,
    _valid_blueprint_payload,
    _write_json,
)


def test_get_tower_state_response_adheres_to_contract(tmp_path):
    """
    Validates that the JSON response from get_tower_state
    successfully parses against the GetTowerStateResponse schema.
    """
    # Arrange: Create a realistic set of artifacts for a "complete" state
    _write_json(tmp_path / "blueprint_t5_payload.json", _valid_blueprint_payload())
    _write_json(
        tmp_path / "approved_annex_t5.template_payload.json",
        _valid_annex_payload(),
    )
    (tmp_path / "Blueprint_Transformacion_T5_client.docx").write_bytes(b"docx")
    (tmp_path / "annex_t5_client_final.docx").write_bytes(b"docx")

    # Arrange: Create some legacy artifacts as well
    _write_json(tmp_path / "approved_asis.generated.json", {"status": "approved"})

    # Act: Call the tool and get the JSON response
    response_json_str = get_tower_state(str(tmp_path))
    response_data = json.loads(response_json_str)

    # Assert: The response data can be validated by the Pydantic model
    # An exception will be raised if validation fails.
    validated_response = GetTowerStateResponse.model_validate(response_data)

    # Assert: Spot check a few key fields to ensure data was parsed correctly
    assert validated_response.canonical.overall_status == "complete"
    assert validated_response.canonical.blueprint_payload.status == "valid"
    assert validated_response.canonical.annex_payload.status == "valid"
    assert (
        validated_response.canonical.deliverables["blueprint_docx"].status == "present"
    )
    assert validated_response.legacy.asis.status == "approved"
    assert validated_response.asis.status == "approved"
    assert validated_response.risks.status == "missing"


def test_start_and_check_plan_generation_adheres_to_contract():
    """
    Validates the contracts for the async plan generation tools.
    """
    import asyncio
    import time
    from assessment_engine.mcp_server import (
        start_plan_generation,
        check_plan_status,
        job_status
    )
    from assessment_engine.schemas.mcp_contracts import (
        StartPlanGenerationResponse,
        CheckPlanStatusResponse,
    )

    # Act: Start the generation
    start_response_str = asyncio.run(start_plan_generation("test request"))
    start_response_data = json.loads(start_response_str)

    # Assert: Validate the "start" response
    validated_start_response = StartPlanGenerationResponse.model_validate(
        start_response_data
    )
    job_id = validated_start_response.job_id
    assert validated_start_response.status == "started"

    # Act: Check status while running
    check_running_str = check_plan_status(job_id)
    check_running_data = json.loads(check_running_str)

    # Assert: Validate the "running" status response
    validated_running_response = CheckPlanStatusResponse.model_validate(
        check_running_data
    )
    assert validated_running_response.status == "running"

    # Await completion
    # In a real test we might mock the background task,
    # here we'll just wait for it to finish.
    # We add a hard-coded time limit to avoid an infinite loop.
    timeout = 30  # seconds
    start_time = time.time()
    while job_status.get(job_id) == "running":
        time.sleep(0.1)
        if time.time() - start_time > timeout:
            raise TimeoutError("Plan generation took too long.")

    # Act: Check status when completed
    check_completed_str = check_plan_status(job_id)
    check_completed_data = json.loads(check_completed_str)

    # Assert: Validate the "completed" status response
    validated_completed_response = CheckPlanStatusResponse.model_validate(
        check_completed_data
    )
    assert validated_completed_response.status in ["completed", "error"]
    assert validated_completed_response.result is not None
