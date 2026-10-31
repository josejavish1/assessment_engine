"""Infrastructure-level exception hierarchy for the Assessment Engine.

Handles configuration loading, I/O faults, file access, and schema boundary validations.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from assessment_engine.domain.exceptions import AssessmentDomainError


class InfrastructureError(AssessmentDomainError):
    """Base exception for all infrastructure, I/O, and external system boundary faults."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "INFRASTRUCTURE_FAULT",
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, context=context)


class ConfigurationError(InfrastructureError):
    """Base class for all configuration resolution, loading, and validation failures."""

    def __init__(
        self,
        message: str,
        *,
        config_path: Path | None = None,
        error_code: str = "CONFIGURATION_ERROR",
        context: Mapping[str, Any] | None = None,
    ) -> None:
        merged_context: dict[str, Any] = dict(context) if context else {}
        if config_path is not None:
            merged_context["config_path"] = os.fspath(config_path)
        super().__init__(message, error_code=error_code, context=merged_context)
        self.config_path = config_path


class ConfigurationFileNotFoundError(ConfigurationError, FileNotFoundError):
    """Raised when a required configuration file cannot be found on disk."""

    def __init__(self, config_path: Path) -> None:
        super().__init__(
            f"Configuration file not found or inaccessible: '{config_path}'.",
            config_path=config_path,
            error_code="CONFIG_FILE_NOT_FOUND",
        )


class ConfigurationPermissionError(ConfigurationError, PermissionError):
    """Raised when the process lacks operating system permissions to read a configuration file."""

    def __init__(self, config_path: Path, os_error: str) -> None:
        super().__init__(
            f"Insufficient permissions to read configuration file: '{config_path}'.",
            config_path=config_path,
            error_code="CONFIG_PERMISSION_DENIED",
            context={"os_error": os_error},
        )


class ConfigurationParseError(ConfigurationError):
    """Raised when a configuration file contains malformed JSON or invalid byte sequences."""

    def __init__(
        self,
        config_path: Path,
        parse_details: str,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        context: dict[str, Any] = {"parse_details": parse_details}
        if line is not None:
            context["line"] = line
        if column is not None:
            context["column"] = column

        super().__init__(
            f"Failed to parse configuration file '{config_path}': {parse_details}",
            config_path=config_path,
            error_code="CONFIG_PARSE_ERROR",
            context=context,
        )


class ConfigurationSchemaError(ConfigurationError):
    """Raised when parsed configuration violates the structural or type contract."""

    def __init__(
        self,
        config_path: Path,
        validation_errors: list[dict[str, Any]],
    ) -> None:
        super().__init__(
            f"Configuration schema validation failed for '{config_path}' with {len(validation_errors)} error(s).",
            config_path=config_path,
            error_code="CONFIG_SCHEMA_VIOLATION",
            context={"validation_errors": validation_errors},
        )


class ConfigurationKeyError(ConfigurationError, KeyError):
    """Raised when a required key is missing from a configuration manifest or dictionary."""

    def __init__(self, key: str, config_name: str = "configuration") -> None:
        super().__init__(
            f"Required key '{key}' is missing from {config_name}.",
            error_code="CONFIG_KEY_MISSING",
            context={"missing_key": key, "config_name": config_name},
        )
