"""Infrastructure configuration loader with environment override support.

Loads external JSON configuration files from the configs/ directory
and provides typed accessors for localization vocabulary, model profiles,
document profiles, and review policies.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
import json
import logging
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any

from assessment_engine.core.errors import ConfigurationError
from assessment_engine.domain.models import (
    DocumentGenerationProfile,
    ModelRoutingConfig,
    ModelTier,
    TaxonomyCatalogConfig,
)
from assessment_engine.domain.taxonomy_resolver import (
    PureTaxonomyResolver,
    TaxonomyCatalogLoaderPort,
    TaxonomyConcept,
    normalize_taxonomy_catalog,
    register_taxonomy_catalog_loader,
)

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONFIGS_DIR = _REPO_ROOT / "configs"


def get_configs_dir() -> Path:
    """Return the canonical path to the configs directory."""
    override = os.environ.get("ASSESSMENT_CONFIGS_DIR")
    if override:
        return Path(override)
    return _CONFIGS_DIR


def _load_json_file(file_path: Path) -> dict[str, Any]:
    """Read and parse a JSON configuration file with error handling."""
    if not file_path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {file_path}",
            config_path=file_path,
        )
    try:
        with open(file_path, encoding="utf-8-sig") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ConfigurationError(
                    f"Expected JSON object at root of {file_path}",
                    config_path=file_path,
                )
            return data
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Invalid JSON in configuration file {file_path}: {exc}",
            config_path=file_path,
            cause=exc,
        ) from exc


@lru_cache(maxsize=8)
def load_localization_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load localization.json containing UI vocabulary and abbreviations."""
    path = config_path or (get_configs_dir() / "localization.json")
    return _load_json_file(path)


def resolve_localized_vocabulary(
    locale: str = "en",
    config_path: Path | None = None,
    synthesizer: Any | None = None,
) -> dict[str, str]:
    """Resolve UI vocabulary for a target locale with English fallback.

    If the requested locale is not statically configured and a
    DynamicLocaleSynthesizer is available, dynamically synthesizes and caches
    the locale pack on the fly.
    """
    data = load_localization_config(config_path)
    locales = data.get("locales", {})
    en_vocab: dict[str, str] = dict(locales.get("en", {}))
    norm_locale = locale.lower().split("_")[0].split("-")[0]

    if norm_locale in locales:
        target_vocab = locales.get(norm_locale, {})
        merged = dict(en_vocab)
        merged.update(target_vocab)
        return merged

    # Dynamic synthesis fallback for unconfigured locales (e.g., fr, pt, de, it, ja)
    if norm_locale != "en":
        try:
            if synthesizer is None:
                from assessment_engine.infrastructure.locale_synthesizer import (
                    DynamicLocaleSynthesizer,
                )

                synthesizer = DynamicLocaleSynthesizer()
            return synthesizer.resolve_vocabulary(
                locale=norm_locale, base_en_vocab=en_vocab
            )
        except Exception as exc:
            logger.warning(
                "Dynamic locale synthesis failed for '%s': %s. Using English fallback.",
                norm_locale,
                exc,
            )

    return en_vocab


def load_abbreviations_glossary(config_path: Path | None = None) -> dict[str, str]:
    """Load standard technical abbreviations dictionary from localization.json."""
    data = load_localization_config(config_path)
    abbreviations: dict[str, str] = data.get("abbreviations", {})
    return dict(abbreviations)


def get_consultant_company_name(config_path: Path | None = None) -> str:
    """Retrieve the configured consultant company name."""
    data = load_localization_config(config_path)
    return str(data.get("consultant_company", "Enterprise Architecture Advisory"))


def get_localized_disclaimer(
    locale: str = "en", config_path: Path | None = None
) -> str:
    """Retrieve localized legal and methodological disclaimer."""
    data = load_localization_config(config_path)
    disclaimers = data.get("disclaimers", {})
    norm_locale = locale.lower().split("_")[0].split("-")[0]
    result = disclaimers.get(norm_locale) or disclaimers.get("en", "")
    return str(result)


@lru_cache(maxsize=8)
def load_model_profiles(config_path: Path | None = None) -> dict[str, Any]:
    """Load model_profiles.json containing LLM routing configurations."""
    path = config_path or (get_configs_dir() / "model_profiles.json")
    return _load_json_file(path)


def load_model_profile(
    profile_name: str | None = None,
    config_path: Path | None = None,
) -> ModelRoutingConfig:
    """Resolve a named model routing profile with environment variable overrides."""
    data = load_model_profiles(config_path)
    active_name = (
        profile_name
        or os.environ.get("ASSESSMENT_MODEL_PROFILE")
        or data.get("default_profile", "balanced")
    )
    profiles = data.get("profiles", {})
    if active_name not in profiles:
        raise ConfigurationError(
            f"Unknown model profile '{active_name}'. Available: {list(profiles.keys())}"
        )

    raw = dict(profiles[active_name])

    # Apply environment overrides per agent role if present
    role_env_map = {
        "principal_architect_model": "ASSESSMENT_MODEL_OVERRIDE_PRINCIPAL",
        "finops_economist_model": "ASSESSMENT_MODEL_OVERRIDE_FINOPS",
        "red_team_auditor_model": "ASSESSMENT_MODEL_OVERRIDE_AUDITOR",
        "executive_Ghostwriter_model": "ASSESSMENT_MODEL_OVERRIDE_GHOSTWRITER",
        "diagram_architect_model": "ASSESSMENT_MODEL_OVERRIDE_DIAGRAM",
    }
    for field_key, env_var in role_env_map.items():
        env_val = os.environ.get(env_var)
        if env_val:
            raw[field_key] = env_val
            logger.info("Overriding %s with %s=%s", field_key, env_var, env_val)

    tier_str = raw.get("tier", active_name)
    try:
        tier = ModelTier(tier_str)
    except ValueError:
        tier = ModelTier.BALANCED

    return ModelRoutingConfig(
        profile_name=active_name,
        tier=tier,
        principal_architect_model=raw["principal_architect_model"],
        finops_economist_model=raw["finops_economist_model"],
        red_team_auditor_model=raw["red_team_auditor_model"],
        executive_Ghostwriter_model=raw["executive_Ghostwriter_model"],
        diagram_architect_model=raw["diagram_architect_model"],
        fallback_model=raw["fallback_model"],
        temperature=float(raw.get("temperature", 0.1)),
        max_output_tokens=int(raw.get("max_output_tokens", 8192)),
    )


@lru_cache(maxsize=8)
def load_document_profiles(config_path: Path | None = None) -> dict[str, Any]:
    """Load document_profiles.json containing generation depth profiles."""
    path = config_path or (get_configs_dir() / "document_profiles.json")
    return _load_json_file(path)


def load_document_profile(
    profile_name: str | None = None,
    config_path: Path | None = None,
) -> DocumentGenerationProfile:
    """Resolve a named document generation profile."""
    data = load_document_profiles(config_path)
    active_name = (
        profile_name
        or os.environ.get("ASSESSMENT_DOCUMENT_PROFILE")
        or data.get("default_profile", "full")
    )
    profiles = data.get("profiles", {})
    if active_name not in profiles:
        raise ConfigurationError(
            f"Unknown document profile '{active_name}'. Available: {list(profiles.keys())}"
        )
    raw = dict(profiles[active_name])
    raw["profile_name"] = active_name
    return DocumentGenerationProfile.model_validate(raw)


@lru_cache(maxsize=16)
def load_policy_file(
    policy_filename: str, config_path: Path | None = None
) -> dict[str, Any]:
    """Load a policy JSON file from configs/policies/."""
    path = config_path or (get_configs_dir() / "policies" / policy_filename)
    return _load_json_file(path)


def load_review_policy(config_path: Path | None = None) -> dict[str, Any]:
    """Load review_policy.json containing Red Team auditor quality gates."""
    return load_policy_file("review_policy.json", config_path)


def load_target_maturity_policy(config_path: Path | None = None) -> dict[str, Any]:
    """Load target_maturity.json containing benchmark targets."""
    return load_policy_file("target_maturity.json", config_path)


def resolve_model_profile_for_role(
    profile_name: str = "balanced",
    config_path: Path | None = None,
) -> ModelRoutingConfig:
    """Backward-compatible alias for load_model_profile."""
    return load_model_profile(profile_name=profile_name, config_path=config_path)


def resolve_model_for_role(
    role: str,
    profile_name: str = "balanced",
    config_path: Path | None = None,
) -> str:
    """Resolve the specific LLM model identifier assigned to a given agent role."""
    routing = load_model_profile(profile_name=profile_name, config_path=config_path)
    role_map = {
        "principal_architect": routing.principal_architect_model,
        "finops_economist": routing.finops_economist_model,
        "red_team_auditor": routing.red_team_auditor_model,
        "executive_ghostwriter": routing.executive_Ghostwriter_model,
        "diagram_architect": routing.diagram_architect_model,
        "fallback": routing.fallback_model,
    }
    norm_role = role.strip().lower()
    return role_map.get(norm_role, routing.principal_architect_model)


def resolve_document_profile(
    profile_name: str = "full",
    config_path: Path | None = None,
) -> DocumentGenerationProfile:
    """Backward-compatible alias for load_document_profile."""
    return load_document_profile(profile_name=profile_name, config_path=config_path)


@lru_cache(maxsize=8)
def load_rate_card(config_path: Path | None = None) -> dict[str, Any]:
    """Load rate_cards.json containing FinOps regional day rates and multipliers."""
    path = config_path or (get_configs_dir() / "rate_cards.json")
    return _load_json_file(path)


@lru_cache(maxsize=8)
def load_taxonomy_catalog(config_path: Path | None = None) -> TaxonomyCatalogConfig:
    """Load and validate taxonomy_catalog.json containing authoritative tower/pillar definitions."""
    path = config_path or (get_configs_dir() / "taxonomy_catalog.json")
    raw = _load_json_file(path)
    return TaxonomyCatalogConfig.model_validate(raw)


@lru_cache(maxsize=8)
def load_strategic_programs(config_path: Path | None = None) -> dict[str, Any]:
    """Load strategic_programs.json containing canonical remediation programs and keyword mappings."""
    return load_policy_file("strategic_programs.json", config_path)


def resolve_canonical_program_id(
    tower_id: str,
    gap_text: str = "",
    config_path: Path | None = None,
) -> str:
    """Deterministically resolve a canonical strategic program ID from tower and gap description."""
    data = load_strategic_programs(config_path)
    keyword_routes: list[dict[str, Any]] = data.get("keyword_routing", [])
    tower_defaults: dict[str, str] = data.get("tower_defaults", {})
    fallback_program: str = str(data.get("fallback_program_id", "PROG-FOUNDATION"))

    norm_text = gap_text.lower()
    norm_tower = tower_id.strip().upper()

    for route in keyword_routes:
        keywords = route.get("keywords", [])
        target_prog = route.get("program_id", "")
        if target_prog and any(kw.lower() in norm_text for kw in keywords):
            return str(target_prog)

    return str(tower_defaults.get(norm_tower, fallback_program))


def _load_raw_taxonomy_multilingual_towers(
    config_path: Path | None = None,
) -> Mapping[str, Any]:
    """Read raw towers mapping from taxonomy_multilingual.json without mutability leaks."""
    path = config_path or (get_configs_dir() / "taxonomy_multilingual.json")
    if not path.exists():
        logger.warning(
            "Multilingual taxonomy file not found at %s; using empty taxonomy catalog.",
            path,
        )
        return MappingProxyType({})
    data = _load_json_file(path)
    towers = data.get("towers", data)
    if not isinstance(towers, Mapping):
        return MappingProxyType({})
    return MappingProxyType(dict(towers))


def load_taxonomy_multilingual(config_path: Path | None = None) -> dict[str, Any]:
    """Load taxonomy_multilingual.json and return a fresh dictionary copy of tower definitions."""
    concepts = load_default_taxonomy_catalog(config_path)
    return {tid: concept.to_raw_dict() for tid, concept in concepts.items()}


@lru_cache(maxsize=8)
def load_default_taxonomy_catalog(
    config_path: Path | None = None,
) -> Mapping[str, TaxonomyConcept]:
    """Load and normalize the default multilingual taxonomy catalog into immutable TaxonomyConcepts."""
    raw_towers = _load_raw_taxonomy_multilingual_towers(config_path)
    concepts, _ = normalize_taxonomy_catalog(raw_towers)
    return concepts


class FileSystemTaxonomyCatalogLoader(TaxonomyCatalogLoaderPort):
    """Infrastructure adapter implementing TaxonomyCatalogLoaderPort via filesystem JSON config."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize loader with an optional explicit path to taxonomy_multilingual.json."""
        self._config_path = config_path

    def load_taxonomy_catalog(self) -> Mapping[str, TaxonomyConcept]:
        """Load and return an immutable mapping of tower IDs to TaxonomyConcept objects."""
        return load_default_taxonomy_catalog(self._config_path)


def create_taxonomy_resolver(
    config_path: Path | None = None,
) -> PureTaxonomyResolver:
    """Bootstrap a PureTaxonomyResolver injected with the filesystem taxonomy concept catalog."""
    catalog = load_default_taxonomy_catalog(config_path)
    return PureTaxonomyResolver(catalog=catalog)


# Register the default infrastructure catalog loader port at module bootstrap
register_taxonomy_catalog_loader(FileSystemTaxonomyCatalogLoader())
