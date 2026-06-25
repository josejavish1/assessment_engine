"""Provides core logic and utilities for the Assessment Engine pipeline execution environment."""

from __future__ import annotations

import os
from typing import Any

DEFAULT_GOOGLE_CLOUD_PROJECT = "sub403o4u0q5"
DEFAULT_GOOGLE_CLOUD_LOCATION = "europe-west1"
DEFAULT_VERTEX_PREFLIGHT_MODEL = "gemini-2.5-pro"
DEFAULT_VERTEX_PREFLIGHT_TIMEOUT_SECONDS = 20.0
DEFAULT_VERTEX_QUERY_TIMEOUT_SECONDS = 300.0


def ensure_google_cloud_env_defaults(
    env: dict[str, str] | None = None,
) -> dict[str, str] | None:
    """Ensure default Google Cloud environment variables are present in an environment.

    This function inspects a target environment for `GOOGLE_CLOUD_PROJECT` and
    `GOOGLE_CLOUD_LOCATION`. If either variable is absent, it is populated using
    module-level default constants. The modification is performed in-place.

    If `env` is None, the process's current environment (`os.environ`) is
    modified directly.

    Args:
        env: The dictionary of environment variables to modify. If `None`,
            `os.environ` is used as the target for modification.

    Returns:
        The original `env` object passed as an argument. Returns `None` if the
        input `env` was `None`, even though `os.environ` was modified in that
        case.
    """
    target = os.environ if env is None else env
    target.setdefault("GOOGLE_CLOUD_PROJECT", DEFAULT_GOOGLE_CLOUD_PROJECT)
    target.setdefault("GOOGLE_CLOUD_LOCATION", DEFAULT_GOOGLE_CLOUD_LOCATION)
    return env


def get_google_cloud_project_location(
    env: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Retrieve the Google Cloud project ID and location from an environment.

    Reads `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` from a specified
    environment dictionary, falling back to `os.environ` if one is not
    provided. Before reading, this function populates default values by calling
    `ensure_google_cloud_env_defaults`, which may modify the target
    environment in place.

    Args:
        env (dict[str, str] | None): The environment dictionary to query. If
            None, `os.environ` is used and may be modified. Defaults to None.

    Returns:
        tuple[str, str]: A tuple of (project, location). Values are stripped of
            leading/trailing whitespace and will be empty strings if the
            corresponding environment variables are not set.
    """
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
    """Return the Vertex AI preflight check timeout in seconds from the environment."""
    return _read_positive_float_env(
        "ASSESSMENT_VERTEX_PREFLIGHT_TIMEOUT_SECONDS",
        DEFAULT_VERTEX_PREFLIGHT_TIMEOUT_SECONDS,
        env,
    )


def get_vertex_query_timeout_seconds(
    env: dict[str, str] | None = None,
) -> float:
    """Return the configured timeout in seconds for Vertex AI queries."""
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
    """Perform a preflight check to verify Vertex AI connectivity and configuration.

    This function validates that the environment is correctly configured to
    communicate with Google Cloud Vertex AI. It authenticates using Application
    Default Credentials (ADC), verifies the specified project and location, and
    confirms that the requested publisher model is available in the Model Garden.

    Configuration is sourced with the following precedence:
    1.  Function arguments (`model_name`, `timeout_seconds`).
    2.  Environment variables (e.g., `GOOGLE_CLOUD_PROJECT`,
        `ASSESSMENT_VERTEX_PREFLIGHT_MODEL`).
    3.  Predefined default values.

    Args:
        env: A dictionary of environment variables for configuration. Defaults to
            `os.environ` if `None`.
        model_name: The model name to verify. Overrides the
            `ASSESSMENT_VERTEX_PREFLIGHT_MODEL` environment variable.
        timeout_seconds: Timeout in seconds for Vertex AI API requests. Overrides
            the value sourced from the environment.

    Returns:
        A dictionary containing the resolved and verified configuration:
          - project (str): The Google Cloud project ID.
          - location (str): The Google Cloud location/region.
          - detected_project (str | None): The project ID detected from ADC.
          - model (str): The resolved model name.
          - publisher_model_name (str): The full Vertex AI publisher model
              resource name.
          - timeout_seconds (float): The resolved timeout for API calls.

    Raises:
        RuntimeError: If essential configuration variables (`GOOGLE_CLOUD_PROJECT`,
            `GOOGLE_CLOUD_LOCATION`) are undefined, if required Google Cloud
            libraries cannot be imported, or if an API call to Vertex AI fails
            due to authentication errors, an invalid project/location, or a
            non-existent model.
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
