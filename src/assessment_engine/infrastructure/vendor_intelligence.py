"""Vendor Intelligence & Just-In-Time (JIT) Dynamic Blueprint Synthesizer.

Neuro-symbolic integration of 86+ official manufacturer technical architectures
with real-time JIT synthesis for novel, niche, or uncataloged vendors.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger("vendor_intelligence")

BLUEPRINTS_DIR = Path("engine_config/vendor_blueprints")
DYNAMIC_BLUEPRINTS_DIR = BLUEPRINTS_DIR / "dynamic"
DYNAMIC_BLUEPRINTS_DIR.mkdir(parents=True, exist_ok=True)


class SynthesizedBlueprintPayload(BaseModel):
    vendor_id: str = Field(
        description="Unique snake_case vendor identifier"
    )
    display_name: str = Field(
        description="Official commercial name of the vendor or solution"
    )
    official_domains: List[str] = Field(
        description="Official domains for technical documentation and support"
    )
    coverage_domain_id: str = Field(
        description="Principal technical domain identifier in uppercase"
    )
    coverage_domain_name: str = Field(
        description="Descriptive name of the reference architecture"
    )
    search_query: str = Field(
        description="Technical search query for datasheets and official whitepapers"
    )
    expected_entities: List[str] = Field(
        description="Key components, protocols, or architecture features"
    )


class DynamicVendorSynthesizer:
    """Synthesizes official manufacturer blueprints Just-In-Time for any uncataloged technology."""

    def __init__(self, dynamic_dir: Optional[Path] = None):
        self.dynamic_dir = dynamic_dir or DYNAMIC_BLUEPRINTS_DIR
        self.dynamic_dir.mkdir(parents=True, exist_ok=True)

    def synthesize_blueprint(
        self, vendor_name: str, context_clue: str = ""
    ) -> Dict[str, Any]:
        """Loads cached blueprint or synthesizes a new one dynamically via AI research."""
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", vendor_name.lower().strip())
        out_file = self.dynamic_dir / f"{clean_name}.yaml"
        if out_file.exists():
            try:
                with open(out_file, encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as exc:
                logger.warning("Failed to read dynamic blueprint %s: %s", out_file, exc)

        logger.info(
            "Synthesizing Just-In-Time Blueprint for technology/vendor: '%s'...",
            vendor_name,
        )

        # Build prompt for structured synthesis
        prompt = f"""You are a Principal Cybersecurity and Tier-1 Infrastructure Engineer.
Identified uncataloged technology or vendor '{vendor_name}' in client environment (Context: '{context_clue}').
This vendor is missing from pre-existing catalog.

Your mission is to research and synthesize the formal vendor blueprint:
1. Deduce unique identifier (vendor_id in snake_case).
2. Official commercial name of solution or suite (display_name).
3. Official documentation and support domains (official_domains).
4. Formulate technical search query with filetype:pdf to retrieve official whitepapers.
5. List 4 to 6 key technical entities, protocols, or native capabilities (expected_entities).
"""
        try:
            from assessment_engine.infrastructure.ai_client import run_agent
            from assessment_engine.infrastructure.model_config import ModelTier

            payload = run_agent(
                prompt=prompt,
                schema=SynthesizedBlueprintPayload,
                tier=ModelTier.FAST,
            )
        except Exception as e:
            logger.warning(
                "Error invoking AI for blueprint of %s: %s. Applying heuristic fallback template.",
                vendor_name,
                e,
            )
            payload = SynthesizedBlueprintPayload(
                vendor_id=clean_name,
                display_name=f"{vendor_name.capitalize()} Enterprise Solutions",
                official_domains=[f"docs.{clean_name}.com", f"{clean_name}.com"],
                coverage_domain_id="CORE_SOLUTION_SPECS",
                coverage_domain_name=f"Official Technical Specifications of {vendor_name}",
                search_query=f"{vendor_name} technical architecture whitepaper filetype:pdf",
                expected_entities=[
                    vendor_name,
                    "Enterprise",
                    "High_Availability",
                    "Security",
                ],
            )

        bp_dict = {
            "vendor_id": payload.vendor_id,
            "display_name": payload.display_name,
            "official_domains": payload.official_domains,
            "coverage_domains": [
                {
                    "domain_id": payload.coverage_domain_id,
                    "name": payload.coverage_domain_name,
                    "criticality": "HIGH",
                    "search_query": payload.search_query,
                    "expected_entities": payload.expected_entities,
                }
            ],
            "synthesized_jit": True,
            "created_at": datetime.now(UTC).isoformat(),
        }

        try:
            with open(out_file, "w", encoding="utf-8") as f:
                yaml.dump(bp_dict, f, allow_unicode=True, sort_keys=False, indent=2)
            logger.info("Dynamic blueprint saved successfully: %s", out_file)
        except Exception as io_err:
            logger.error(
                "Error saving dynamic blueprint %s: %s", out_file, io_err
            )

        return bp_dict


class VendorRegistry:
    """Manages static and dynamically synthesized vendor blueprints."""

    _STATIC_REGISTRY: Dict[str, Dict[str, Any]] = {}
    _INITIALIZED: bool = False

    @classmethod
    def initialize(cls):
        """Load static and dynamic vendor blueprints into registry cache."""
        if cls._INITIALIZED:
            return
        cls._STATIC_REGISTRY.clear()
        if BLUEPRINTS_DIR.exists():
            for yaml_file in BLUEPRINTS_DIR.glob("*.yaml"):
                try:
                    with open(yaml_file, encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    if isinstance(data, dict) and "vendor_id" in data:
                        cls._STATIC_REGISTRY[data["vendor_id"].lower()] = data
                except Exception as e:
                    logger.debug("Error cargando blueprint %s: %s", yaml_file, e)

        # Load dynamic blueprints
        if DYNAMIC_BLUEPRINTS_DIR.exists():
            for yaml_file in DYNAMIC_BLUEPRINTS_DIR.glob("*.yaml"):
                try:
                    with open(yaml_file, encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    if isinstance(data, dict) and "vendor_id" in data:
                        cls._STATIC_REGISTRY[data["vendor_id"].lower()] = data
                except Exception as e:
                    logger.debug(
                        "Error loading dynamic blueprint %s: %s", yaml_file, e
                    )

        cls._INITIALIZED = True

    @classmethod
    def get_supported_vendor_ids(cls) -> List[str]:
        """Retrieve list of supported vendor identifiers from catalog."""
        cls.initialize()
        return list(cls._STATIC_REGISTRY.keys())

    @classmethod
    def resolve_blueprint(
        cls, vendor_name: str, auto_synthesize: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Resolves blueprint from static catalog or triggers JIT synthesis."""
        cls.initialize()
        v_key = re.sub(r"[^a-zA-Z0-9_]", "_", vendor_name.lower().strip())
        if v_key in cls._STATIC_REGISTRY:
            return cls._STATIC_REGISTRY[v_key]

        # Check for substring match (e.g. 'pure' for 'pure_storage')
        for existing_id, bp in cls._STATIC_REGISTRY.items():
            if existing_id == v_key or v_key in existing_id or existing_id in v_key:
                return bp

        if auto_synthesize:
            synthesizer = DynamicVendorSynthesizer()
            bp = synthesizer.synthesize_blueprint(vendor_name)
            cls._STATIC_REGISTRY[bp["vendor_id"].lower()] = bp
            return bp

        return None

    @classmethod
    def detect_vendors_in_text(cls, text: str) -> List[Dict[str, Any]]:
        """Scans evidence text to identify mentioned vendors and retrieve their technical capabilities."""
        cls.initialize()
        detected: List[Dict[str, Any]] = []
        seen = set()

        text_lower = text.lower()
        for vendor_id, bp in cls._STATIC_REGISTRY.items():
            name_check = bp.get("display_name", vendor_id).lower()
            tokens = [vendor_id.replace("_", " "), vendor_id]
            if len(name_check) > 3:
                tokens.append(name_check)

            if any(
                re.search(r"\b" + re.escape(t) + r"\b", text_lower)
                for t in tokens
                if len(t) > 2
            ):
                if vendor_id not in seen:
                    seen.add(vendor_id)
                    detected.append(bp)

        return detected

    @classmethod
    def format_vendor_context_for_architect(cls, vendors: List[Dict[str, Any]]) -> str:
        """Formats discovered vendor technical architectures for prompt injection."""
        if not vendors:
            return ""

        lines = [
            "\n### OFFICIAL VENDOR REFERENCE ARCHITECTURE CAPABILITIES:",
            "Leverage native capabilities present in client tooling before prescribing third-party licenses:",
        ]

        for bp in vendors:
            v_name = bp.get("display_name", bp.get("vendor_id", "Vendor"))
            domains = bp.get("coverage_domains", [])
            lines.append(f"\n- **Vendor: {v_name}**")
            for dom in domains:
                dom_name = dom.get("name", "")
                entities = ", ".join(dom.get("expected_entities", []))
                lines.append(f"  • {dom_name}: Key capabilities [{entities}]")

        lines.append(
            "\nMANDATORY PRESCRIPTION DIRECTIVE:\n"
            "If proposing modernization across these components, cite the official native capabilities indicated above "
            "(e.g. WORM, SnapLock, Active IQ, FortKnox, SpanFS, Cloud Tiering, MetroCluster, etc.) to substantiate maximum return on investment."
        )
        return "\n".join(lines)
