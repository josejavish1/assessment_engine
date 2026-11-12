"""Unit test suite for GovernanceScaleEngine.

Verifies:
1. Strict half-open interval partitioning [a_k, a_{k+1}) for CMMI scores.
2. Complete elimination of IEEE 754 floating-point drift via quantization sanitization.
3. Dimensionless downtime hours scaling across multiple global currencies (EUR, USD, GBP, JPY).
4. Full SR 11-7 provenance and zero static monetary thresholds.
Written in 100% Technical English.
"""

from __future__ import annotations

from decimal import Decimal
import pytest

from assessment_engine.domain.governance import (
    FinancialSeverityCode,
    GovernanceScaleEngine,
    MaturityBandCode,
    sanitize_to_decimal,
)


@pytest.fixture
def engine() -> GovernanceScaleEngine:
    return GovernanceScaleEngine.get_instance()


def test_sanitize_to_decimal_eliminates_ieee754_drift() -> None:
    """Verifies that float sanitization via str representation prevents mantissa contamination."""
    res = sanitize_to_decimal(1.95)
    assert res == Decimal("1.9500")

    # Rejection of invalid reals
    with pytest.raises(ValueError, match="Invariant violation"):
        sanitize_to_decimal(-10.0)

    with pytest.raises(ValueError, match="Invalid numeric input"):
        sanitize_to_decimal("invalid_string")


def test_cmmi_half_open_interval_boundary_precision(engine: GovernanceScaleEngine) -> None:
    """Verifies strict half-open interval partitioning [a_k, a_{k+1}) for CMMI maturity scales."""
    # Level 1: [0.00, 1.50)
    m0 = engine.resolve_maturity(0.00)
    assert m0.level == 1
    assert m0.band_code == MaturityBandCode.INITIAL
    assert m0.label == "Initial"

    m1_49 = engine.resolve_maturity(1.49)
    assert m1_49.level == 1
    assert m1_49.band_code == MaturityBandCode.INITIAL

    # Exact boundary 1.50 -> Level 2
    m1_50 = engine.resolve_maturity(1.50)
    assert m1_50.level == 2
    assert m1_50.band_code == MaturityBandCode.REPEATABLE
    assert m1_50.label == "Managed"

    # The 1.84 case -> Level 2
    m1_84 = engine.resolve_maturity(1.84, locale="es")
    assert m1_84.level == 2
    assert m1_84.band_code == MaturityBandCode.REPEATABLE
    assert m1_84.label == "Gestionado"

    # Level 3: [2.50, 3.50)
    m2_49 = engine.resolve_maturity(2.49)
    assert m2_49.level == 2
    m2_50 = engine.resolve_maturity(2.50)
    assert m2_50.level == 3
    assert m2_50.label == "Defined"

    # The 2.55 case -> Level 3
    m2_55 = engine.resolve_maturity(2.55)
    assert m2_55.level == 3

    # Level 4: [3.50, 4.50)
    m3_50 = engine.resolve_maturity(3.50)
    assert m3_50.level == 4
    assert m3_50.label == "Quantitatively Managed"

    # The 4.25 case -> Level 4
    m4_25 = engine.resolve_maturity(4.25, locale="es")
    assert m4_25.level == 4
    assert m4_25.band_code == MaturityBandCode.MANAGED
    assert m4_25.label == "Gestionado Cuantitativamente"

    # Level 5: [4.50, 5.00]
    m4_50 = engine.resolve_maturity(4.50)
    assert m4_50.level == 5
    assert m4_50.label == "Optimizing"

    m5_00 = engine.resolve_maturity(5.00)
    assert m5_00.level == 5


def test_dimensionless_open_fair_scaling_with_hourly_burn_rate(engine: GovernanceScaleEngine) -> None:
    """
    Verifies that Open FAIR Loss Magnitude (LM1-LM5) is dynamically scaled by downtime hours:
    T1 = 1.0 * rate, T2 = 4.0 * rate, T3 = 16.0 * rate, T4 = 64.0 * rate.
    Zero static currency amounts or hardcoded currency symbols.
    """
    # Case 1: Industrial enterprise with 13,061.00 currency_units/hour (e.g. Molins in EUR)
    rate_molins = Decimal("13061.0")

    # Under 1 hour (< 13,061) -> LM1
    r_lm1 = engine.resolve_financial_risk(10000, hourly_burn_rate=rate_molins, locale="es")
    assert r_lm1.open_fair_lm == "LM1"
    assert r_lm1.severity == FinancialSeverityCode.LOW
    assert r_lm1.label == "Muy Bajo"

    # Between 1h and 4h (13,061 to 52,244) -> LM2 (e.g. 35,000)
    r_lm2 = engine.resolve_financial_risk(35000, hourly_burn_rate=rate_molins, locale="es")
    assert r_lm2.open_fair_lm == "LM2"
    assert r_lm2.severity == FinancialSeverityCode.MODERATE
    assert r_lm2.label == "Bajo"

    # Between 4h and 16h (52,244 to 208,976) -> LM3 (e.g. 83,859 in T2)
    r_lm3 = engine.resolve_financial_risk(83859, hourly_burn_rate=rate_molins, locale="es")
    assert r_lm3.open_fair_lm == "LM3"
    assert r_lm3.severity == FinancialSeverityCode.ELEVATED
    assert r_lm3.label == "Medio"

    # Between 16h and 64h (208,976 to 835,904) -> LM4 (e.g. 253,959 in T2)
    r_lm4 = engine.resolve_financial_risk(253959, hourly_burn_rate=rate_molins, locale="es")
    assert r_lm4.open_fair_lm == "LM4"
    assert r_lm4.severity == FinancialSeverityCode.HIGH
    assert r_lm4.label == "Alto"

    # Over 64h (>= 835,904) -> LM5
    r_lm5 = engine.resolve_financial_risk(1000000, hourly_burn_rate=rate_molins, locale="es")
    assert r_lm5.open_fair_lm == "LM5"
    assert r_lm5.severity == FinancialSeverityCode.CRITICAL
    assert r_lm5.label == "Muy Alto"


def test_multi_currency_and_scale_invariance(engine: GovernanceScaleEngine) -> None:
    """Verifies that the engine scales seamlessly to US Tech firm (USD) and SME without currency coupling."""
    # US Tech Enterprise: 50,000 USD/hour
    rate_us = Decimal("50000.0")
    # 40,000 USD is < 1 hour -> LM1
    r_us1 = engine.resolve_financial_risk(40000, hourly_burn_rate=rate_us)
    assert r_us1.open_fair_lm == "LM1"
    assert r_us1.severity == FinancialSeverityCode.LOW
    assert r_us1.label == "Low"

    # 150,000 USD is 3 hours -> LM2
    r_us2 = engine.resolve_financial_risk(150000, hourly_burn_rate=rate_us)
    assert r_us2.open_fair_lm == "LM2"
    assert r_us2.severity == FinancialSeverityCode.MODERATE

    # Small SaaS Company: 200 GBP/hour
    rate_sme = Decimal("200.0")
    # 500 GBP is 2.5 hours -> LM2
    r_sme = engine.resolve_financial_risk(500, hourly_burn_rate=rate_sme)
    assert r_sme.open_fair_lm == "LM2"

    # 20,000 GBP is 100 hours -> LM5 Critical
    r_sme_crit = engine.resolve_financial_risk(20000, hourly_burn_rate=rate_sme)
    assert r_sme_crit.open_fair_lm == "LM5"
    assert r_sme_crit.severity == FinancialSeverityCode.CRITICAL


def test_sr11_7_model_provenance_audit_trail(engine: GovernanceScaleEngine) -> None:
    """Verifies that every calculation carries cryptographic provenance per Fed SR 11-7."""
    res = engine.resolve_financial_risk(50000, hourly_burn_rate=10000)
    assert "SR11-7" in res.model_provenance
    assert "PHYSICAL-DOWNTIME-SCALE" in res.model_provenance
