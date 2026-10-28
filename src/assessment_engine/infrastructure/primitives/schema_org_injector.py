"""
Schema.org JSON-LD Semantic SEO Primitive — GEMA 12 (SOTA 2026).
Injects rich structured data (LocalBusiness, MedicalClinic, SportsActivityLocation, Product)
into HTML head tags for prominent Google Search and Knowledge Graph ranking.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.schema_org_injector")


SCHEMA_ORG_ARCHETYPE_MAP = {
    "A1": "OnlineStore",
    "A2": "SoftwareApplication",
    "A3": "ProfessionalService",
    "A4": "EducationalOrganization",
    "A5": "RealEstateAgent",
    "A6": "SoftwareApplication",
    "A7": "LocalBusiness",
    "A8": "EntertainmentBusiness",
    "A9": "FinancialService",
    "A10": "ProfessionalService",
    "A11": "GovernmentOrganization",
}

MACRO_TO_SCHEMA_ORG_MAP = {
    "HEALTH": "MedicalBusiness",
    "HEALTH_WELLNESS_DAILY": "MedicalBusiness",
    "PETS_SERVICES_CARE": "MedicalBusiness",
    "SPORTS": "SportsActivityLocation",
    "FITNESS_SPORTS_CLUBS": "SportsActivityLocation",
    "FOOD_HOSPITALITY": "FoodEstablishment",
    "LEGAL_CORP": "LegalService",
    "AUTOMOTIVE_LOCAL_MOBILITY": "AutomotiveBusiness",
    "FINTECH": "FinancialService",
    "FINANCIAL": "FinancialService",
    "REAL_ESTATE": "RealEstateAgent",
    "HOUSING_ACCESSIBLE_REALESTATE": "RealEstateAgent",
    "EDUCATION": "EducationalOrganization",
    "RETAIL_COMMERCE_D2C": "OnlineStore",
}


def _resolve_schema_org_type(contract: dict[str, Any]) -> str:
    """Resolve the canonical Schema.org @type from contract archetypes or enterprise taxonomy database."""
    declared = contract.get("schema_type")
    if declared:
        return str(declared)

    arch = str(contract.get("archetype") or "").split("_")[0].upper()
    if arch in SCHEMA_ORG_ARCHETYPE_MAP:
        base_type = SCHEMA_ORG_ARCHETYPE_MAP[arch]
        if base_type != "LocalBusiness":
            return base_type

    sector = str(contract.get("sector") or "")
    if sector:
        try:
            from assessment_engine.infrastructure.primitives.design_system_synthesizer import _resolve_macro_category_from_db
            macro = _resolve_macro_category_from_db("", sector)
            if macro in MACRO_TO_SCHEMA_ORG_MAP:
                return MACRO_TO_SCHEMA_ORG_MAP[macro]
        except Exception as ex:
            logger.debug(f"[SchemaOrgInjector] Error resolviendo macro ontología: {ex}")

    return "LocalBusiness"


def _resolve_price_range(contract: dict[str, Any]) -> str:
    """Derive standard priceRange indicator from pricing tiers."""
    tiers = contract.get("pricing_tiers", [])
    all_text = " ".join(str(t.get("price_text", "")) for t in tiers)
    if "$" in all_text:
        return "$$"
    if "£" in all_text:
        return "££"
    if "AED" in all_text:
        return "AED"
    if "CHF" in all_text:
        return "CHF"
    if "¥" in all_text or "元" in all_text:
        return "¥¥"
    return "€€"


class SchemaOrgInjectorPrimitive:
    """
    Inject domain-agnostic Schema.org JSON-LD structured data for worldwide applications.
    """

    def generate_json_ld(self, contract: dict[str, Any]) -> str:
        """Generate the JSON-LD script block from the domain contract."""
        app_name = contract.get("app_name", "Plataforma Profesional")
        tagline = contract.get("tagline", "Servicios profesionales de alta calidad")
        locale = str(contract.get("locale") or "es").lower()

        schema_type = _resolve_schema_org_type(contract)
        price_range = _resolve_price_range(contract)

        country_code = "US" if "en" in locale else ("ES" if "es" in locale else "GLOBAL")
        data = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "name": app_name,
            "description": tagline,
            "url": "https://autonomuos.app",
            "priceRange": price_range,
            "address": {
                "@type": "PostalAddress",
                "addressCountry": country_code,
            }
        }

        return f'<script type="application/ld+json">\n{json.dumps(data, indent=2, ensure_ascii=False)}\n</script>'


schema_org_injector = SchemaOrgInjectorPrimitive()
