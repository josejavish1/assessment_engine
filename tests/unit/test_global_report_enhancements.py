"""Unit tests for Global Report 10/10 Tier-1 Enhancements: Board Memo, Cross-Tower Nexus, and Executive Callouts."""

from pathlib import Path
from assessment_engine.domain.schemas.global_report import (
    BoardMemoDraft,
    CrossTowerNexusDraft,
    ExecutiveCalloutItem,
    GlobalReportPayload,
)
from assessment_engine.application.build_global_report_payload import (
    _build_board_memo,
    _build_cross_tower_nexus,
    _build_executive_callouts,
    build_global_payload,
)


def test_build_board_memo_structure() -> None:
    """Verify that _build_board_memo constructs valid BoardMemoDraft schemas."""
    mock_towers = [
        {"id": "T6", "name": "Seguridad de Infraestructura", "score": "2.8", "band": "Definido", "status_color": "E06666"}
    ]
    memo_dict = _build_board_memo(mock_towers, [], "Molins", doc_lang="es")
    memo = BoardMemoDraft.model_validate(memo_dict)

    assert len(memo.items) == 1
    assert memo.items[0].domain == "T6: Seguridad de Infraestructura"
    assert memo.items[0].status_color == "E06666"
    assert "PAM" in memo.items[0].critical_decision


def test_build_cross_tower_nexus_structure() -> None:
    """Verify that _build_cross_tower_nexus constructs valid CrossTowerNexusDraft schemas."""
    mock_towers = [
        {"id": "T6", "name": "Seguridad", "score": "2.8", "band": "Definido", "status_color": "E06666"},
        {"id": "T2", "name": "Cómputo", "score": "2.5", "band": "Definido", "status_color": "E06666"},
    ]
    nexus_dict = _build_cross_tower_nexus(mock_towers, [], doc_lang="es")
    nexus = CrossTowerNexusDraft.model_validate(nexus_dict)

    assert len(nexus.dependencies) >= 1
    assert any("T6" in d.source_tower and "T2" in d.target_tower for d in nexus.dependencies)


def test_build_executive_callouts_structure() -> None:
    """Verify that _build_executive_callouts constructs valid ExecutiveCalloutItem schemas."""
    callouts_list = _build_executive_callouts("Molins", [], doc_lang="es")
    callouts = [ExecutiveCalloutItem.model_validate(c) for c in callouts_list]

    assert len(callouts) == 3
    types = [c.callout_type for c in callouts]
    assert "legal" in types
    assert "factory" in types
    assert "decision" in types
