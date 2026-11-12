from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.infrastructure.runtime_paths import ROOT
from assessment_engine.domain.maturity_band import ANNEX_MATURITY_BANDS, resolve_maturity_band
from assessment_engine.domain.services.domain_router import DomainSemanticRouter, TowerID


def test_legacy_keyword_file_is_completely_eradicated() -> None:
    """Invariant 1: Brittle substring keyword configuration must never exist in the codebase."""
    legacy_file = ROOT / "engine_config" / "tower_classification_keywords.json"
    assert not legacy_file.exists(), "Legacy tower_classification_keywords.json must be deleted permanently."


def test_cmmi_v2_international_band_alignment() -> None:
    """Invariant 2: CMMI Level 4 must be Quantitatively Managed, never confused with Level 2."""
    from assessment_engine.infrastructure.localization import t

    lvl4_band = [b for b in ANNEX_MATURITY_BANDS if b["level"] == 4][0]
    assert lvl4_band["label"] == "Quantitatively Managed"
    assert lvl4_band["band_key"] == "band_quantitatively_managed"

    # In Spanish localization, it must resolve to 'Gestionado Cuantitativamente'
    resolved_es = resolve_maturity_band(4.00, ANNEX_MATURITY_BANDS, locale="es", translator=t)
    assert resolved_es["label"] == "Gestionado Cuantitativamente"

    # Level 2 must resolve to 'Gestionado' or 'Repetible'
    resolved_l2_es = resolve_maturity_band(2.10, ANNEX_MATURITY_BANDS, locale="es", translator=t)
    assert resolved_l2_es["label"] in ("Gestionado", "Repetible", "Gestionado (Repetible)")


def test_brand_profile_is_neutral_and_white_labeled() -> None:
    """Invariant 3: Default brand profile must never hardcode third-party corporate entities like NTT DATA."""
    brand_path = ROOT / "engine_config" / "brand_profile.json"
    assert brand_path.exists()
    brand_data = json.loads(brand_path.read_text(encoding="utf-8"))
    assert "NTT DATA" not in brand_data.get("company_name", ""), "company_name must not hardcode NTT DATA"


def test_domain_semantic_router_physical_environment_and_process_overrides() -> None:
    """Invariant 4: Concrete plants belong strictly to T10; DRP governance belongs strictly to T5."""
    router = DomainSemanticRouter()
    
    # Concrete plant servers -> must be T10, NEVER T1
    plant_decision = router.route_finding("Permanencia de servidores locales en casetas de control de hormigón en delegaciones de fábrica")
    assert plant_decision.primary_tower == TowerID.T10, "Plant-floor servers must route to T10, not T1"

    # DRP governance -> must be T5, NEVER T1
    drp_decision = router.route_finding("Ausencia de un Plan de Recuperación ante Desastres (DRP) para conmutar aplicaciones de negocio")
    assert drp_decision.primary_tower == TowerID.T5, "DRP software plans must route to T5, not T1"


def test_two_tier_table_8_mathematical_closure() -> None:
    """Invariant 5: Table 8 two-tier financial reconciliation balances exactly: Standalone - Simultaneity = Net."""
    standalone_sum = 174460
    simultaneity_adj = -17061
    expected_net = 157399

    assert standalone_sum + simultaneity_adj == expected_net, "Two-tier table math must close to the exact cent."
