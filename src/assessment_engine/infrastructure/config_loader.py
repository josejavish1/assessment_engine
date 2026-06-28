"""Implements the core logic and utility functions for the Assessment Engine pipeline."""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENGINE_CONFIG_DIR = ROOT / "engine_config"


from typing import Any, TypedDict


class ModelProfile(TypedDict):
    """TypedDict defining model configuration parameters like temperature and seed."""

    model: str
    temperature: float
    top_p: float
    seed: int
    max_output_tokens: int


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"No existe: {path}")
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_abbreviations_glossary() -> dict:
    """Load and parse the dynamic localized abbreviations glossary.

    Returns:
        The deserialized glossary terms dictionary.
    """
    return _load_json(ENGINE_CONFIG_DIR / "abbreviations_glossary.json")


def load_brand_profile() -> dict:
    """Load, parse, and normalize the corporate brand profile.

    Reads `brand_profile.json` and ensures color strings are normalized (removing
    any potential '#' prefix) to guarantee rendering safety in down-stream compilers.

    Returns:
        The normalized brand profile configuration dictionary.
    """
    data = _load_json(ENGINE_CONFIG_DIR / "brand_profile.json")
    styling = data.get("styling", {})
    if "primary_color_hex" in styling:
        styling["primary_color_hex"] = styling["primary_color_hex"].lstrip("#")
    if "alternate_row_color_hex" in styling:
        styling["alternate_row_color_hex"] = styling["alternate_row_color_hex"].lstrip(
            "#"
        )
    return data


def load_locales() -> dict:
    """Load and parse the dynamic localization strings file.

    Returns:
        The deserialized locales dictionary.
    """
    return _load_json(ENGINE_CONFIG_DIR / "locales.json")


def resolve_localized_vocabulary(lang: str) -> dict:
    """Resolves and returns the localized vocabulary terms for a given language.

    Falls back to Spanish ('es') if the requested language is not found.
    """
    locales = load_locales()
    lang_key = lang.lower() if lang else "es"
    return locales.get(lang_key, locales.get("es", {}))


def load_runtime_manifest() -> Any:
    """Load and parse the runtime manifest from its canonical location.

    The manifest, a file named `runtime_manifest.json`, is expected to reside in
    the engine's configuration directory (`ENGINE_CONFIG_DIR`). It contains
    metadata about the runtime environment and its components.

    Returns:
        The deserialized content of the runtime manifest. The specific type
        depends on the JSON document's root element, but is typically a dict.

    Raises:
        FileNotFoundError: If the manifest file cannot be found at the expected
            location.
        json.JSONDecodeError: If the manifest file contains malformed JSON.
    """
    return _load_json(ENGINE_CONFIG_DIR / "runtime_manifest.json")


def load_model_profiles() -> Any:
    """Load and parse the model profiles configuration file.

    This function locates and reads the `model_profiles.json` file from the
    engine's configuration directory and deserializes its JSON content.

    Returns:
        The deserialized JSON content of the `model_profiles.json` file.

    Raises:
        FileNotFoundError: If the `model_profiles.json` file cannot be found.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    return _load_json(ENGINE_CONFIG_DIR / "model_profiles.json")


def load_model_profile(profile_name: str) -> ModelProfile:
    """Loads a model configuration profile by name, with environment override support.

    Retrieves a specified model configuration profile and returns a mutable copy.
    This function supports dynamic overriding of the 'model' key within the
    profile via a corresponding environment variable.

    The environment variable name is constructed by prefixing the `profile_name`
    with `ASSESSMENT_MODEL_OVERRIDE_`, converting it to uppercase, and replacing
    all non-alphanumeric characters with underscores. For example, a profile
    named 'claude-3-sonnet' is overridden by the environment variable
    `ASSESSMENT_MODEL_OVERRIDE_CLAUDE_3_SONNET`.

    Args:
        profile_name (str): The name of the model profile to load.

    Returns:
        Dict[str, Any]: A mutable dictionary containing the configuration for the
            requested model profile. The 'model' key is replaced if a valid
            environment variable override exists.

    Raises:
        KeyError: If `profile_name` does not exist in the available profiles.
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
    """Load a document profile configuration by its profile name."""
    return _load_json(ENGINE_CONFIG_DIR / "document_profiles" / f"{profile_name}.json")


def load_policy_file(file_name: str) -> dict:
    """Load a policy configuration file by its base name from the policies directory."""
    return _load_json(ENGINE_CONFIG_DIR / "policies" / f"{file_name}.json")


def load_target_maturity_policy() -> dict:
    """Load the 'target_maturity_policy' configuration file."""
    return load_policy_file("target_maturity_policy")


def load_review_policy() -> dict:
    """Load the 'review_policy' configuration."""
    return load_policy_file("review_policy")


def resolve_model_profile_for_role(role_name: str) -> ModelProfile:
    """Resolve and load the model profile configuration for a specified role.

    Loads the runtime manifest to identify the model profile name associated
    with the given `role_name`. It then loads and returns the contents of that
    specific model profile configuration file.

    Args:
        role_name (str): The identifier for the role whose model profile is to be
            resolved and loaded.

    Returns:
        ModelProfile: The configuration dictionary loaded from the model profile file.

    Raises:
        KeyError: If the provided `role_name` does not map to a configured
            model profile in the runtime manifest.
        FileNotFoundError: If the runtime manifest file or the resolved model
            profile file cannot be located on the filesystem.
    """
    manifest = load_runtime_manifest()
    model_profiles = manifest.get("model_profiles", {})
    profile_name = model_profiles.get(role_name)
    if not profile_name:
        raise KeyError(f"No hay perfil de modelo configurado para el rol: {role_name}")
    return load_model_profile(profile_name)


def resolve_document_profile() -> dict:
    """Loads the document profile specified in the runtime manifest.

    This function retrieves the active document profile name from the runtime
    manifest and uses it to load the corresponding profile configuration.

    Returns:
        dict: The configuration dictionary of the resolved document profile.

    Raises:
        KeyError: If the 'document_profile' key is missing from the runtime
            manifest or its value is empty.
    """
    manifest = load_runtime_manifest()
    profile_name = manifest.get("document_profile")
    if not profile_name:
        raise KeyError("No hay document_profile en runtime_manifest.json")
    return load_document_profile(profile_name)


def resolve_target_maturity_defaults(document_profile_id: str) -> dict:
    """Resolves the default target maturity configuration for a specified document profile.

    This function loads the global target maturity policy via the
    `load_target_maturity_policy()` helper. It then accesses the 'defaults'
    section of the policy and retrieves the configuration dictionary
    corresponding to the given `document_profile_id`.

    Args:
        document_profile_id: The unique identifier for the document profile,
            used as the key for the lookup within the 'defaults' policy section.

    Returns:
        A dictionary containing the default target maturity settings.

    Raises:
        KeyError: If the 'defaults' section of the loaded policy does not
            contain an entry for the provided `document_profile_id`.
    """
    policy = load_target_maturity_policy()
    defaults = policy.get("defaults", {})
    if document_profile_id not in defaults:
        raise KeyError(
            f"No hay defaults de target maturity para: {document_profile_id}"
        )
    return defaults[document_profile_id]


def resolve_review_rules() -> dict:
    """{'docstring': "Extract the 'rules' dictionary from the main review policy configuration."}."""
    policy = load_review_policy()
    return policy.get("rules", {})


def load_rate_card() -> dict:
    """Load and parse the dynamic rate card parameters.

    Returns:
        The deserialized rate card dictionary.
    """
    return _load_json(ENGINE_CONFIG_DIR / "rate_card.json")


def load_industry_profile(profile_key: str) -> dict:
    """Load and parse an industry-specific configuration profile with automatic fallback to 'default'.

    Guarantees absolute path resolution to support execution from any directory context.

    Returns:
        The deserialized industry profile dictionary.
    """
    key = str(profile_key or "default").replace(".json", "").strip().lower()
    profile_file = ENGINE_CONFIG_DIR / "industry_profiles" / f"{key}.json"

    # Robust fallback handling (Technical Debt / Backward Compatibility)
    try:
        if not profile_file.exists():
            profile_file = ENGINE_CONFIG_DIR / "industry_profiles" / "default.json"
        return _load_json(profile_file)
    except Exception:
        # Fallback to default.json if the custom profile is corrupt/malformed on disk
        default_file = ENGINE_CONFIG_DIR / "industry_profiles" / "default.json"
        try:
            return _load_json(default_file)
        except Exception:
            raise KeyError(
                "No se pudo cargar el perfil de industria por defecto o se encuentra corrupto."
            )


def load_framework_rubric(framework_id: str) -> dict:
    """Load and parse a dynamic RAGE framework evaluation rubric by its ID.

    Guarantees absolute path resolution to support execution from any directory context.

    Returns:
        The deserialized framework rubric dictionary.
    """
    key = str(framework_id or "").strip().lower()
    rubric_file = ENGINE_CONFIG_DIR / "frameworks" / f"{key}.json"
    return _load_json(rubric_file)
