"""Unit tests for RFC 076: Executive Narrative Realism & Operational Continuity Governance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")


@pytest.fixture
def locales_catalog() -> Dict[str, Any]:
    """Loads the canonical locales catalog."""
    repo_root = Path(__file__).resolve().parents[2]
    locales_path = repo_root / "engine_config" / "locales.json"
    with open(locales_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_rfc076_fallback_continuity_bullet_symmetry(locales_catalog: Dict[str, Any]) -> None:
    """Quality Gate: Assert fallback continuity bullet exists across all 6 locales without rate placeholders."""
    for locale in SUPPORTED_LOCALES:
        assert locale in locales_catalog, f"Missing locale '{locale}'"
        title = locales_catalog[locale].get("tomo_ch1_continuity_bullet_title", "")
        body = locales_catalog[locale].get("tomo_ch1_continuity_bullet_body", "")

        assert len(title.strip()) > 5, f"Title too short in locale '{locale}'"
        assert len(body.strip()) > 20, f"Body too short in locale '{locale}'"

        # Assert zero simulation rate mechanics or hardcoded numbers in fallback bullet body
        assert "hourly_rate" not in body, f"Legacy placeholder in locale '{locale}'"
        assert "€/h" not in body, f"Methodological rate unit in locale '{locale}'"
        assert "5.000" not in body, f"Static rate in locale '{locale}'"
        assert "13.061" not in body, f"Static rate in locale '{locale}'"


def test_rfc076_dynamic_burning_platform_extraction() -> None:
    """Verify that Chapter 1 extracts bullets dynamically from burning_platform when present."""
    from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
        Volume1AsisASTCompiler,
    )

    compiler = Volume1AsisASTCompiler()
    global_payload = {
        "burning_platform": [
            {
                "theme": "Operational Continuity & Edge Vulnerability",
                "business_risk": "Local plant and warehouse nodes suffer from single points of failure in edge connectivity.",
            },
            {
                "theme": "Legacy Core Saturation",
                "business_risk": "Central mainframe and batch processing operate near 95% capacity ceiling.",
            },
        ],
        "meta": {"client": "GLOBAL BANK", "date": "2026-11-05"},
    }

    nodes: list = []
    compiler._build_chapter_1_executive_summary(
        nodes=nodes,
        global_payload=global_payload,
        tower_payloads={},
        client_name="GLOBAL BANK",
        currency="€",
        doc_lang="en",
    )

    bullet_nodes = [n for n in nodes if hasattr(n, "style") and n.style == "List Bullet"]
    assert len(bullet_nodes) == 2
    assert "Operational Continuity & Edge Vulnerability" in bullet_nodes[0].text
    assert "Legacy Core Saturation" in bullet_nodes[1].text
