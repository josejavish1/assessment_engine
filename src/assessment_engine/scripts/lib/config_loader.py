"""Provides core logic and utilities for the Assessment Engine pipeline."""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ENGINE_CONFIG_DIR = ROOT / "engine_config"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No existe: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_runtime_manifest() -> dict:
    """Load the runtime manifest from the engine's configuration directory."""
    return _load_json(ENGINE_CONFIG_DIR / "runtime_manifest.json")


def load_model_profiles() -> dict:
    """Load the model profiles configuration from the 'model_profiles.json' file."""
    return _load_json(ENGINE_CONFIG_DIR / "model_profiles.json")


def load_model_profile(profile_name: str) -> dict:
    """Load a model profile by name, applying an optional environment override.

    Retrieves a model configuration profile. This function supports overriding the
    'model' attribute within the profile via a specifically formatted environment
    variable. The variable name is constructed by prefixing
    `ASSESSMENT_MODEL_OVERRIDE_` to the `profile_name` after converting it to
    uppercase and replacing all non-alphanumeric characters with underscores.

    Args:
        profile_name: The identifier of the model profile to load.

    Returns:
        A copy of the model profile configuration as a dictionary. If the
        corresponding override environment variable is set and non-empty, the
        'model' attribute in the returned dictionary is replaced with its value.

    Raises:
        KeyError: If the specified `profile_name` does not exist in the
            loaded model profiles.
    """
    data = load_model_profiles()
    profiles = data.get("profiles", {})
    if profile_name not in profiles:
        raise KeyError(f"Perfil de modelo no encontrado: {profile_name}")
    profile = dict(profiles[profile_name])
    override_env_name = "ASSESSMENT_MODEL_OVERRIDE_" + re.sub(
        r"[^A-Z0-9]+", "_", profile_name.upper()
    ).strip("_")
    override_model = os.environ.get(override_env_name, "").strip()
    if override_model:
        profile["model"] = override_model
    return profile


def load_document_profile(profile_name: str) -> dict:
    """Load a document profile configuration from a JSON file by profile name."""
    return _load_json(ENGINE_CONFIG_DIR / "document_profiles" / f"{profile_name}.json")


def load_policy_file(file_name: str) -> dict:
    """Load and parse a policy configuration file from the policies directory."""
    return _load_json(ENGINE_CONFIG_DIR / "policies" / f"{file_name}.json")


def load_target_maturity_policy() -> dict:
    """Load and parse the 'target_maturity_policy' configuration file."""
    return load_policy_file("target_maturity_policy")


def load_review_policy() -> dict:
    """Load the review policy configuration."""
    return load_policy_file("review_policy")


def resolve_model_profile_for_role(role_name: str) -> dict:
    """Resolves and loads the model profile configuration for a specified role.

    This function retrieves the runtime manifest to identify the model profile name
    associated with a given `role_name`. It then loads and returns the
    contents of that specific model profile configuration. The runtime manifest
    is expected to contain a 'model_profiles' key, which maps role names to
    their corresponding profile names.

    Args:
        role_name: The identifier for the role whose model profile is to be
            resolved and loaded.

    Returns:
        A dictionary representing the loaded model profile configuration.

    Raises:
        KeyError: If the `role_name` is not found within the 'model_profiles'
            section of the runtime manifest.
    """
    manifest = load_runtime_manifest()
    model_profiles = manifest.get("model_profiles", {})
    profile_name = model_profiles.get(role_name)
    if not profile_name:
        raise KeyError(f"No hay perfil de modelo configurado para el rol: {role_name}")
    return load_model_profile(profile_name)


def resolve_document_profile() -> dict:
    """Load the document profile configuration specified by the runtime manifest.

    This function orchestrates the loading of a document profile by first parsing
    the runtime manifest to identify the active profile name. It then proceeds to
    load and return the configuration dictionary for that specific profile.

    Returns:
        A dictionary representing the resolved document profile configuration.

    Raises:
        KeyError: If the 'document_profile' key is missing from the runtime
            manifest or its value is empty.
        FileNotFoundError: If the runtime manifest file or the specified document
            profile file cannot be found.
    """
    manifest = load_runtime_manifest()
    profile_name = manifest.get("document_profile")
    if not profile_name:
        raise KeyError("No hay document_profile en runtime_manifest.json")
    return load_document_profile(profile_name)


def resolve_target_maturity_defaults(document_profile_id: str) -> dict:
    """Retrieves the default target maturity configuration for a document profile.

    This function loads the global target maturity policy, accesses the 'defaults'
    section, and extracts the configuration corresponding to the provided profile ID.

    Args:
        document_profile_id: The unique identifier for the document profile.

    Returns:
        A dictionary containing the default target maturity settings for the
        specified profile.

    Raises:
        KeyError: If a default configuration for the specified
            `document_profile_id` does not exist in the policy.
    """
    policy = load_target_maturity_policy()
    defaults = policy.get("defaults", {})
    if document_profile_id not in defaults:
        raise KeyError(
            f"No hay defaults de target maturity para: {document_profile_id}"
        )
    return defaults[document_profile_id]


def resolve_review_rules() -> dict:
    """Resolve and return the review rules from the main policy configuration."""
    policy = load_review_policy()
    return policy.get("rules", {})
