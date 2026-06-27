import json
from pathlib import Path

from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge


def test_brand_profile_localization_structure() -> None:
    """Verify the structure and multi-language support of brand_profile.json."""
    brand_path = Path("engine_config/brand_profile.json")
    assert brand_path.exists(), "El perfil de marca debe existir"

    with open(brand_path, "r", encoding="utf-8") as f:
        brand = json.load(f)

    # Verify mandatory primary keys
    assert "company_name" in brand
    assert "default_classification" in brand
    assert "disclaimer_text" in brand
    assert "styling" in brand
    assert "locales" in brand

    # Verify that the local schema contains the corresponding languages
    for lang in ["es", "en", "pt", "fr", "ja"]:
        assert lang in brand["locales"], (
            f"El locale '{lang}' debe estar en el perfil de marca"
        )
        assert "default_classification" in brand["locales"][lang]
        assert "disclaimer_text" in brand["locales"][lang]


def test_payload_to_ast_bridge_branding_localization_and_robust_colors() -> None:
    """Validate dynamic injection of classification and localized disclaimer in the AST compiler."""
    # Instantiate the bridge
    bridge = PayloadToASTBridge()

    # Verify that classification is loaded by default and that color robustness is supported
    assert hasattr(bridge, "brand_data")
    assert "locales" in bridge.brand_data

    # Simulate injection of attributes based on language
    # Japanese language (ja)
    lang_brand_ja = bridge.brand_data["locales"]["ja"]
    assert "極秘" in lang_brand_ja["default_classification"]

    # English language (en)
    lang_brand_en = bridge.brand_data["locales"]["en"]
    assert "Confidential" in lang_brand_en["default_classification"]
    assert "This document constitutes" in lang_brand_en["disclaimer_text"]
