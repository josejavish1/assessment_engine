# golden-path: ignore
from __future__ import annotations

import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph


def test_epistemic_graph_system_schema_validation(tmp_path):
    # Set up a namespaced test graph
    client_id = "schema_test_client"
    try:
        graph = EpistemicGraph(client_id=client_id)

        # 1. Valid system-injected predicate should pass
        graph.inject_triple(
            subject="P01",
            predicate="BELONGS_TO_TOWER",
            object_val="T5",
            source="TOWER_PIPELINE",
            confidence=1.0,
        )
        truth = graph.resolve_truth()
        assert "P01" in truth
        assert truth["P01"]["BELONGS_TO_TOWER"]["value"] == "T5"

        # 2. Invalid system-injected predicate should raise ValueError
        with pytest.raises(ValueError) as exc:
            graph.inject_triple(
                subject="P01",
                predicate="INVALID_SYS_RELATION",
                object_val="T5",
                source="TOWER_PIPELINE",
                confidence=1.0,
            )
        assert "Graph Schema Violation: System-injected predicate" in str(exc.value)
    finally:
        import shutil
        from pathlib import Path
        p = Path("working") / client_id
        if p.exists():
            shutil.rmtree(p)


def test_epistemic_graph_dynamic_schema_validation():
    client_id = "dynamic_schema_test"
    try:
        graph = EpistemicGraph(client_id=client_id)

        # 1. Valid AI-extracted predicate in uppercase SNAKE_CASE should pass
        graph.inject_triple(
            subject="DATABASE_SRV",
            predicate="RUNS_ON_HARDWARE",
            object_val="BLADE_01",
            source="OSINT",
            confidence=0.5,
        )
        truth = graph.resolve_truth()
        assert "DATABASE_SRV" in truth
        assert truth["DATABASE_SRV"]["RUNS_ON_HARDWARE"]["value"] == "BLADE_01"

        # 2. Invalid dynamic predicate (lowercase or containing spaces/hyphens) should raise ValueError
        with pytest.raises(ValueError) as exc:
            graph.inject_triple(
                subject="DATABASE_SRV",
                predicate="runs-on-hardware",
                object_val="BLADE_01",
                source="OSINT",
                confidence=0.5,
            )
        assert "Graph Schema Violation: Predicate" in str(exc.value)
    finally:
        import shutil
        from pathlib import Path
        p = Path("working") / client_id
        if p.exists():
            shutil.rmtree(p)
