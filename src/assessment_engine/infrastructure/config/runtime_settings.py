"""
Centralized Runtime Settings & Environment Configuration (Tier-1 SOTA).
Eliminates scattered magic numbers, hardcoded ports, and unconfigurable timeouts.
Provides type-safe, validated configuration with environment variable overrides.
"""
from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, Field
from assessment_engine.infrastructure.genai_client import ModelTier, get_model
from assessment_engine.infrastructure.primitives.security import resolve_secret


class ServerSettings(BaseModel):
    """Configure control plane and proxy server settings."""
    host: str = Field(default="0.0.0.0", description="Host de escucha del servidor")
    port: int = Field(default=8000, ge=1, le=65535, description="Puerto TCP del servidor de control plane")
    public_ip: str = Field(default="127.0.0.1", description="IP pública oficial para callbacks")


class CloudSettings(BaseModel):
    """Configure Google Cloud and Gemini models."""
    project_id: str = Field(default="sub403o4u0q5", description="ID de proyecto de Google Cloud")
    location: str = Field(default="us-central1", description="Región principal de Vertex AI")
    flash_model: str = Field(default_factory=lambda: get_model(ModelTier.FAST), description="Modelo rápido para scouting y tareas frecuentes")
    pro_model: str = Field(default_factory=lambda: get_model(ModelTier.REASONING), description="Modelo arquitectónico de razonamiento profundo")


class FactorySettings(BaseModel):
    """Configure FinOps limits, quotas, and factory sandboxing."""
    exec_timeout: int = Field(default=180, ge=1, description="Timeout en segundos para ejecución en Bubblewrap")
    max_cycles: int = Field(default=5, ge=1, description="Número máximo de ciclos de iteración autónoma")
    max_cost_usd: float = Field(default=1.0, ge=0.0, description="Presupuesto FinOps máximo en USD por ejecución")
    max_tokens: int = Field(default=300000, ge=1000, description="Límite máximo de tokens de contexto")
    max_wall_time_seconds: int = Field(default=600, ge=10, description="Tiempo máximo de reloj en segundos")
    max_file_read_bytes: int = Field(default=35000, ge=1024, description="Límite de lectura de archivos sin truncado")
    max_repo_map_chars: int = Field(default=12000, ge=1024, description="Límite de caracteres para el mapa de símbolos AST")


class DatabaseSettings(BaseModel):
    """Configure high-performance SQLite WAL tuning."""
    busy_timeout_ms: int = Field(default=5000, ge=100, description="PRAGMA busy_timeout en milisegundos")
    mmap_size_bytes: int = Field(default=268435456, ge=0, description="PRAGMA mmap_size (256 MB para lecturas en RAM)")
    cache_size_kb: int = Field(default=64000, ge=1000, description="PRAGMA cache_size en páginas (64 MB)")


class SecuritySettings(BaseModel):
    """Define master keys and cryptographic derivation secrets."""
    csrf_secret: str = Field(default_factory=lambda: resolve_secret("CSRF_SECRET_KEY"), min_length=16)
    encryption_secret: str = Field(default_factory=lambda: resolve_secret("MASTER_ENCRYPTION_SECRET"), min_length=16)


class CompanionEngineSettings(BaseModel):
    """Configure companion engines (Meilisearch, etc.)."""
    meili_http_addr: str = Field(default="127.0.0.1:7700")
    meili_master_key: str = Field(default_factory=lambda: resolve_secret("MEILI_MASTER_KEY", 16), min_length=8)


class RuntimeSettings(BaseModel):
    """
    Único Punto de Verdad (Single Source of Truth) para la configuración del sistema.
    Carga de forma determinista desde variables de entorno con fallbacks robustos.
    """
    server: ServerSettings = Field(default_factory=ServerSettings)
    cloud: CloudSettings = Field(default_factory=CloudSettings)
    factory: FactorySettings = Field(default_factory=FactorySettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    companion: CompanionEngineSettings = Field(default_factory=CompanionEngineSettings)

    @classmethod
    def load_from_env(cls) -> RuntimeSettings:
        """Load configuration by inspecting active environment variables."""
        server_port_raw = os.environ.get("CONTROL_PLANE_PORT", os.environ.get("PORT", "8000"))
        try:
            server_port = int(server_port_raw)
        except ValueError:
            server_port = 8000

        server_conf = ServerSettings(
            host=os.environ.get("CONTROL_PLANE_HOST", "0.0.0.0"),
            port=server_port,
            public_ip=os.environ.get("SERVER_PUBLIC_IP", "127.0.0.1")
        )

        cloud_conf = CloudSettings(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("GCP_PROJECT_ID", "sub403o4u0q5")),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", os.environ.get("GCP_LOCATION", "us-central1")),
            flash_model=get_model(ModelTier.FAST),
            pro_model=get_model(ModelTier.REASONING)
        )

        factory_conf = FactorySettings(
            exec_timeout=int(os.environ.get("FACTORY_EXEC_TIMEOUT", "180")),
            max_cycles=int(os.environ.get("FACTORY_MAX_CYCLES", "5")),
            max_cost_usd=float(os.environ.get("FACTORY_MAX_COST_USD", "1.0")),
            max_tokens=int(os.environ.get("FACTORY_MAX_TOKENS", "300000")),
            max_wall_time_seconds=int(os.environ.get("FACTORY_MAX_WALL_TIME", "600")),
            max_file_read_bytes=int(os.environ.get("FACTORY_MAX_FILE_READ_BYTES", "35000")),
            max_repo_map_chars=int(os.environ.get("FACTORY_MAX_REPO_MAP_CHARS", "12000"))
        )

        db_conf = DatabaseSettings(
            busy_timeout_ms=int(os.environ.get("SQLITE_BUSY_TIMEOUT_MS", "5000")),
            mmap_size_bytes=int(os.environ.get("SQLITE_MMAP_SIZE_BYTES", "268435456")),
            cache_size_kb=int(os.environ.get("SQLITE_CACHE_SIZE_KB", "64000"))
        )

        sec_conf = SecuritySettings(
            csrf_secret=resolve_secret("CSRF_SECRET_KEY"),
            encryption_secret=resolve_secret("MASTER_ENCRYPTION_SECRET")
        )

        comp_conf = CompanionEngineSettings(
            meili_http_addr=os.environ.get("MEILI_HTTP_ADDR", "127.0.0.1:7700"),
            meili_master_key=resolve_secret("MEILI_MASTER_KEY", 16)
        )

        return cls(
            server=server_conf,
            cloud=cloud_conf,
            factory=factory_conf,
            database=db_conf,
            security=sec_conf,
            companion=comp_conf
        )


# Provide a preconfigured singleton ready for injection.
runtime_settings = RuntimeSettings.load_from_env()
