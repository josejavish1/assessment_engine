"""
Módulo runtime_env.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
from __future__ import annotations

import os
from typing import Any


DEFAULT_GOOGLE_CLOUD_PROJECT = "sub403o4u0q5"
DEFAULT_GOOGLE_CLOUD_LOCATION = "europe-west1"
DEFAULT_VERTEX_PREFLIGHT_MODEL = "gemini-2.5-pro"
DEFAULT_VERTEX_PREFLIGHT_TIMEOUT_SECONDS = 20.0
DEFAULT_VERTEX_QUERY_TIMEOUT_SECONDS = 180.0


def ensure_google_cloud_env_defaults(
    env: dict[str, str] | None = None,
) -> dict[str, str] | None:
    target = os.environ if env is None else env
    target.setdefault("GOOGLE_CLOUD_PROJECT", DEFAULT_GOOGLE_CLOUD_PROJECT)
    target.setdefault("GOOGLE_CLOUD_LOCATION", DEFAULT_GOOGLE_CLOUD_LOCATION)
    return env


def get_google_cloud_project_location(
    env: dict[str, str] | None = None,
) -> tuple[str, str]:
    target = os.environ if env is None else env
    ensure_google_cloud_env_defaults(target)

    project = str(target.get("GOOGLE_CLOUD_PROJECT", "")).strip()
    location = str(target.get("GOOGLE_CLOUD_LOCATION", "")).strip()
    return project, location


def _read_positive_float_env(
    name: str,
    default: float,
    env: dict[str, str] | None = None,
) -> float:
    target = os.environ if env is None else env
    raw_value = str(target.get(name, default)).strip()
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} debe ser un número positivo. Valor recibido: {raw_value!r}"
        ) from exc

    if value <= 0:
        raise RuntimeError(f"{name} debe ser mayor que 0. Valor recibido: {raw_value!r}")

    return value


def get_vertex_preflight_timeout_seconds(
    env: dict[str, str] | None = None,
) -> float:
    return _read_positive_float_env(
        "ASSESSMENT_VERTEX_PREFLIGHT_TIMEOUT_SECONDS",
        DEFAULT_VERTEX_PREFLIGHT_TIMEOUT_SECONDS,
        env,
    )


def get_vertex_query_timeout_seconds(
    env: dict[str, str] | None = None,
) -> float:
    return _read_positive_float_env(
        "ASSESSMENT_VERTEX_QUERY_TIMEOUT_SECONDS",
        DEFAULT_VERTEX_QUERY_TIMEOUT_SECONDS,
        env,
    )


def run_vertex_ai_preflight(
    env: dict[str, str] | None = None,
    *,
    model_name: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    target = os.environ if env is None else env
    ensure_google_cloud_env_defaults(target)
    project, location = get_google_cloud_project_location(target)

    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT no está definido.")
    if not location:
        raise RuntimeError("GOOGLE_CLOUD_LOCATION no está definido.")

    resolved_model = (
        model_name
        or str(target.get("ASSESSMENT_VERTEX_PREFLIGHT_MODEL", "")).strip()
        or DEFAULT_VERTEX_PREFLIGHT_MODEL
    )
    resolved_timeout = timeout_seconds or get_vertex_preflight_timeout_seconds(target)

    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        from google.cloud.aiplatform_v1 import ModelGardenServiceClient
    except ImportError as exc:
        raise RuntimeError(
            "No se pudieron importar las dependencias de Vertex AI necesarias para el preflight."
        ) from exc

    try:
        credentials, detected_project = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(Request())

        client = ModelGardenServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
        location_name = f"projects/{project}/locations/{location}"
        client.get_location(
            request={"name": location_name},
            timeout=resolved_timeout,
        )

        publisher_model_name = client.publisher_model_path("google", resolved_model)
        client.get_publisher_model(
            name=publisher_model_name,
            timeout=resolved_timeout,
        )
    except Exception as exc:
        raise RuntimeError(
            "Vertex AI preflight failed "
            f"(project={project}, location={location}, model={resolved_model}): {exc}"
        ) from exc

    return {
        "project": project,
        "location": location,
        "detected_project": detected_project,
        "model": resolved_model,
        "publisher_model_name": publisher_model_name,
        "timeout_seconds": resolved_timeout,
    }
