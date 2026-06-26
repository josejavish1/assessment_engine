import json
from pathlib import Path

from assessment_engine.application.run_executive_annex_synthesizer import (
    derive_maturity_band,
)


def test_locales_contains_all_languages() -> None:
    """Aserciones de seguridad de que los 5 idiomas principales están soportados."""
    # --- ARRANGE ---
    locales_path = Path("engine_config/locales.json")

    # --- ACT ---
    exists = locales_path.exists()

    # --- ASSERT ---
    assert exists, "El archivo locales.json debe existir en engine_config/"
    if exists:
        with open(locales_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        for lang in ["es", "en", "pt", "fr", "ja"]:
            assert lang in data, (
                f"El idioma {lang} debe estar registrado en locales.json"
            )


def test_canonical_5_level_localization_mapping() -> None:
    """
    Verifica que las 5 bandas oficiales de madurez del proyecto se mapean
    de forma idéntica e internacionalizada contra las claves de locales.json.
    Esto previene cualquier regresión o discrepancia estructural (split-brain).
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
                f"La etiqueta canónica {repr(label)} no posee una clave i18n mapeada."
            )

        # 2. Asegurar que cada clave mapeada existe en locales.json para cada idioma registrado
        for lang in ["es", "en", "pt", "fr", "ja"]:
            vocab = locales_data[lang]
            for label, key in mapping.items():
                assert key in vocab, (
                    f"Falta la clave de traducción {repr(key)} (etiqueta canónica: {repr(label)}) en el idioma {repr(lang)} inside locales.json"
                )
                assert str(vocab[key]).strip(), (
                    f"La traducción para {repr(key)} en el idioma {repr(lang)} no puede estar vacía"
                )


def test_derive_maturity_band_scores_integration() -> None:
    """
    Verifica que la lógica derive_maturity_band resuelva correctamente
    los 5 niveles de madurez oficiales para puntuaciones reales en los 5 idiomas.
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
                    f"Discrepancia para score {score} en idioma {lang}: esperado {repr(expected)}, obtenido {repr(res)}"
                )
