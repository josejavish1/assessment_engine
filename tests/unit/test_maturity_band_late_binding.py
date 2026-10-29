import pytest

from assessment_engine.application.run_executive_annex_synthesizer import (
    derive_maturity_band,
)
from assessment_engine.domain.maturity_band import (
    ANNEX_MATURITY_BANDS,
    resolve_maturity_band,
)


def test_resolve_maturity_band_late_binding_tokens():
    """Verify that resolve_maturity_band returns immutable semantic tokens (band_key)
    and resolves localized labels via late-binding against locales.json."""
    # 1. Default (no locale specified -> universal baseline English)
    res_default = resolve_maturity_band(4.0, ANNEX_MATURITY_BANDS)
    assert res_default["band_key"] == "band_managed"
    assert res_default["label"] == "Managed"

    # 2. Spanish locale -> Spanish labels
    res_es = resolve_maturity_band(4.0, ANNEX_MATURITY_BANDS, locale="es")
    assert res_es["band_key"] == "band_managed"
    assert res_es["label"] == "Gestionado"

    # 3. English locale -> English labels
    res_en = resolve_maturity_band(4.0, ANNEX_MATURITY_BANDS, locale="en")
    assert res_en["band_key"] == "band_managed"
    assert res_en["label"] == "Managed"

    # 4. Initial level in English
    res_initial_en = resolve_maturity_band(1.2, ANNEX_MATURITY_BANDS, locale="en")
    assert res_initial_en["band_key"] == "band_initial"
    assert res_initial_en["label"] == "Initial"

    # 5. Optimized level in English
    res_opt_en = resolve_maturity_band(4.8, ANNEX_MATURITY_BANDS, locale="en")
    assert res_opt_en["band_key"] == "band_optimized"
    assert res_opt_en["label"] == "Optimized"


def test_derive_maturity_band_bilingual():
    """Verify that derive_maturity_band supports bilingual resolution while preserving backwards compatibility."""
    assert derive_maturity_band(4.0) == "Managed"
    assert derive_maturity_band(4.0, locale="es") == "Gestionado"
    assert derive_maturity_band(4.0, locale="en") == "Managed"
    assert derive_maturity_band(1.0, locale="en") == "Initial"
    assert derive_maturity_band(1.0, locale="es") == "Inicial"
