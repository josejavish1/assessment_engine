"""Unit tests verifying quadri-lingual context-aware Gamma and Beta narrative resolution."""

import json
from pathlib import Path
import pytest

from assessment_engine.adapters.compilers.strategies.actuarial_receptors import (
    ActuarialReceptorContext,
    ActuarialReceptorFactory,
)
from assessment_engine.domain.taxonomy.archetype_registry import LossArchetypeType

LOCALES_PATH = Path("engine_config/locales.json")
LOCALES_DATA = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))


def _make_dummy_context(delivery_model: str, operational_archetype: str, gamma: float, beta: float, lang: str) -> ActuarialReceptorContext:
    loc_branch = LOCALES_DATA.get(lang, LOCALES_DATA["en"])
    return ActuarialReceptorContext(
        total_fair_ale=100_000.0,
        currency="EUR",
        meta_lang=lang,
        tower_name="Test Domain",
        client_name="Test Corp",
        loc_branch=loc_branch,
        primary_color_rgb=[48, 84, 150],
        alt_row_hex="F2F4F8",
        ch4_sec1_title="4.1 Test Heading",
        callout_title="Note",
        callout_body="Callout body text",
        delivery_model=delivery_model,
        operational_archetype=operational_archetype,
        cloud_intensity_gamma=gamma,
        buffering_elasticity_beta=beta,
    )


def test_cloud_native_finops_narrative_resolution() -> None:
    strategy = ActuarialReceptorFactory.get_strategy(LossArchetypeType.CAPITAL_INEFFICIENCY)

    # Cloud Native in English
    ctx_en = _make_dummy_context("CLOUD_NATIVE", "CONTINUOUS_DIGITAL_FINTECH", 0.85, 0.95, "en")
    nodes_en = strategy.build_ast_nodes(ctx_en)
    supp_en = nodes_en[-1].text.lower()
    assert "cloud-native finops topology" in supp_en
    assert "on-premise" not in supp_en

    # On Prem Heavy in Spanish
    ctx_es = _make_dummy_context("ON_PREM_HEAVY", "PROCESS_MANUFACTURING_OT", 0.22, 0.35, "es")
    nodes_es = strategy.build_ast_nodes(ctx_es)
    supp_es = nodes_es[-1].text.lower()
    assert "gobernanza de infraestructura y licenciamiento por core" in supp_es or "infraestructura" in supp_es
    assert "broadcom" not in supp_es  # Certified vendor-neutral!
    assert "vmware" not in supp_es

    # Hybrid in Portuguese
    ctx_pt = _make_dummy_context("HYBRID", "LIFE_SAFETY_CRITICAL", 0.45, 0.78, "pt")
    nodes_pt = strategy.build_ast_nodes(ctx_pt)
    supp_pt = nodes_pt[-1].text.lower()
    assert "nuvem híbrida" in supp_pt


def test_buffering_elasticity_narrative_resolution() -> None:
    strategy = ActuarialReceptorFactory.get_strategy(LossArchetypeType.AVAILABILITY_OUTAGE)

    # Industrial Silos in Spanish (low beta)
    ctx_ind = _make_dummy_context("ON_PREM_HEAVY", "PROCESS_MANUFACTURING_OT", 0.22, 0.35, "es")
    nodes_ind = strategy.build_ast_nodes(ctx_ind)
    supp_ind = nodes_ind[-1].text.lower()
    assert "amortiguación física por silos" in supp_ind

    # FinTech Realtime Clearing in English (high beta)
    ctx_fin = _make_dummy_context("CLOUD_NATIVE", "CONTINUOUS_DIGITAL_FINTECH", 0.85, 0.95, "en")
    nodes_fin = strategy.build_ast_nodes(ctx_fin)
    supp_fin = nodes_fin[-1].text.lower()
    assert "synchronous clearing sensitivity" in supp_fin

    # Healthcare ICU Telemetry in Portuguese (high beta)
    ctx_med = _make_dummy_context("HYBRID", "LIFE_SAFETY_CRITICAL", 0.45, 0.78, "pt")
    nodes_med = strategy.build_ast_nodes(ctx_med)
    supp_med = nodes_med[-1].text.lower()
    assert "vulnerabilidade clínica aguda" in supp_med
