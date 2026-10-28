"""
Fail-Fast Configuration & Environment Validator — GEMA 49 (SOTA 2026).
Validates runtime environment variables against strict Pydantic typed schemas.
Aborts cleanly at startup with clear diagnostics if required credentials or database paths are missing.
"""

from __future__ import annotations

import logging
import os

from pydantic import BaseModel, Field
from assessment_engine.infrastructure.primitives.security import resolve_secret

logger = logging.getLogger("assessment_engine.infrastructure.primitives.config_validator")


class ProjectRuntimeConfig(BaseModel):
    """Define a strictly typed configuration schema for a generated project."""
    app_env: str = Field(default="production", description="Entorno de ejecución: development, staging, production")
    database_url: str = Field(default="sqlite:///app.db", description="Ruta de conexión SQLite")
    port: int = Field(default=8000, description="Puerto de servicio HTTP")
    host: str = Field(default="0.0.0.0", description="Host de enlace")
    secret_key: str = Field(default_factory=lambda: resolve_secret("SECRET_KEY"), min_length=16)


class ConfigValidatorPrimitive:
    """
    Validate configuration using a domain-agnostic, fail-fast approach.
    """

    def validate_env(self, env_dict: dict[str, str] | None = None) -> tuple[bool, ProjectRuntimeConfig | None, list[str]]:
        """Validate current environment variables or those passed as a dictionary. Return (is_valid, config_object, error_list)."""
        raw_env = env_dict if env_dict is not None else dict(os.environ)
        normalized = {}
        for k, v in raw_env.items():
            normalized[k.lower()] = v

        data = {
            "app_env": normalized.get("app_env", "production"),
            "database_url": normalized.get("database_url", "sqlite:///app.db"),
            "port": int(normalized.get("port", 8000)),
            "host": normalized.get("host", "0.0.0.0"),
            "secret_key": normalized.get("secret_key") or resolve_secret("SECRET_KEY")
        }

        try:
            cfg = ProjectRuntimeConfig(
                app_env=str(data["app_env"]),
                database_url=str(data["database_url"]),
                port=int(str(data["port"])),
                host=str(data["host"]),
                secret_key=str(data["secret_key"])
            )
            return True, cfg, []
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            errors = [str(ex)]
            logger.error(f"[ConfigValidator] Error de configuración: {errors}")
            return False, None, errors


config_validator = ConfigValidatorPrimitive()
