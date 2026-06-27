# golden-path: ignore
from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from assessment_engine.mcp_server import mcp


def test_mcp_server_initialization() -> None:
    # 1. --- ARRANGE & ACT & ASSERT ---
    assert isinstance(mcp, FastMCP), "The mcp instance must be an instance of FastMCP."
    assert mcp.name == "Assessment Engine Core", "The FastMCP application name is incorrect."


@pytest.mark.asyncio
async def test_mcp_server_tools_registration() -> None:
    # 2. --- ARRANGE ---
    expected_tools = {
        "build_tower_payload",
        "render_tower_docx",
        "generate_radar_chart",
        "render_commercial_docx",
        "get_tower_state",
        "start_plan_generation",
        "check_plan_status",
        "start_plan_execution",
        "check_execution_status",
        "check_action_gate",
        "authorize_action_gate",
        "abort_and_revert",
    }

    # --- ACT ---
    registered_tools = await mcp.list_tools()
    registered_names = {t.name for t in registered_tools}

    # --- ASSERT ---
    for tool_name in expected_tools:
        assert tool_name in registered_names, f"Mandatory MCP tool '{tool_name}' is not registered on the server."


@pytest.mark.asyncio
async def test_mcp_get_tower_state_robustness() -> None:
    """Verify that get_tower_state handles invalid directories gracefully without crashing."""
    # 3. --- ARRANGE & ACT ---
    result_content, result_meta = await mcp.call_tool("get_tower_state", {"case_dir": "non_existent_mcp_test_path"})
    
    # --- ASSERT ---
    assert isinstance(result_content, list), "Expected TextContent list from MCP."
    assert len(result_content) > 0
    
    first_msg = result_content[0]
    assert first_msg.type == "text"
    assert "no encontrado" in first_msg.text or "Error:" in first_msg.text
