"""Integration test suite for empirical multi-national, multi-sector, and multi-lingual simulation."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.simulate_multinational_archetypes import (
    ARCHETYPES,
    BASE_OUTPUT_DIR,
    simulate_archetype,
)


def test_empirical_multinational_simulation_all_archetypes():
    """Verify that all 4 global enterprise archetypes compile valid physical DOCX deliverables."""
    assert len(ARCHETYPES) == 4, "Debe haber exactamente 4 arquetipos globales definidos."

    for archetype in ARCHETYPES:
        result = simulate_archetype(archetype)
        assert result["checks_passed"] is True, f"Archetype {archetype.archetype_id} failed quality checks."
        assert len(result["generated_files"]) >= 4, f"Archetype {archetype.archetype_id} produced fewer than 4 files."

        # Verify physical file existence and non-zero size
        for f_path_str in result["generated_files"]:
            f_path = Path(f_path_str)
            assert f_path.is_file(), f"Deliverable {f_path} does not exist physically."
            min_size = 10000 if f_path.suffix == ".docx" else 50
            assert f_path.stat().st_size > min_size, f"Deliverable {f_path} is unexpectedly small."


def test_simulation_summary_log_structure():
    """Verify that SIMULATION_SUMMARY.json exists and certifies zero template leaks and correct currencies."""
    summary_path = BASE_OUTPUT_DIR / "SIMULATION_SUMMARY.json"
    assert summary_path.is_file(), "SIMULATION_SUMMARY.json must be generated in working/out/simulations/."

    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(data) == 4

    currencies_found = {item["currency"] for item in data}
    assert currencies_found == {"€", "¥", "$"}

    for item in data:
        assert item["checks_passed"] is True
        details = item["check_details"]
        # Verify no check detail failed
        failed_checks = [d for d in details if not d["passed"]]
        assert len(failed_checks) == 0, f"Found failed checks in {item['archetype_id']}: {failed_checks}"
