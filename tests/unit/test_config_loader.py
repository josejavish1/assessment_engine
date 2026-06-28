# golden-path: ignore
from __future__ import annotations

import os

import pytest

from assessment_engine.infrastructure.config_loader import (
    load_abbreviations_glossary,
    load_brand_profile,
    load_framework_rubric,
    load_industry_profile,
    load_model_profile,
    load_rate_card,
    load_runtime_manifest,
    resolve_document_profile,
    resolve_localized_vocabulary,
    resolve_model_profile_for_role,
    resolve_review_rules,
    resolve_target_maturity_defaults,
)


def test_load_abbreviations_glossary() -> None:
    # --- ARRANGE & ACT ---
    glossary = load_abbreviations_glossary()

    # --- ASSERT ---
    assert isinstance(glossary, dict)
    assert len(glossary) > 0


def test_load_brand_profile() -> None:
    # --- ARRANGE & ACT ---
    brand = load_brand_profile()

    # --- ASSERT ---
    assert isinstance(brand, dict)
    assert "styling" in brand
    # Hex codes should be stripped of "#"
    assert not brand["styling"]["primary_color_hex"].startswith("#")


def test_resolve_localized_vocabulary() -> None:
    # --- ARRANGE, ACT & ASSERT ---
    # Test valid Spanish
    vocab_es = resolve_localized_vocabulary("es")
    assert "control_documental_title" in vocab_es

    # Test English
    vocab_en = resolve_localized_vocabulary("en")
    assert "control_documental_title" in vocab_en

    # Test fallback to Spanish
    vocab_fallback = resolve_localized_vocabulary("invalid_lang")
    assert "control_documental_title" in vocab_fallback


def test_load_runtime_manifest() -> None:
    # --- ARRANGE & ACT ---
    manifest = load_runtime_manifest()

    # --- ASSERT ---
    assert "document_profile" in manifest


def test_load_model_profile_and_overrides() -> None:
    # --- ARRANGE & ACT ---
    # Test standard profile load
    profile = load_model_profile("writer_fast")
    assert profile["model"] == "gemini-2.5-pro"

    # Test environment variable override
    os.environ["ASSESSMENT_MODEL_OVERRIDE_WRITER_FAST"] = "my-custom-model"
    try:
        profile_override = load_model_profile("writer_fast")
        assert profile_override["model"] == "my-custom-model"
    except Exception as e:
        pytest.fail(f"Overridden load_model_profile threw exception: {e}")
    finally:
        del os.environ["ASSESSMENT_MODEL_OVERRIDE_WRITER_FAST"]

    # Test error handling for missing profile name
    with pytest.raises(KeyError):
        load_model_profile("non_existent_profile_name")


def test_resolve_model_profile_for_role() -> None:
    # --- ARRANGE & ACT ---
    profile = resolve_model_profile_for_role("section_writer")

    # --- ASSERT ---
    assert isinstance(profile, dict)


def test_resolve_document_profile() -> None:
    # --- ARRANGE & ACT ---
    doc_profile = resolve_document_profile()

    # --- ASSERT ---
    assert isinstance(doc_profile, dict)


def test_resolve_target_maturity_defaults() -> None:
    # --- ARRANGE, ACT & ASSERT ---
    defaults = resolve_target_maturity_defaults("tower_annex_profile")
    assert isinstance(defaults, dict)

    with pytest.raises(KeyError):
        resolve_target_maturity_defaults("non_existent_profile")


def test_resolve_review_rules() -> None:
    # --- ARRANGE & ACT ---
    rules = resolve_review_rules()

    # --- ASSERT ---
    assert isinstance(rules, dict)


def test_load_rate_card() -> None:
    # --- ARRANGE & ACT ---
    rate_card = load_rate_card()

    # --- ASSERT ---
    assert isinstance(rate_card, dict)


def test_load_industry_profile_fallback() -> None:
    # --- ARRANGE, ACT & ASSERT ---
    # Test loading real profile
    profile = load_industry_profile("critical_infrastructure")
    assert "industry" in profile

    # Test fallback to default
    fallback_profile = load_industry_profile("non_existent_industry_profile_fuzzing")
    assert "industry" in fallback_profile


def test_load_framework_rubric() -> None:
    # --- ARRANGE & ACT ---
    rubric = load_framework_rubric("ens_alta")

    # --- ASSERT ---
    assert (
        rubric["framework_name"]
        == "Esquema Nacional de Seguridad (ENS) - Categoría Alta"
    )


def test_config_loader_edge_cases() -> None:
    """Verify that config_loader raises appropriate exceptions under error conditions."""
    from pathlib import Path
    from unittest.mock import patch

    from assessment_engine.infrastructure.config_loader import _load_json

    # 1. Test missing file raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        _load_json(Path("non_existent_json_file"))

    # 2. Test missing role name raises KeyError
    with pytest.raises(KeyError):
        resolve_model_profile_for_role("non_existent_role_under_test")

    # 3. Test missing document_profile key in manifest raises KeyError
    with patch(
        "assessment_engine.infrastructure.config_loader.load_runtime_manifest"
    ) as mock_manifest:
        mock_manifest.return_value = {}
        with pytest.raises(KeyError):
            resolve_document_profile()


def test_load_industry_profile_corrupted_fallback() -> None:
    """Verify that load_industry_profile falls back to default.json when the custom profile is corrupt/malformed."""
    import json
    from unittest.mock import patch

    from assessment_engine.infrastructure.config_loader import load_industry_profile

    # We patch _load_json to raise JSONDecodeError specifically for the custom profile
    def mock_load_json(path):
        if "custom_corrupted_profile" in str(path):
            raise json.JSONDecodeError("Expecting value", "doc", 0)
        # Call the original JSON loader by opening the file
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)

    with patch(
        "assessment_engine.infrastructure.config_loader._load_json",
        side_effect=mock_load_json,
    ):
        # --- ACT ---
        profile = load_industry_profile("custom_corrupted_profile")

        # --- ASSERT ---
        # It must successfully fallback to default.json
        assert "industry" in profile
        assert profile["industry"] == "Default / General Enterprise"
