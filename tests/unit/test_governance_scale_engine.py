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
    """Invariant: float sanitization via str representation prevents mantissa contamination."""
    res = sanitize_to_decimal(1.95)
    assert res == Decimal("1.9500")

    # Rejection of invalid reals
    with pytest.raises(ValueError, match="Invariant violation"):
        sanitize_to_decimal(-10.0)

    with pytest.raises(ValueError, match="Invalid numeric input"):
        sanitize_to_decimal("invalid_string")


def test_cmmi_half_open_interval_boundary_precision(engine: GovernanceScaleEngine) -> None:
    """Verifies strict half-open interval partitioning [a_k, a_{k+1}) for CMMI."""
    # Nivel 1: [0.00, 1.50)
    m0 = engine.resolve_maturity(0.00)
    assert m0.level == 1
    assert m0.band_code == MaturityBandCode.INITIAL

    m1_49 = engine.resolve_maturity(1.49)
    assert m1_49.level == 1
    assert m1_49.band_code == MaturityBandCode.INITIAL

    # Exact boundary 1.50 -> Nivel 2
    m1_50 = engine.resolve_maturity(1.50)
    assert m1_50.level == 2
    assert m1_50.band_code == MaturityBandCode.REPEATABLE
    assert m1_50.label == "Gestionado"

    # The infamous 1.84 case -> Nivel 2, NEVER Nivel 4!
    m1_84 = engine.resolve_maturity(1.84)
    assert m1_84.level == 2
    assert m1_84.band_code == MaturityBandCode.REPEATABLE
    assert m1_84.display_tag == "Nivel 2 (Gestionado)"

    # Nivel 3: [2.50, 3.50)
    m2_49 = engine.resolve_maturity(2.49)
    assert m2_49.level == 2
    m2_50 = engine.resolve_maturity(2.50)
    assert m2_50.level == 3
    assert m2_50.label == "Definido"

    # The 2.55 case -> Nivel 3 unassailable
    m2_55 = engine.resolve_maturity(2.55)
    assert m2_55.level == 3

    # Nivel 4: [3.50, 4.50)
    m3_50 = engine.resolve_maturity(3.50)
    assert m3_50.level == 4
    assert m3_50.label == "Gestionado Cuantitativamente"

    # The 4.25 case -> Nivel 4, NEVER Nivel 5!
    m4_25 = engine.resolve_maturity(4.25)
    assert m4_25.level == 4
    assert m4_25.band_code == MaturityBandCode.MANAGED
    assert m4_25.label == "Gestionado Cuantitativamente"

    # Nivel 5: [4.50, 5.00]
    m4_50 = engine.resolve_maturity(4.50)
    assert m4_50.level == 5
    assert m4_50.label == "Optimizado"

    m5_00 = engine.resolve_maturity(5.00)
    assert m5_00.level == 5


def test_open_fair_alometric_scaling_for_molins(engine: GovernanceScaleEngine) -> None:
    """Verifies that for Molins (1.144B EUR), Open FAIR thresholds match Table 8 exactly."""
    molins_rev = Decimal("1144000000.0")

    # 10,000 EUR -> LM 1 (Very Low / Muy Bajo)
    r1 = engine.resolve_financial_risk(10000, annual_revenue_eur=molins_rev)
    assert r1.open_fair_lm == "LM1"
    assert r1.severity == FinancialSeverityCode.LOW
    assert r1.label == "Muy Bajo"

    # 35,000 EUR -> LM 2 (Low / Bajo) - completely fixes the 35k split brain!
    r2 = engine.resolve_financial_risk(35000, annual_revenue_eur=molins_rev)
    assert r2.open_fair_lm == "LM2"
    assert r2.severity == FinancialSeverityCode.MODERATE
    assert r2.label == "Bajo"

    # 83,859 EUR (RVS10 in T2) -> LM 3 (Medium / Medio)
    r3 = engine.resolve_financial_risk(83859, annual_revenue_eur=molins_rev)
    assert r3.open_fair_lm == "LM3"
    assert r3.severity == FinancialSeverityCode.ELEVATED
    assert r3.label == "Medio"

    # 253,959 EUR (Tower 2 consolidated) -> LM 4 (High / Alto)
    r4 = engine.resolve_financial_risk(253959, annual_revenue_eur=molins_rev)
    assert r4.open_fair_lm == "LM4"
    assert r4.severity == FinancialSeverityCode.HIGH
    assert r4.label == "Alto"

    # 1,000,000 EUR -> LM 5 (Critical / Muy Alto)
    r5 = engine.resolve_financial_risk(1000000, annual_revenue_eur=molins_rev)
    assert r5.open_fair_lm == "LM5"
    assert r5.severity == FinancialSeverityCode.CRITICAL
    assert r5.label == "Muy Alto"


def test_alometric_sensitivity_for_small_firm(engine: GovernanceScaleEngine) -> None:
    """Verifies that an enterprise of 2M EUR perceives 35,000 EUR as a severe threat, not Low."""
    sme_rev = Decimal("2000000.0")

    # For an SME with 2M EUR turnover, 35k EUR is significant (ELEVATED or higher, not LM2 Low)
    r_sme = engine.resolve_financial_risk(35000, annual_revenue_eur=sme_rev)
    assert r_sme.open_fair_lm in ("LM3", "LM4"), "35k EUR must be classified as elevated or high for a 2M EUR firm"


def test_sr11_7_model_provenance_audit_trail(engine: GovernanceScaleEngine) -> None:
    """Verifies that every calculation carries cryptographic provenance per Fed SR 11-7."""
    res = engine.resolve_financial_risk(50000, annual_revenue_eur=100000000)
    assert "SR11-7" in res.model_provenance
    assert "ALOMETRIC-OFAIR-BETA0.75" in res.model_provenance
