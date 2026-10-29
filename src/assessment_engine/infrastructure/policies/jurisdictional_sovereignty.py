"""Jurisdictional Sovereignty Policy for the Sovereign Assessment Engine.

Maps client regulatory environments and country contexts to concrete territorial
architectural invariants, sovereign cloud stacks, and direct connectivity standards,
featuring Just-In-Time (JIT) dynamic synthesis and caching for unlisted jurisdictions.
"""
from __future__ import annotations


import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from assessment_engine.domain.schemas.jurisdiction import (
    JurisdictionSovereigntyProfile,
    JurisdictionalRegistry,
)
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = ROOT / "engine_config" / "policies" / "jurisdictional_sovereignty.json"
DYNAMIC_DIR = ROOT / "engine_config" / "policies" / "jurisdictions_dynamic"

_REGISTRY_CACHE: JurisdictionalRegistry | None = None


def load_jurisdictional_registry(path: Path | None = None) -> JurisdictionalRegistry:
    """Load and cache the canonical JurisdictionalRegistry from disk, augmenting with dynamic JIT locales."""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None and path is None:
        return _REGISTRY_CACHE

    target = path or CONFIG_PATH
    if not target.exists():
        target = Path("engine_config/policies/jurisdictional_sovereignty.json")

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        registry = JurisdictionalRegistry.model_validate(data)
    except Exception as ex:
        logger.warning("Failed to load jurisdictional registry from %s: %s. Using empty fallback.", target, ex)
        registry = JurisdictionalRegistry()

    # Auto-load any dynamically synthesized and cached jurisdictions
    dynamic_path = Path(DYNAMIC_DIR)
    if dynamic_path.exists():
        for dyn_file in dynamic_path.glob("*.json"):
            code = dyn_file.stem.upper()
            if code not in registry.jurisdictions:
                try:
                    p_data = json.loads(dyn_file.read_text(encoding="utf-8"))
                    profile = JurisdictionSovereigntyProfile.model_validate(p_data)
                    registry.jurisdictions[code] = profile
                except Exception as ex:
                    logger.debug("Error loading dynamic jurisdiction from %s: %s", dyn_file, ex)

    if path is None:
        _REGISTRY_CACHE = registry
    return registry


def infer_jurisdiction_code(
    country: str | None,
    frameworks: List[str] | None,
    language: str | None,
) -> str:
    """Infers the ISO region code based on country, regulatory frameworks, or document language."""
    if country:
        import unicodedata
        c_clean = unicodedata.normalize("NFKD", country.strip().upper()).encode("ASCII", "ignore").decode("utf-8")
        if c_clean in ("DE", "GERMANY", "DEUTSCHLAND", "DACH"):
            return "DE"
        if c_clean in ("ES", "SPAIN", "ESPANA"):
            return "ES"
        if c_clean in ("US", "USA", "UNITED STATES", "ESTADOS UNIDOS"):
            return "US"
        if c_clean in ("BR", "BRAZIL", "BRASIL"):
            return "BR"
        if c_clean in ("MX", "MEXICO"):
            return "MX"
        if c_clean in ("JP", "JAPAN", "JAPON"):
            return "JP"
        if c_clean in ("SA", "SAUDI ARABIA", "ARABIA SAUDITA", "KSA"):
            return "SA"
        if c_clean in ("SG", "SINGAPORE", "SINGAPUR"):
            return "SG"
        if c_clean in ("AU", "AUSTRALIA"):
            return "AU"
        if c_clean in ("CL", "CHILE"):
            return "CL"
        if c_clean in ("CO", "COLOMBIA"):
            return "CO"
        if c_clean in ("NO", "NORWAY", "NORUEGA"):
            return "NO"
        if c_clean in ("UK", "GB", "UNITED KINGDOM", "REINO UNIDO"):
            return "GB"
        if len(c_clean) == 2 and c_clean.isalpha():
            return c_clean

    # Analyze regulatory text tokens
    tokens = " ".join(frameworks or []).lower()
    if any(k in tokens for k in ("nis2", "bsi", "it-grundschutz", "iec 62443", "gaia-x")):
        return "DE"
    if any(k in tokens for k in ("ens", "ccn", "esquema nacional", "sara")):
        return "ES"
    if any(k in tokens for k in ("fedramp", "hipaa", "cmmc", "nist", "fda")):
        return "US"
    if any(k in tokens for k in ("bcb", "lgpd", "pix", "rsfn")):
        return "BR"
    if any(k in tokens for k in ("cnbv", "spei", "banxico", "inai")):
        return "MX"
    if any(k in tokens for k in ("fisc", "ismap", "zedi", "jcmvp")):
        return "JP"
    if any(k in tokens for k in ("sama", "nca", "ecc-1")):
        return "SA"
    if any(k in tokens for k in ("mas", "trm", "abs")):
        return "SG"
    if any(k in tokens for k in ("apra", "essential eight", "cps 234")):
        return "AU"
    if any(k in tokens for k in ("cmf", "ran 20-10")):
        return "CL"
    if any(k in tokens for k in ("sfc", "circular 007")):
        return "CO"

    # Fallback to language hints
    lang_to_jurisdiction = {
        "de": "DE",
        "ja": "JP",
        "en": "US",
        "pt": "BR",
    }
    normalized_code = (language or "en").strip().lower()
    return lang_to_jurisdiction.get(normalized_code, "ES")


def synthesize_jurisdiction_profile_jit(
    country: str,
    frameworks: List[str] | None = None,
    region_code: str | None = None,
) -> JurisdictionSovereigntyProfile | None:
    """Synthesizes at runtime a formal JurisdictionSovereigntyProfile for an unlisted country/jurisdiction."""
    clean_code = (region_code or country[:2]).strip().upper()
    dynamic_dir = Path(DYNAMIC_DIR)
    dynamic_dir.mkdir(parents=True, exist_ok=True)
    cache_file = dynamic_dir / f"{clean_code.lower()}.json"

    if cache_file.exists():
        try:
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            return JurisdictionSovereigntyProfile.model_validate(cached_data)
        except Exception as ex:
            logger.debug("Failed reading cached dynamic jurisdiction: %s", ex)

    try:
        from assessment_engine.infrastructure.genai_client import (
            ModelTier,
            create_genai_client,
            get_model,
        )

        client = create_genai_client()
        model_name = get_model(ModelTier.FAST)

        prompt = f"""You are a Principal Enterprise & Sovereign Cloud Architect specializing in global regulatory and territorial compliance.
Synthesize the formal territorial architectural sovereignty profile for country/jurisdiction: '{country}'.
Relevant regulatory frameworks: {json.dumps(frameworks or [])}.
Region Code: '{clean_code}'.

Return ONLY a valid JSON object matching the exact schema:
{{
  "name": "{country} / Regional Sovereign Cloud",
  "region_code": "{clean_code}",
  "sovereign_cloud_providers": ["List 2-4 primary qualified local or sovereign cloud datacenter providers"],
  "architectural_invariants": ["List 3-4 mandatory technical, cryptographic, or operational invariants, e.g. local residency, specific banking/critical infra laws, certification schemes"],
  "connectivity_standards": ["List 1-2 direct secure interconnection standards, national fiber backbones, or IXPs"],
  "primary_hsm_standard": "Mandated HSM standard, e.g. FIPS 140-2 Level 3 or local standard",
  "data_residency_rules": ["List 1-2 strict data boundary or judicial custody rules"]
}}"""

        response = client.models.generate_content(
            model=model_name, contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        synthesized = json.loads(text)
        profile = JurisdictionSovereigntyProfile.model_validate(synthesized)
        cache_file.write_text(
            json.dumps(profile.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Successfully synthesized and cached JIT jurisdiction profile for '%s' (%s).", country, clean_code)
        return profile
    except Exception as ex:
        logger.warning("JIT synthesis of jurisdiction '%s' skipped or unavailable: %s. Using default baseline.", country, ex)
        return None


class JurisdictionalSovereigntyPolicy(BaseSovereignPolicy):
    """Enforces territorial architectural sovereignty across knowledge graphs and deliverables."""

    def __init__(self, registry: JurisdictionalRegistry | None = None) -> None:
        self.registry = registry or load_jurisdictional_registry()

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Injects jurisdictional invariants into the epistemic graph and enriches document payload."""
        meta = payload.get("document_meta", {})
        client_name = meta.get("client_name", "CLIENT")
        tower_code = meta.get("tower_code", "T0")

        # Extract context
        country_hint = meta.get("country") or meta.get("region_code") or payload.get("jurisdiction")
        frameworks = meta.get("regulatory_context") or meta.get("regulatory_frameworks") or []
        language = meta.get("language") or meta.get("doc_lang")

        code = infer_jurisdiction_code(country_hint, frameworks, language)
        profile: JurisdictionSovereigntyProfile | None = self.registry.jurisdictions.get(code)

        # Runtime JIT Resolution if unlisted
        if not profile and country_hint:
            profile = synthesize_jurisdiction_profile_jit(str(country_hint), frameworks, region_code=code)
            if profile:
                self.registry.jurisdictions[code] = profile

        if not profile:
            profile = self.registry.jurisdictions.get("ES")

        if not profile:
            return payload

        # 1. Enrich payload metadata
        meta["jurisdiction_code"] = code
        meta["jurisdiction_name"] = profile.name
        meta["jurisdictional_sovereignty"] = profile.model_dump()

        # 2. Augment target projects with jurisdictional deliverables
        for pillar in payload.get("pillars_analysis", []):
            for proj in pillar.get("projects_todo", []):
                deliverables = proj.setdefault("deliverables", [])
                invariant = profile.architectural_invariants[0]
                d_item = f"Architectural Sovereignty Verification: {invariant}"
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
