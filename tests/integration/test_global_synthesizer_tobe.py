# golden-path: ignore
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from assessment_engine.application.run_global_synthesizer_tobe import (
    HighLevelRoadmap,
    Phase1Strategy,
    Phase2ResilienceStrategy,
    Phase3Benefits,
    Phase4RisksAndAssumptions,
    SynthesisAudit,
    synthesize_global_tobe,
)


@pytest.mark.asyncio
async def test_synthesize_global_tobe_with_self_healing(tmp_path: Path):
    """Verify that synthesize_global_tobe runs, handles a rejected audit, and auto-corrects.

    This is a Red Team approved Trap & Recover test that asserts the self-healing
    reflection loop executes successfully when the verifier initially rejects the draft.
    """
    # 1. Arrange - Setup sandbox with a dummy tower payload
    working_dir = tmp_path / "working"
    tower_dir = working_dir / "T1"
    tower_dir.mkdir(parents=True)
    
    tower_payload = {
        "document_meta": {
            "client_name": "Test Client",
            "tower_name": "Core Infrastructure"
        },
        "pillars_analysis": [
            {
                "pilar_name": "Computing",
                "target_architecture_tobe": {
                    "vision_3_years": "Sovereign Edge",
                    "vision_5_years": "Active-Active"
                }
            }
        ]
    }
    
    payload_file = tower_dir / "blueprint_t1_payload.json"
    payload_file.write_text(json.dumps(tower_payload), encoding="utf-8")
    
    # Track calls to the verifier to simulate initial rejection and subsequent approval
    verifier_call_count = 0

    async def mock_run_agent_impl(app, user_id, message, schema=None, **kwargs):
        nonlocal verifier_call_count
        
        if schema == Phase1Strategy:
            return {
                "executive_vision": "Sovereign cloud vision.",
                "transformation_strategy": "Migrating key workloads.",
                "document_purpose": "Guide next-gen security.",
                "document_scope": "Full platform coverage.",
                "maturity_approach": "C-Level alignment."
            }
        elif schema == Phase2ResilienceStrategy:
            return {
                "cpd_strategy_3_years": "3 years of edge CPD.",
                "cpd_strategy_5_years": "5 years of dual-site CPD.",
                "active_active_transition": "High availability activo-activo.",
                "app_modernization_relation": "Aligned with NIS2 requirements."
            }
        elif schema == Phase3Benefits:
            return {
                "strategic_levers": ["Palanca 1", "Palanca 2"],
                "global_benefits": ["Beneficio 1", "Beneficio 2"],
                "public_mission_impact": "National resilience."
            }
        elif schema == Phase4RisksAndAssumptions:
            return {
                "assumptions_structural": ["Supuesto S1"],
                "assumptions_technological": ["Supuesto T1"],
                "assumptions_regulatory": ["Supuesto R1"],
                "risks_if_not_acted": ["Riesgo N1"],
                "risks_of_implementation": ["Riesgo I1"],
                "next_steps": ["Siguiente paso 1"]
            }
        elif schema == HighLevelRoadmap:
            return {
                "phase_1_short_term": ["Tactical 1"],
                "phase_2_mid_term": ["Medium 1"],
                "phase_3_long_term": ["Strategic 1"]
            }
        elif schema == SynthesisAudit:
            verifier_call_count += 1
            if verifier_call_count == 1:
                # First round fails - verifier demands a specific correction
                return {
                    "is_approved": False,
                    "hallucinations_detected": ["Missing critical ENS High security references."],
                    "remediation_critique": "Please add explicit ENS High category compliance in executive_vision."
                }
            else:
                # Second round succeeds
                return {
                    "is_approved": True,
                    "hallucinations_detected": [],
                    "remediation_critique": ""
                }
        
        # Fallback to general risks/assumptions
        return {
            "assumptions_structural": ["Supuesto S1"],
            "assumptions_technological": ["Supuesto T1"],
            "assumptions_regulatory": ["Supuesto R1"],
            "risks_if_not_acted": ["Riesgo N1"],
            "risks_of_implementation": ["Riesgo I1"],
            "next_steps": ["Siguiente paso 1"]
        }

    # 2. Act - Run the synthesizer with mocked Vertex AI agent execution
    with patch("assessment_engine.application.run_global_synthesizer_tobe.run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = mock_run_agent_impl
        
        await synthesize_global_tobe(str(working_dir), "critical_infrastructure")

    # 3. Assert - Verify output exists and reflection loop was executed twice
    summary_file = working_dir / "global_tobe_executive_summary.json"
    assert summary_file.exists(), "The global TO-BE summary file was not generated."
    
    # Ensure the verifier was called twice (Ronda 1 rejected, Ronda 2 approved)
    assert verifier_call_count == 2, f"Expected 2 verifier calls (self-healing), but got {verifier_call_count}."
    
    # Read the output and verify schema structure
    with open(summary_file, "r", encoding="utf-8-sig") as f:
        summary_data = json.load(f)
        
    assert summary_data["executive_vision"] == "Sovereign cloud vision."
    assert "NIS2" in summary_data["app_modernization_relation"]
    assert "roadmap" in summary_data
    assert summary_data["roadmap"]["phase_1_short_term"] == ["Tactical 1"]
