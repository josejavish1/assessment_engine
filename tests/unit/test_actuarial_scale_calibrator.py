"""Unit tests for Dynamic Loss Magnitude (LM) scale calibrator."""

from __future__ import annotations

import math
import pytest

from assessment_engine.domain.actuarial_scale_calibrator import (
    CURRENCY_SCALE_PARITY,
    clamp_scale_level,
    compute_dynamic_lm_brackets,
    compute_dynamic_lm_thresholds,
    resolve_currency_parity,
    resolve_dynamic_lm_scale_level,
    resolve_iso_currency_code,
    resolve_risk_matrix_coordinates,
    safe_float,
)


def test_default_eur_thresholds() -> None:
    """Verifies default baseline thresholds for EUR without custom telemetry."""
    t1, t2, t3, t4 = compute_dynamic_lm_thresholds(currency="EUR", is_critical_tier=False)
    assert t1 == 1000.0
    assert t2 == 4000.0
    assert t3 == 16000.0
    assert t4 == 64000.0

    t1_crit, t2_crit, t3_crit, t4_crit = compute_dynamic_lm_thresholds(
        currency="EUR", is_critical_tier=True
    )
    assert t1_crit == 2500.0
    assert t2_crit == 12500.0
    assert t3_crit == 62500.0
    assert t4_crit == 250000.0


def test_jpy_currency_parity_scaling() -> None:
    """Verifies that JPY scales by currency parity factor (160x) preventing premature LM 5 caps."""
    t1, t2, t3, t4 = compute_dynamic_lm_thresholds(currency="JPY", is_critical_tier=True)
    assert t1 >= 100000.0
    assert t4 >= 10000000.0  # At least 10M JPY for catastrophic tier

    brackets = compute_dynamic_lm_brackets(currency="¥", locale="ja", is_critical_tier=True)
    assert len(brackets) == 5
    assert "¥" in brackets[5]
    assert "<" in brackets[1]
    assert "≥" in brackets[5] or ">=" in brackets[5]


def test_large_enterprise_revenue_anchoring() -> None:
    """Verifies that a $50B multinational bank scales LM thresholds to millions."""
    annual_rev = 50_000_000_000.0
    hourly_burn = 2_500_000.0
    t1, t2, t3, t4 = compute_dynamic_lm_thresholds(
        currency="USD",
        annual_revenue=annual_rev,
        hourly_downtime_cost=hourly_burn,
        is_critical_tier=True,
    )
    # LM 1 upper bound should be anchored near ~2 hours of burn = $5,000,000
    assert t1 >= 1_000_000.0
    assert t4 >= 100_000_000.0


def test_resolve_dynamic_lm_scale_level() -> None:
    """Verifies accurate mapping of continuous loss expectancy to 1..5 discrete scale."""
    thresholds = (1000.0, 5000.0, 25000.0, 100000.0)
    assert resolve_dynamic_lm_scale_level(500.0, thresholds) == 1
    assert resolve_dynamic_lm_scale_level(1000.0, thresholds) == 2
    assert resolve_dynamic_lm_scale_level(4999.0, thresholds) == 2
    assert resolve_dynamic_lm_scale_level(5000.0, thresholds) == 3
    assert resolve_dynamic_lm_scale_level(24999.0, thresholds) == 3
    assert resolve_dynamic_lm_scale_level(25000.0, thresholds) == 4
    assert resolve_dynamic_lm_scale_level(99999.0, thresholds) == 4
    assert resolve_dynamic_lm_scale_level(100000.0, thresholds) == 5
    assert resolve_dynamic_lm_scale_level(5000000.0, thresholds) == 5


def test_nan_inf_negative_resilience() -> None:
    """Guarantees resilience against NaN, Infinity, and negative values."""
    t1, t2, t3, t4 = compute_dynamic_lm_thresholds(
        currency="USD",
        annual_revenue=float("nan"),
        hourly_downtime_cost=float("inf"),
        is_critical_tier=False,
    )
    assert t1 == 1000.0
    assert t4 == 64000.0

    thresholds = (1000.0, 4000.0, 16000.0, 64000.0)
    assert resolve_dynamic_lm_scale_level(float("nan"), thresholds) == 1
    assert resolve_dynamic_lm_scale_level(-500.0, thresholds) == 1
    assert resolve_dynamic_lm_scale_level(0.0, thresholds) == 1
    # Unbounded catastrophic tail loss must resolve to maximum LM 5
    assert resolve_dynamic_lm_scale_level(float("inf"), thresholds) == 5


def test_micro_revenue_floor_clamp() -> None:
    """Guarantees that micro-revenue entities ($50k) do not collapse thresholds below minimum floor."""
    t1, t2, t3, t4 = compute_dynamic_lm_thresholds(
        currency="EUR",
        annual_revenue=50_000.0,
        is_critical_tier=False,
    )
    assert t1 >= 100.0
    assert t4 >= 6400.0


def test_currency_scale_parity_immutability() -> None:
    """Verifies that CURRENCY_SCALE_PARITY is strictly immutable to prevent cross-tenant state pollution."""
    with pytest.raises(TypeError):
        CURRENCY_SCALE_PARITY["EUR"] = 999.0  # type: ignore[index]


def test_locale_formatting_variations() -> None:
    """Verifies thousands separators for Spanish/German (dot), French (space), and US/UK (comma)."""
    b_es = compute_dynamic_lm_brackets(currency="EUR", locale="es-ES", is_critical_tier=False)
    assert "1.000" in b_es[1] or "1.000" in b_es[2]

    b_fr = compute_dynamic_lm_brackets(currency="EUR", locale="fr-FR", is_critical_tier=False)
    assert "1 000" in b_fr[1] or "1 000" in b_fr[2]

    b_en = compute_dynamic_lm_brackets(currency="USD", locale="en-US", is_critical_tier=False)
    assert "1,000" in b_en[1] or "1,000" in b_en[2]


def test_safe_float_bool_rejection() -> None:
    """Guarantees booleans are explicitly rejected and localized European strings are parsed cleanly."""
    assert safe_float(True) is None
    assert safe_float(False) is None
    assert safe_float(1.0) == 1.0
    assert safe_float("1500.50") == 1500.50
    assert safe_float("50.000.000") == 50000000.0
    assert safe_float("1.000.000,50") == 1000000.50
    assert safe_float("25,50") == 25.50
    assert safe_float("1,500") == 1500.0
    assert safe_float("0,125") == 0.125
    assert safe_float("0,500") == 0.5
    assert safe_float("$1,500.00") == 1500.0
    assert safe_float("EUR 50.000,00") == 50000.0
    assert safe_float("EUR 50,000") == 50000.0
    assert safe_float("1'500'000.50") == 1500000.50
    assert safe_float("1\u2019500\u2019000") == 1500000.0
    assert safe_float("1\u00a0500\u00a0000") == 1500000.0
    assert safe_float("1\u202f500\u202f000.75") == 1500000.75
    assert safe_float("1,125", locale="es-ES") == 1.125
    assert safe_float("1,125", locale="en-US") == 1125.0
    assert safe_float("50.000", locale="es-ES") == 50000.0
    assert safe_float("50.000", locale="en-US") == 50.0
    assert safe_float("1e-05") == 0.00001
    assert safe_float("2.5E+07") == 25000000.0
    assert safe_float("$1.5e6") == 1500000.0
    assert safe_float("1,5e6") == 1500000.0
    assert safe_float("0.0", allow_zero=True) == 0.0
    assert safe_float("0.0", allow_zero=False) is None
    assert safe_float("0.125", locale="es-ES") == 0.125
    assert safe_float("1,000e3") == 1000000.0
    assert safe_float("1,000e3", locale="en-US") == 1000000.0
    assert safe_float("1.500,25e3", locale="es-ES") == 1500250.0
    assert safe_float("-$1,500.00") is None
    assert safe_float("$ -1,500.00") is None
    assert safe_float("inf") is None
    assert safe_float("+Infinity") is None
    assert safe_float("NaN") is None
    assert safe_float("invalid") is None


def test_clamp_scale_level_bounds() -> None:
    """Verifies scale level clamping into strictly 1..5 range."""
    assert clamp_scale_level(0) == 1
    assert clamp_scale_level(1) == 1
    assert clamp_scale_level(3.4) == 3
    assert clamp_scale_level(5) == 5
    assert clamp_scale_level(10) == 5
    assert clamp_scale_level("N/A", default=2) == 2


def test_resolve_risk_matrix_coordinates_decoupled() -> None:
    """Verifies decoupled TEF and LM axis resolution with continuous and discrete fallbacks."""
    thresholds = (1000.0, 4000.0, 16000.0, 64000.0)

    # 1. Full continuous telemetry
    risk_full = {"lef": 1.5, "sle": 25000.0}
    assert resolve_risk_matrix_coordinates(risk_full, thresholds) == (3, 4)

    # 2. Continuous SLE with discrete TEF scale level
    risk_partial = {"tef_scale_level": 4, "sle": 800.0}
    assert resolve_risk_matrix_coordinates(risk_partial, thresholds) == (4, 1)

    # 3. Catastrophic unbounded loss (+inf)
    risk_inf = {"lef": float("inf"), "sle": float("inf")}
    assert resolve_risk_matrix_coordinates(risk_inf, thresholds) == (5, 5)

    # 4. Monetary value in 'lm' field (> 5.0) resolved dynamically instead of clamped to 5
    risk_monetary_lm = {"tef": 2, "lm": 25000.0}
    assert resolve_risk_matrix_coordinates(risk_monetary_lm, thresholds) == (2, 4)


def test_currency_symbol_locale_disambiguation() -> None:
    """Verifies disambiguation of ambiguous symbols (¥, $) based on client locale context."""
    # ¥ with Chinese locale -> CNY parity ~7.2
    t1_cny, *_ = compute_dynamic_lm_thresholds(currency="¥", locale="zh-CN", is_critical_tier=False)
    # ¥ with Japanese locale -> JPY parity 160.0
    t1_jpy, *_ = compute_dynamic_lm_thresholds(currency="¥", locale="ja-JP", is_critical_tier=False)
    assert t1_jpy > t1_cny * 10  # JPY threshold is significantly higher due to unit denomination

    # $ with Mexican Spanish locale -> MXN parity ~18.0
    t1_mxn, *_ = compute_dynamic_lm_thresholds(currency="$", locale="es-MX", is_critical_tier=False)
    # $ with US English locale -> USD parity 1.0
    t1_usd, *_ = compute_dynamic_lm_thresholds(currency="$", locale="en-US", is_critical_tier=False)
    assert t1_mxn > t1_usd * 10

    # Public resolve_currency_parity verification
    assert resolve_currency_parity("JPY", locale="ja") >= 140.0
    assert resolve_currency_parity("EUR") == 1.0
    assert resolve_currency_parity("USD") == 1.0


def test_regional_locale_thousands_separators() -> None:
    """Verifies regional comma formatting for Mexican Spanish and Swiss apostrophes."""
    # Mexican Spanish uses comma as thousands separator, not dot
    b_mx = compute_dynamic_lm_brackets(currency="MXN", locale="es-MX", is_critical_tier=False)
    assert "," in b_mx[1] or "," in b_mx[2]

    # Swiss German uses apostrophe
    b_ch = compute_dynamic_lm_brackets(currency="CHF", locale="de-CH", is_critical_tier=False)
    assert "'" in b_ch[1] or "'" in b_ch[2]


def test_actuarial_scale_mutation_survivor_invariants() -> None:
    """Verifies boundary conditions that kill AST mutants in calibrator."""
    from assessment_engine.domain.actuarial_scale_calibrator import _extract_bcp47_lang_and_region

    # Line 171 mutants: invert == to != in len(part) == 2 or len(part) == 3
    assert _extract_bcp47_lang_and_region("zh-hant-hk")[2] == "hk"
    assert _extract_bcp47_lang_and_region("es-419")[2] == "419"
    assert resolve_iso_currency_code("¥", locale="zh-Hant-HK") == "HKD"

    # Line 232 mutant: invert allow_zero=False to True
    assert safe_float(0.0) is None
    assert safe_float(0.0, allow_zero=True) == 0.0
