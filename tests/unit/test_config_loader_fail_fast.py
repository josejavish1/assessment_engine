# golden-path: ignore
"""Unit tests verifying fail-fast configuration error handling and typed exceptions."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from assessment_engine.infrastructure.config_loader import (
    _load_json,
    get_consultant_company_name,
    get_localized_disclaimer,
    load_industry_profile,
    load_model_profile,
    resolve_document_profile,
)
from assessment_engine.infrastructure.exceptions import (
    ConfigurationError,
    ConfigurationFileNotFoundError,
    ConfigurationKeyError,
    ConfigurationParseError,
)


def test_missing_file_raises_configuration_file_not_found(tmp_path: Path) -> None:
    missing_file = tmp_path / "non_existent.json"
    with pytest.raises(ConfigurationFileNotFoundError) as exc_info:
        _load_json(missing_file)

    # Invariant: Must also be a FileNotFoundError for backward compatibility
    assert isinstance(exc_info.value, FileNotFoundError)
    assert isinstance(exc_info.value, ConfigurationError)
    assert exc_info.value.error_code == "CONFIG_FILE_NOT_FOUND"


def test_malformed_json_raises_configuration_parse_error(tmp_path: Path) -> None:
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{invalid_json: 123", encoding="utf-8")

    with pytest.raises(ConfigurationParseError) as exc_info:
        _load_json(corrupt_file)

    assert exc_info.value.error_code == "CONFIG_PARSE_ERROR"
    assert "line" in exc_info.value.context


def test_missing_model_profile_raises_configuration_key_error() -> None:
    with pytest.raises(ConfigurationKeyError) as exc_info:
        load_model_profile("completely_unknown_profile_identifier")

    # Invariant: Must also be a KeyError for backward compatibility
    assert isinstance(exc_info.value, KeyError)
    assert exc_info.value.error_code == "CONFIG_KEY_MISSING"


def test_missing_document_profile_raises_configuration_key_error() -> None:
    with patch(
        "assessment_engine.infrastructure.config_loader.load_runtime_manifest",
        return_value={},
    ):
        with pytest.raises(ConfigurationKeyError) as exc_info:
            resolve_document_profile()

        assert isinstance(exc_info.value, KeyError)


def test_industry_profile_strict_mode_rejects_missing() -> None:
    with pytest.raises(ConfigurationFileNotFoundError):
        load_industry_profile("non_existent_strict_vertical", allow_fallback=False)


def test_industry_profile_strict_mode_rejects_corrupted() -> None:
    def mock_corrupt_json(path: Path):
        raise ConfigurationParseError(path, "Syntax error in industry profile")

    with patch(
        "assessment_engine.infrastructure.config_loader._load_json",
        side_effect=mock_corrupt_json,
    ):
        with pytest.raises(ConfigurationParseError):
            load_industry_profile("critical_infrastructure", allow_fallback=False)


def test_get_consultant_company_name_safe_default() -> None:
    with patch(
        "assessment_engine.infrastructure.config_loader.load_brand_profile",
        side_effect=ConfigurationFileNotFoundError(Path("dummy")),
    ):
        name = get_consultant_company_name(default="Enterprise Advisory")
        assert name == "Enterprise Advisory"


def test_get_localized_disclaimer_handles_missing_cleanly() -> None:
    with patch(
        "assessment_engine.infrastructure.config_loader.resolve_localized_vocabulary",
        side_effect=ConfigurationFileNotFoundError(Path("dummy")),
    ):
        disclaimer = get_localized_disclaimer(lang="unknown")
        assert disclaimer == ""
