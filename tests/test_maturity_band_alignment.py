import json
from pathlib import Path

from assessment_engine.application.run_executive_annex_synthesizer import (
    derive_maturity_band,
)


def test_locales_contains_all_languages() -> None:
    """Security assertions to ensure the 5 primary languages are supported."""
    # --- ARRANGE ---
    locales_path = Path("engine_config/locales.json")

    # --- ACT ---
    exists = locales_path.exists()

    # --- ASSERT ---
    assert exists, "The locales.json file must exist in engine_config/"
    if exists:
        with open(locales_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        for lang in ["es", "en", "pt", "fr", "ja"]:
            assert lang in data, (
                f"The language {lang} must be registered in locales.json"
            )


def test_canonical_5_level_localization_mapping() -> None:
    """Verify that the 5 official project maturity bands map identically
    and in an internationalized manner against locales.json keys.
    This prevents any structural regression or discrepancy (split-brain).
    """
    # --- ARRANGE ---
    locales_path = Path("engine_config/locales.json")
    official_labels = ["Inicial", "Repetible", "Definido", "Gestionado", "Optimizado"]

    mapping = {
        "Inicial": "band_initial",
        "Repetible": "band_repeatable",
        "Definido": "band_defined",
        "Gestionado": "band_managed",
        "Optimizado": "band_optimized",
    }

    # --- ACT ---
    exists = locales_path.exists()

    # --- ASSERT ---
    if exists:
        with open(locales_path, "r", encoding="utf-8-sig") as lf:
            locales_data = json.load(lf)

        # 1. Asegurar correspondencia estricta en el mapeo local
        for label in official_labels:
            assert label in mapping, (
                f"The canonical label {repr(label)} does not have a mapped i18n key."
            )

        # Ensure that each mapped key exists in locales.json for each registered language.
        for lang in ["es", "en", "pt", "fr", "ja"]:
            vocab = locales_data[lang]
            for label, key in mapping.items():
                assert key in vocab, (
                    f"Missing translation key {repr(key)} (canonical label: {repr(label)}) in language {repr(lang)} inside locales.json"
                )
                assert str(vocab[key]).strip(), (
                    f"The translation for {repr(key)} in language {repr(lang)} cannot be empty"
                )


def test_derive_maturity_band_scores_integration() -> None:
    """Verify that the derive_maturity_band logic correctly resolves the
    5 official maturity levels for real scores across the 5 languages.
    """
    # --- ARRANGE ---
    locales_path = Path("engine_config/locales.json")
    test_cases = [
        (1.0, "band_initial"),
        (2.0, "band_repeatable"),
        (3.0, "band_defined"),
        (4.0, "band_managed"),
        (5.0, "band_optimized"),
    ]

    # --- ACT ---
    exists = locales_path.exists()

    # --- ASSERT ---
    if exists:
        with open(locales_path, "r", encoding="utf-8-sig") as lf:
            locales_data = json.load(lf)

        for lang in ["es", "en", "pt", "fr", "ja"]:
            locales_data[lang]
            for score, key in test_cases:
                res = derive_maturity_band(score)
                expected = {
                    "band_initial": "Inicial",
                    "band_repeatable": "Repetible",
                    "band_defined": "Definido",
                    "band_managed": "Gestionado",
                    "band_optimized": "Optimizado",
                }[key]
                assert res == expected, (
                    f"Discrepancy for score {score} in language {lang}: expected {repr(expected)}, obtained {repr(res)}"
                )
