"""Provides the core logic and utility functions for the Assessment Engine's data processing pipeline."""

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
    """Set default Google Cloud environment variables if they are not present.

    Modifies a dictionary of environment variables in-place to ensure default
    values for `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` exist. This
    function uses `dict.setdefault` and will not overwrite existing values.

    If `env` is None, `os.environ` is modified directly.

    Args:
        env: The environment dictionary to modify. If None, `os.environ` is
            used as the target for modification.

    Returns:
        The original dictionary passed as the `env` argument, which has been
        modified. Returns None if the input `env` was None.
    """
    target = os.environ if env is None else env
    target.setdefault("GOOGLE_CLOUD_PROJECT", DEFAULT_GOOGLE_CLOUD_PROJECT)
    target.setdefault("GOOGLE_CLOUD_LOCATION", DEFAULT_GOOGLE_CLOUD_LOCATION)
    return env


def get_google_cloud_project_location(
    env: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Return the Google Cloud project and location from environment variables."""
    target = os.environ if env is None else env
    ensure_google_cloud_env_defaults(target)  # type: ignore

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
        raise RuntimeError(
            f"{name} debe ser mayor que 0. Valor recibido: {raw_value!r}"
        )

    return value


def get_vertex_preflight_timeout_seconds(
    env: dict[str, str] | None = None,
) -> float:
    """Get the timeout for the Vertex preflight check in seconds."""
    return _read_positive_float_env(
        "ASSESSMENT_VERTEX_PREFLIGHT_TIMEOUT_SECONDS",
        DEFAULT_VERTEX_PREFLIGHT_TIMEOUT_SECONDS,
        env,
    )


def get_vertex_query_timeout_seconds(
    env: dict[str, str] | None = None,
) -> float:
    """Return the Vertex AI query timeout in seconds from an environment variable."""
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
    """Perform a preflight check for Vertex AI connectivity and configuration.

    This function validates that the runtime environment can successfully communicate
    with Google Cloud Vertex AI services. It performs a sequence of checks:
    1.  Resolves the Google Cloud project and location from environment variables.
    2.  Verifies that the necessary Google Cloud client libraries are installed.
    3.  Attempts to authenticate using Application Default Credentials (ADC).
    4.  Contacts the Vertex AI API to validate the specified project and location.
    5.  Queries the Model Garden Service to ensure the target model is available.

    Args:
        env: A dictionary of environment variables to use for configuration. If
            None, `os.environ` is used as the source. Defaults to None.
        model_name: The name of the Vertex AI model to verify. The resolution
            order is: this argument, the `ASSESSMENT_VERTEX_PREFLIGHT_MODEL`
            environment variable, then a hardcoded default model.
        timeout_seconds: The timeout in seconds for individual API calls to Vertex
            AI. If not provided, a default value is resolved from the
            environment or a hardcoded fallback.

    Returns:
        A dictionary containing the resolved configuration from the successful
        preflight check, with the following keys:
            - project (str): The resolved Google Cloud project ID.
            - location (str): The resolved Google Cloud location (region).
            - detected_project (str): The project ID detected from credentials.
            - model (str): The resolved model name that was checked.
            - publisher_model_name (str): The full resource name of the model.
            - timeout_seconds (float): The timeout value used for API calls.

    Raises:
        RuntimeError: If any stage of the preflight check fails, including:
            - Missing `GOOGLE_CLOUD_PROJECT` or `GOOGLE_CLOUD_LOCATION`
              environment variables.
            - Failure to import the required `google-cloud-aiplatform` library.
            - Authentication failures via `google.auth.default`.
            - Any API-level error from Vertex AI, such as an invalid project,
              non-existent location, permission denied, or a model not found.
    """
    target = os.environ if env is None else env
    ensure_google_cloud_env_defaults(target)  # type: ignore
    project, location = get_google_cloud_project_location(target)  # type: ignore

    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT no está definido.")
    if not location:
        raise RuntimeError("GOOGLE_CLOUD_LOCATION no está definido.")

    resolved_model = (
        model_name
        or str(target.get("ASSESSMENT_VERTEX_PREFLIGHT_MODEL", "")).strip()
        or DEFAULT_VERTEX_PREFLIGHT_MODEL
    )
    resolved_timeout = timeout_seconds or get_vertex_preflight_timeout_seconds(target)  # type: ignore

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
