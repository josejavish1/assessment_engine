import json
from pathlib import Path

import pytest

from assessment_engine.application.build_evidence_ledger import (
    build_evidence_entries,
)


def test_evidence_ledger_density_ranking_over_fifo(tmp_path: Path):
    """Verify that build_evidence_entries ranks fragments globally by keyword density
    and picks the highest-overlap RAPTOR summary instead of arbitrary sequential FIFO."""
    vault_file = tmp_path / "evidence_vault.json"
    tree_file = tmp_path / "raptor_tree.json"

    # 1. Setup fragments: frag1 has low overlap, frag2 has high overlap
    fragments = [
        {
            "fragment_id": "frag_low_001",
            "source_uri": "doc.docx",
            "content": "La sala técnica tiene alimentación eléctrica básica.",
        },
        {
            "fragment_id": "frag_high_002",
            "source_uri": "doc.docx",
            "content": "Autonomía eléctrica garantizada con SAI redundante y generador diésel de conmutación.",
        },
    ]
    vault_file.write_text(json.dumps({"fragments": fragments}), encoding="utf-8")

    # 2. Setup raptor tree: node1 has 1 token overlap, node2 has multiple token overlap
    raptor_nodes = {
        "n1": {
            "node_id": "n1",
            "level": 1,
            "content": "Resumen genérico de sala técnica.",
        },
        "n2": {
            "node_id": "n2",
            "level": 1,
            "content": "Resumen sobre energía, continuidad eléctrica, generador, autonomía y SAI.",
        },
    }
    tree_file.write_text(
        json.dumps({"nodes": raptor_nodes}), encoding="utf-8"
    )

    case_input = {
        "_build_metadata": {"context_file": str(vault_file)},
        "tower_id": "T1",
        "answers": [
            {
                "kpi_id": "T1.P1.K1",
                "question_id": "Q1",
                "kpi_name": "Autonomía eléctrica",
                "value": 3.0,
            }
        ],
    }

    tower_definition = {
        "pillars": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Energía y Continuidad Eléctrica",
                "kpis": [
                    {
                        "kpi_id": "T1.P1.K1",
                        "kpi_name": "Autonomía eléctrica garantizada",
                    }
                ],
            }
        ]
    }

    entries = build_evidence_entries(
        case_input, tmp_path, Path("responses.txt"), tower_definition
    )

    # 1. Best RAPTOR summary must be n2 (highest overlap), not n1 (FIFO)
    strat_entries = [
        e for e in entries if e["source_type"] == "strategic_summary"
    ]
    assert len(strat_entries) == 1
    assert strat_entries[0]["raptor_node_id"] == "n2"

    # 2. The highest-ranked fragment (frag_high_002) must be ranked first among atomic fragments
    frag_entries = [
        e for e in entries if e["source_type"] == "atomic_fragment"
    ]
    assert len(frag_entries) == 2
    assert frag_entries[0]["fragment_id"] == "frag_high_002"
    assert "T1.P1.K1" in frag_entries[0]["kpi_ids"]
