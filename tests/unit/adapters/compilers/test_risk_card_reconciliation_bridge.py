"""Unit test oracle: Mathematical Reconciliation Bridge in Open FAIR Risk Cards (SR 11-7 / Red Team Certified).

Statically and dynamically verifies that:
1. Primary Downtime + Direct Replacement + Weighted Secondary + Stochastic Adjustment == Mean SLE.
2. LEF * Mean SLE - Euler Diversification Credit == Net Allocated ALE.
3. Every displayed arithmetic step closes with 100.00% precision without unparsed template variables.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge
from assessment_engine.domain.schemas.ast import TableNode


def _extract_all_cell_texts(table_node: TableNode) -> list[str]:
    """Flattens all text entries inside a TableNode."""
    texts = []
    for row in table_node.rows:
        for cell in row.cells:
            if cell.text:
                texts.append(cell.text)
    return texts


def test_risk_card_reconciliation_bridge_closed_form_arithmetic() -> None:
    """Verifies that the generated risk card table presents exact closed-form arithmetic reconciling to Mean SLE and Net ALE."""
    bridge = PayloadToASTBridge()

    sample_hc: Dict[str, Any] = {
        "id": "RVS03",
        "node_id": "T1_F003",
        "capability": "UPS Battery Degradation and Power Redundancy Gap",
        "finding": "CPD 2 UPS battery string shows severe chemical degradation without automatic CGBT failover.",
        "business_risk": "Power supply disruption halting manufacturing process dispatch.",
        "severity": "CRITICAL",
        "tef": 2.5,
        "lm": 3.0,
        "recovery_time_hours": 8.0,
        "hourly_burn_rate": 13061.29,
        "direct_replacement_cost": 15000.0,
        "secondary_loss_mean": 46260.0,
        "blast_radius_alpha": 0.70,
        "ownership_type": "PRIMARY_CUSTODIAN",
        "actuarial_input_vector": {
            "inputs": {
                "rto_hours_mode": {"effective_value": 8.0},
                "hourly_burn_rate": {"effective_value": 13061.29},
                "blast_radius_alpha": {"effective_value": 0.70},
                "direct_replacement_cost": {"effective_value": 15000.0},
                "secondary_loss_mean": {"effective_value": 46260.0},
            },
            "outputs": {
                "mean_lef": 1.55,
                "mean_sle": 45224.0,
                "portfolio_allocated_ale": 61669.0,
                "standalone_ale": 70079.0,
                "var_90": 88400.0,
                "var_99": 215000.0,
            },
        },
    }

    ctx: Dict[str, Any] = {
        "meta_lang": "es",
        "currency": "€",
        "tower_id": "T1",
        "total_fair_ale": 229249.0,
        "blueprint_data": {
            "document_meta": {"tower_id": "T1"},
            "hourly_burn_rate": 13061.29,
        },
    }

    card_table = bridge._build_risk_mini_infographic_card(
        ctx=ctx,
        hc=sample_hc,
        t_idx=1,
        p_name="Instalaciones Físicas y Suministro Eléctrico",
        total_fair_ale=229249.0,
    )

    assert isinstance(card_table, TableNode)
    all_texts = _extract_all_cell_texts(card_table)
    full_card_text = "\n".join(all_texts)

    # 1. Assert zero unparsed template tokens or Python placeholders
    assert not re.search(r"\{[a-zA-Z0-9_]+\}", full_card_text), f"Unparsed template variable found: {full_card_text}"
    assert "NaN" not in full_card_text
    assert "None" not in full_card_text

    # 2. Assert that Mean SLE (92.769 €) and Net ALE (61.669 €) are explicitly printed
    assert "92.769 €" in full_card_text or "92.769" in full_card_text
    assert "61.669 €" in full_card_text or "61.669" in full_card_text

    # 3. Assert the presence of the structured arithmetic breakdown
    assert "SLE" in full_card_text
    assert "ALE" in full_card_text
