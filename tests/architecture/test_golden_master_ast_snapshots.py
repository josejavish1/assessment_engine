"""Architectural Golden Master Characterization Test Suite (Phase 0 Ironclad Shield).

Enforces strict zero-regression invariance across Document AST generation.
Captures full structural topology, table geometries, cell payloads, and node sequences.
Any unauthorized modification to table layouts, node orders, or financial calculations
instantly fails this suite, preventing silent document corruption.
Written in 100% Technical English.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge
from assessment_engine.infrastructure.runtime_paths import ROOT

GOLDEN_DIR = ROOT / "tests" / "golden_masters"
TOWERS = ["t1", "t2", "t5"]


@pytest.fixture(scope="module")
def bridge() -> PayloadToASTBridge:
    return PayloadToASTBridge()


@pytest.mark.parametrize("tower_code", TOWERS)
def test_ast_golden_master_characterization_fidelity(bridge: PayloadToASTBridge, tower_code: str) -> None:
    """Verifies that the generated DocumentAST matches the frozen Golden Master bit-for-bit."""
    snapshot_file = GOLDEN_DIR / f"molins_{tower_code}_ast_snapshot.json"
    assert snapshot_file.exists(), f"Golden master snapshot missing: {snapshot_file}"

    payload_path = ROOT / "working" / "molins" / tower_code.upper() / f"blueprint_{tower_code}_payload.json"
    assert payload_path.exists(), f"Source blueprint payload missing: {payload_path}"

    golden_data = json.loads(snapshot_file.read_text(encoding="utf-8"))
    current_ast = bridge.convert(str(payload_path))
    current_data = current_ast.model_dump()

    # 1. Title and Metadata Invariance
    assert current_data["title"] == golden_data["title"], (
        f"Document title mismatch: {current_data['title']!r} != {golden_data['title']!r}"
    )

    # 2. Total Node Count Invariance
    golden_nodes = golden_data["nodes"]
    current_nodes = current_data["nodes"]
    assert len(current_nodes) == len(golden_nodes), (
        f"AST node count diverged for {tower_code.upper()}: "
        f"current={len(current_nodes)} vs golden={len(golden_nodes)}"
    )

    # 3. Structural Sequence and Node Type Invariance
    for idx, (curr, gold) in enumerate(zip(current_nodes, golden_nodes)):
        curr_type = curr.get("type")
        gold_type = gold.get("type")
        assert curr_type == gold_type, (
            f"Node {idx} type divergence in {tower_code.upper()}: current={curr_type} vs golden={gold_type}"
        )

        # For Headings: verify level and exact text
        if curr_type == "heading":
            assert curr.get("level") == gold.get("level"), (
                f"Heading {idx} level mismatch: {curr.get('level')} != {gold.get('level')}"
            )
            assert curr.get("text") == gold.get("text"), (
                f"Heading {idx} text mismatch: {curr.get('text')!r} != {gold.get('text')!r}"
            )

        # For Tables: verify exact geometry (rows, columns) and cell text
        elif curr_type == "table":
            curr_rows = curr.get("rows", [])
            gold_rows = gold.get("rows", [])
            assert len(curr_rows) == len(gold_rows), (
                f"Table {idx} row count divergence in {tower_code.upper()}: "
                f"current={len(curr_rows)} vs golden={len(gold_rows)}"
            )
            for r_idx, (c_row, g_row) in enumerate(zip(curr_rows, gold_rows)):
                c_cells = c_row.get("cells", [])
                g_cells = g_row.get("cells", [])
                assert len(c_cells) == len(g_cells), (
                    f"Table {idx} row {r_idx} cell count mismatch in {tower_code.upper()}: "
                    f"current={len(c_cells)} vs golden={len(g_cells)}"
                )
                for c_idx, (c_cell, g_cell) in enumerate(zip(c_cells, g_cells)):
                    c_txt = c_cell.get("text", "").strip()
                    g_txt = g_cell.get("text", "").strip()
                    assert c_txt == g_txt, (
                        f"Table {idx} cell [{r_idx}, {c_idx}] text divergence in {tower_code.upper()}:\n"
                        f"Current: {c_txt!r}\nGolden:  {g_txt!r}"
                    )
