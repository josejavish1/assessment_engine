"""Jurisdictional Sovereignty Policy for the Sovereign Assessment Engine.

Maps client regulatory environments and country contexts to concrete territorial
architectural invariants, sovereign cloud stacks, and direct connectivity standards,
featuring Just-In-Time (JIT) dynamic synthesis and caching for unlisted jurisdictions.
"""
from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List

from pydantic import ValidationError

from assessment_engine.domain.schemas.jurisdiction import (
    JurisdictionSovereigntyProfile,
    JurisdictionalRegistry,
)
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = Path(
    os.environ.get(
        "SOVEREIGN_JURISDICTION_CONFIG_PATH",
        str(ROOT / "engine_config" / "policies" / "jurisdictional_sovereignty.json"),
    )
)
DYNAMIC_DIR = Path(
    os.environ.get(
        "SOVEREIGN_DYNAMIC_JURISDICTION_DIR",
        str(ROOT / "engine_config" / "policies" / "jurisdictions_dynamic"),
    )
)
JIT_PROMPT_PATH = Path(
    os.environ.get(
        "SOVEREIGN_JIT_PROMPT_PATH",
        str(ROOT / "engine_config" / "prompts" / "jurisdiction_jit_synthesis.txt"),
    )
)

_REGISTRY_CACHE: JurisdictionalRegistry | None = None


class ConfigurationError(RuntimeError):
    """Raised when a mandatory sovereign governance configuration file is missing, unreadable, or malformed."""


def _validate_profile_invariants(code: str, profile: JurisdictionSovereigntyProfile, source: Path) -> None:
    """Verify that a loaded jurisdiction profile contains mandatory non-empty architectural invariants."""
    if not profile.architectural_invariants:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Jurisdiction '{code}' in '{source}' defines zero architectural invariants."
        )


def load_verified_registry_fail_closed(path: Path | None = None) -> JurisdictionalRegistry:
    """Load and strictly validate the canonical JurisdictionalRegistry in fail-closed mode.

    Raises:
        ConfigurationError: If the governance policy file is missing, unreadable, malformed,
            fails strict Pydantic schema validation, or defines an empty jurisdiction set.
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None and path is None:
        return _REGISTRY_CACHE

    target = Path(path).resolve() if path is not None else CONFIG_PATH.resolve()
    if not target.exists() or not target.is_file():
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Jurisdictional sovereignty registry not found or not a regular file at '{target}'."
        )

    try:
        raw_text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Unable to read jurisdictional registry at '{target}': {exc}"
        ) from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Malformed JSON in jurisdictional registry '{target}': {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Root element of '{target}' must be a JSON object."
        )

    try:
        registry = JurisdictionalRegistry.model_validate(data, strict=True)
    except ValidationError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Schema validation failed for '{target}': {exc}"
        ) from exc

    if not registry.jurisdictions:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Jurisdictional registry '{target}' contains zero active jurisdictions."
        )

    for code, profile in registry.jurisdictions.items():
        _validate_profile_invariants(code, profile, target)

    # Strict fail-closed loading of any dynamically synthesized and cached jurisdictions
    dynamic_path = Path(DYNAMIC_DIR).resolve()
    if dynamic_path.exists():
        if not dynamic_path.is_dir():
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Dynamic jurisdiction path '{dynamic_path}' is not a directory."
            )
        for dyn_file in sorted(dynamic_path.glob("*.json")):
            if not dyn_file.is_file():
                raise ConfigurationError(
                    f"Fatal Fail-Closed Policy Error: Dynamic jurisdiction entry '{dyn_file}' is not a regular file."
                )
            code = dyn_file.stem.upper()
            if code not in registry.jurisdictions:
                try:
                    raw_dyn = dyn_file.read_text(encoding="utf-8")
                except OSError as exc:
                    raise ConfigurationError(
                        f"Fatal Fail-Closed Policy Error: Unable to read dynamic jurisdiction file '{dyn_file}': {exc}"
                    ) from exc
                try:
                    p_data = json.loads(raw_dyn)
                except json.JSONDecodeError as exc:
                    raise ConfigurationError(
                        f"Fatal Fail-Closed Policy Error: Malformed JSON in dynamic jurisdiction file '{dyn_file}': {exc}"
                    ) from exc
                try:
                    profile = JurisdictionSovereigntyProfile.model_validate(p_data, strict=True)
                except ValidationError as exc:
                    raise ConfigurationError(
                        f"Fatal Fail-Closed Policy Error: Schema validation failed for dynamic jurisdiction '{dyn_file}': {exc}"
                    ) from exc
                _validate_profile_invariants(code, profile, dyn_file)
                registry.jurisdictions[code] = profile

    if path is None:
        _REGISTRY_CACHE = registry
    return registry


def load_jurisdictional_registry(path: Path | None = None) -> JurisdictionalRegistry:
    """Load and cache the canonical JurisdictionalRegistry from disk using fail-closed enforcement."""
    return load_verified_registry_fail_closed(path=path)


def _normalize_token(value: str) -> str:
    """Normalize a string token to uppercase ASCII without diacritics."""
    return (
        unicodedata.normalize("NFKD", value.strip().upper())
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )


def infer_jurisdiction_code(
    country: str | None,
    frameworks: List[str] | None,
    language: str | None,
    registry: JurisdictionalRegistry | None = None,
) -> str:
    """Infer the ISO region code dynamically from the verified JurisdictionalRegistry."""
    active_registry = registry or load_verified_registry_fail_closed()
    if not active_registry.jurisdictions:
        raise ConfigurationError(
            "Fatal Fail-Closed Policy Error: Cannot infer jurisdiction code from an empty registry."
        )

    extra_config: Dict[str, Any] = (
        active_registry.model_extra if isinstance(active_registry.model_extra, dict) else {}
    )
    country_aliases: Dict[str, str] = getattr(active_registry, "country_aliases", None) or extra_config.get("country_aliases", {})
    framework_mappings: Dict[str, str] = getattr(active_registry, "framework_mappings", None) or extra_config.get("framework_mappings", {})
    language_mappings: Dict[str, str] = getattr(active_registry, "language_mappings", None) or extra_config.get("language_mappings", {})

    if country:
        c_clean = _normalize_token(country)
        if c_clean in active_registry.jurisdictions:
            return c_clean
        if isinstance(country_aliases, dict) and c_clean in country_aliases:
            return str(country_aliases[c_clean]).upper()
        for code, profile in active_registry.jurisdictions.items():
            if c_clean == _normalize_token(profile.region_code):
                return code
            name_tokens = [
                t.strip()
                for t in re.split(r"[/,\-()\s]+", _normalize_token(profile.name))
                if t.strip()
            ]
            if c_clean in name_tokens or c_clean == _normalize_token(profile.name):
                return code
        if len(c_clean) == 2 and c_clean.isalpha():
            return c_clean

    if frameworks:
        normalized_frameworks = [_normalize_token(fw) for fw in frameworks if fw and fw.strip()]
        joined_tokens = " ".join(normalized_frameworks)
        if isinstance(framework_mappings, dict):
            for keyword, mapped_code in framework_mappings.items():
                if _normalize_token(str(keyword)) in joined_tokens:
                    return str(mapped_code).upper()
        for code, profile in active_registry.jurisdictions.items():
            corpus = " ".join(
                [
                    _normalize_token(profile.name),
                    _normalize_token(profile.primary_hsm_standard),
                    *(_normalize_token(inv) for inv in profile.architectural_invariants),
                    *(_normalize_token(rule) for rule in profile.data_residency_rules),
                    *(_normalize_token(std) for std in profile.connectivity_standards),
                ]
            )
            for fw_token in normalized_frameworks:
                if fw_token and fw_token in corpus:
                    return code

    if language:
        lang_clean = _normalize_token(language)
        if isinstance(language_mappings, dict):
            for lang_key, mapped_code in language_mappings.items():
                if _normalize_token(str(lang_key)) == lang_clean:
                    return str(mapped_code).upper()
        if lang_clean in active_registry.jurisdictions:
            return lang_clean

    default_code = (
        getattr(active_registry, "default_jurisdiction", None)
        or extra_config.get("default_jurisdiction")
    )
    if isinstance(default_code, str) and default_code.upper() in active_registry.jurisdictions:
        return default_code.upper()

    return next(iter(active_registry.jurisdictions.keys()))


def _load_jit_prompt_template(registry: JurisdictionalRegistry | None = None) -> str:
    """Load the JIT jurisdiction synthesis prompt template from external configuration."""
    if registry is not None:
        extra_config: Dict[str, Any] = (
            registry.model_extra if isinstance(registry.model_extra, dict) else {}
        )
        inline_template = (
            getattr(registry, "jit_synthesis_prompt_template", None)
            or extra_config.get("jit_synthesis_prompt_template")
        )
        if isinstance(inline_template, str) and inline_template.strip():
            return inline_template

    prompt_file = JIT_PROMPT_PATH.resolve()
    if not prompt_file.exists() or not prompt_file.is_file():
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: JIT synthesis prompt template file missing at '{prompt_file}'."
        )
    try:
        content = prompt_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Unable to read JIT synthesis prompt template at '{prompt_file}': {exc}"
        ) from exc
    if not content:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: JIT synthesis prompt template at '{prompt_file}' is empty."
        )
    return content


def synthesize_jurisdiction_profile_jit(
    country: str,
    frameworks: List[str] | None = None,
    region_code: str | None = None,
    registry: JurisdictionalRegistry | None = None,
) -> JurisdictionSovereigntyProfile | None:
    """Synthesize at runtime a formal JurisdictionSovereigntyProfile for an unlisted jurisdiction."""
    if not country or len(country.strip()) < 2:
        raise ConfigurationError(
            "Fatal Fail-Closed Policy Error: Country identifier for JIT synthesis must contain at least 2 characters."
        )
    clean_code = (region_code or country.strip()[:2]).strip().upper()
    dynamic_dir = Path(DYNAMIC_DIR).resolve()
    try:
        dynamic_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Unable to create dynamic jurisdiction directory '{dynamic_dir}': {exc}"
        ) from exc

    cache_file = dynamic_dir / f"{clean_code.lower()}.json"

    if cache_file.exists():
        if not cache_file.is_file():
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Cached dynamic jurisdiction path '{cache_file}' is not a regular file."
            )
        try:
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            profile = JurisdictionSovereigntyProfile.model_validate(cached_data, strict=True)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Corrupted cached dynamic jurisdiction at '{cache_file}': {exc}"
            ) from exc
        _validate_profile_invariants(clean_code, profile, cache_file)
        return profile

    prompt_template = _load_jit_prompt_template(registry=registry)
    prompt = prompt_template.format(
        country=country.strip(),
        frameworks=json.dumps(frameworks or []),
        clean_code=clean_code,
    )

    from assessment_engine.infrastructure.genai_client import (
        ModelTier,
        create_genai_client,
        get_model,
    )

    client = create_genai_client()
    model_name = get_model(ModelTier.FAST)

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
    except RuntimeError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Model invocation failed during JIT synthesis for '{country}': {exc}"
        ) from exc

    raw_output = getattr(response, "text", None)
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Empty model response during JIT synthesis for '{country}'."
        )

    text = raw_output.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        synthesized = json.loads(text)
        profile = JurisdictionSovereigntyProfile.model_validate(synthesized, strict=True)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Synthesized JIT profile for '{country}' failed validation: {exc}"
        ) from exc

    _validate_profile_invariants(clean_code, profile, cache_file)

    try:
        cache_file.write_text(
            json.dumps(profile.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ConfigurationError(
            f"Fatal Fail-Closed Policy Error: Failed writing synthesized jurisdiction cache '{cache_file}': {exc}"
        ) from exc

    logger.info(
        "Successfully synthesized and cached JIT jurisdiction profile for '%s' (%s).",
        country,
        clean_code,
    )
    return profile


class JurisdictionalSovereigntyPolicy(BaseSovereignPolicy):
    """Enforces territorial architectural sovereignty across knowledge graphs and deliverables."""

    def __init__(self, registry: JurisdictionalRegistry | None = None) -> None:
        self.registry = registry or load_verified_registry_fail_closed()
        if not self.registry.jurisdictions:
            raise ConfigurationError(
                "Fatal Fail-Closed Policy Error: JurisdictionalSovereigntyPolicy initialized with an empty registry."
            )

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Inject jurisdictional invariants into the epistemic graph and enrich document payload."""
        meta = payload.setdefault("document_meta", {})
        client_name = meta.get("client_name", "CLIENT")
        tower_code = meta.get("tower_code", "T0")

        # Extract context
        country_hint = (
            meta.get("country")
            or meta.get("region_code")
            or payload.get("jurisdiction")
        )
        frameworks = (
            meta.get("regulatory_context")
            or meta.get("regulatory_frameworks")
            or []
        )
        language = meta.get("language") or meta.get("doc_lang")

        code = infer_jurisdiction_code(
            country=country_hint,
            frameworks=frameworks,
            language=language,
            registry=self.registry,
        )
        profile: JurisdictionSovereigntyProfile | None = self.registry.jurisdictions.get(code)

        # Runtime JIT Resolution if unlisted and country_hint is provided
        if profile is None and country_hint:
            profile = synthesize_jurisdiction_profile_jit(
                str(country_hint),
                frameworks,
                region_code=code,
                registry=self.registry,
            )
            if profile is not None:
                self.registry.jurisdictions[code] = profile

        if profile is None:
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: No verified JurisdictionSovereigntyProfile resolved for code '{code}'."
            )

        if not profile.architectural_invariants:
            raise ConfigurationError(
                f"Fatal Fail-Closed Policy Error: Resolved jurisdiction '{code}' contains zero architectural invariants."
            )

        # 1. Enrich payload metadata
        meta["jurisdiction_code"] = code
        meta["jurisdiction_name"] = profile.name
        meta["jurisdictional_sovereignty"] = profile.model_dump()

        # 2. Augment target projects with jurisdictional deliverables
        primary_invariant = profile.architectural_invariants[0]
        for pillar in payload.get("pillars_analysis", []):
            for proj in pillar.get("projects_todo", []):
                deliverables = proj.setdefault("deliverables", [])
                d_item = f"Architectural Sovereignty Verification: {primary_invariant}"
                if d_item not in deliverables:
                    deliverables.append(d_item)

        # 3. Inject semantic sovereignty triples into the epistemic graph
        graph.inject_triple(
            subject=client_name,
            predicate="BOUND_TO_JURISDICTION",
            object_val=profile.name,
            source="SOVEREIGNTY_POLICY",
            confidence=1.0,
        )

        for provider in profile.sovereign_cloud_providers[:2]:
            graph.inject_triple(
                subject=tower_code,
                predicate="QUALIFIED_SOVEREIGN_PROVIDER",
                object_val=provider,
                source="SOVEREIGNTY_POLICY",
                confidence=0.9,
            )

        for i, inv in enumerate(profile.architectural_invariants, 1):
            graph.inject_triple(
                subject=tower_code,
                predicate=f"ENFORCES_JURISDICTIONAL_INVARIANT_{i}",
                object_val=inv,
                source="SOVEREIGNTY_POLICY",
                confidence=0.95,
            )

        return payload
