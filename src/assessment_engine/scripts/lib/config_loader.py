"""
Módulo config_loader.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

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
    return _load_json(ENGINE_CONFIG_DIR / "runtime_manifest.json")


def load_model_profiles() -> dict:
    return _load_json(ENGINE_CONFIG_DIR / "model_profiles.json")


def load_model_profile(profile_name: str) -> dict:
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
    return _load_json(ENGINE_CONFIG_DIR / "document_profiles" / f"{profile_name}.json")


def load_policy_file(file_name: str) -> dict:
    return _load_json(ENGINE_CONFIG_DIR / "policies" / f"{file_name}.json")


def load_target_maturity_policy() -> dict:
    return load_policy_file("target_maturity_policy")


def load_review_policy() -> dict:
    return load_policy_file("review_policy")


def resolve_model_profile_for_role(role_name: str) -> dict:
    manifest = load_runtime_manifest()
    model_profiles = manifest.get("model_profiles", {})
    profile_name = model_profiles.get(role_name)
    if not profile_name:
        raise KeyError(f"No hay perfil de modelo configurado para el rol: {role_name}")
    return load_model_profile(profile_name)


def resolve_document_profile() -> dict:
    manifest = load_runtime_manifest()
    profile_name = manifest.get("document_profile")
    if not profile_name:
        raise KeyError("No hay document_profile en runtime_manifest.json")
    return load_document_profile(profile_name)


def resolve_target_maturity_defaults(document_profile_id: str) -> dict:
    policy = load_target_maturity_policy()
    defaults = policy.get("defaults", {})
    if document_profile_id not in defaults:
        raise KeyError(
            f"No hay defaults de target maturity para: {document_profile_id}"
        )
    return defaults[document_profile_id]


def resolve_review_rules() -> dict:
    policy = load_review_policy()
    return policy.get("rules", {})
