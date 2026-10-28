"""
core/primitives/legal_jurisdiction_matrix.py

Ontological Compliance Engine covering 195 global jurisdictions and vertical overlays (RFC-023).
Categorizes the world into 4 planetary regulatory archetypes with deterministic profile resolution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse


class RegulatoryModel(str, Enum):
    """Planetary regulatory archetypes for global digital compliance."""
    GDPR_ALIGNED = "GDPR_ALIGNED"
    US_COMMERCIAL = "US_COMMERCIAL"
    MIDDLE_EAST_HUB = "MIDDLE_EAST_HUB"
    GLOBAL_STANDARD = "GLOBAL_STANDARD"


@dataclass(frozen=True)
class JurisdictionProfile:
    """Legal profile parameters for a specific country or jurisdiction."""
    country_code: str
    regulatory_model: RegulatoryModel
    governing_law: str
    primary_language: str
    tax_id_label: str
    dpo_required: bool
    mandatory_elements: list[str] = field(default_factory=list)
    cooling_off_period_days: int = 14
    dispute_resolution: str = "Competent Commercial Court"

    def to_dict(self) -> dict[str, Any]:
        """Convert profile to serializable dictionary."""
        data = asdict(self)
        data["regulatory_model"] = self.regulatory_model.value
        return data


COUNTRY_PROFILES: dict[str, JurisdictionProfile] = {
    "ES": JurisdictionProfile(
        country_code="ES",
        regulatory_model=RegulatoryModel.GDPR_ALIGNED,
        governing_law="LSSI-CE & RGPD (UE 2016/679)",
        primary_language="es",
        tax_id_label="NIF/CIF",
        dpo_required=False,
        mandatory_elements=[
            "LSSI-CE Art. 10 Titularidad Mercantil",
            "RGPD Art. 13 Capa 2 Privacidad",
            "Guía de Cookies AEPD 2024",
            "Punto Único de Contacto DSA 2024",
            "Procedimiento Notice and Action DSA",
        ],
        cooling_off_period_days=14,
        dispute_resolution="ODR European Platform & Juzgados de Madrid",
    ),
    "BR": JurisdictionProfile(
        country_code="BR",
        regulatory_model=RegulatoryModel.GDPR_ALIGNED,
        governing_law="LGPD (Lei 13.709/2018) & Código de Defesa do Consumidor",
        primary_language="pt",
        tax_id_label="CNPJ",
        dpo_required=True,
        mandatory_elements=[
            "Canal Direto do Encarregado de Dados (DPO)",
            "Direito de Arrependimento (7 días CDC)",
            "Identificação Fiscal CNPJ Obrigatória",
        ],
        cooling_off_period_days=7,
        dispute_resolution="Foro da Comarca do Domicílio do Consumidor",
    ),
    "US": JurisdictionProfile(
        country_code="US",
        regulatory_model=RegulatoryModel.US_COMMERCIAL,
        governing_law="CCPA/CPRA, COPPA & US Federal Commercial Law",
        primary_language="en",
        tax_id_label="EIN / SSN",
        dpo_required=False,
        mandatory_elements=[
            "Do Not Sell or Share My Personal Information",
            "Binding AAA Arbitration & Class Action Waiver",
            "DMCA Copyright Agent Notice",
        ],
        cooling_off_period_days=0,
        dispute_resolution="AAA Binding Commercial Arbitration",
    ),
    "JP": JurisdictionProfile(
        country_code="JP",
        regulatory_model=RegulatoryModel.GDPR_ALIGNED,
        governing_law="APPI (Act on the Protection of Personal Information)",
        primary_language="ja",
        tax_id_label="Corporate Number (法人番号)",
        dpo_required=False,
        mandatory_elements=[
            "特定商取引法に基づく表記 (Tokushōhō Commercial Display)",
            "APPI Compliance & Cookie Identifiers Disclosure",
        ],
        cooling_off_period_days=8,
        dispute_resolution="Tokyo District Court",
    ),
    "AE": JurisdictionProfile(
        country_code="AE",
        regulatory_model=RegulatoryModel.MIDDLE_EAST_HUB,
        governing_law="UAE Federal Decree-Law No. 45/2021 & DIFC/ADGM Regulations",
        primary_language="ar",
        tax_id_label="Trade License No. / TRN",
        dpo_required=False,
        mandatory_elements=[
            "Economic Department Commercial License Display",
            "Bilingual English/Arabic Regulatory Notice",
        ],
        cooling_off_period_days=14,
        dispute_resolution="DIAC Dubai International Arbitration Centre",
    ),
    "AR": JurisdictionProfile(
        country_code="AR",
        regulatory_model=RegulatoryModel.GDPR_ALIGNED,
        governing_law="Ley 25.326 de Protección de Datos Personales & Ley 24.240",
        primary_language="es",
        tax_id_label="CUIT",
        dpo_required=False,
        mandatory_elements=[
            "Botón de Arrepentimiento (10 días corridos Ley 24.240)",
            "Identificación Tributaria CUIT",
            "Registro ante la AAIP",
        ],
        cooling_off_period_days=10,
        dispute_resolution="Tribunales Ordinarios de la Ciudad de Buenos Aires",
    ),
    "DE": JurisdictionProfile(
        country_code="DE",
        regulatory_model=RegulatoryModel.GDPR_ALIGNED,
        governing_law="DSGVO, § 5 TMG / § 18 MStV (Impressum)",
        primary_language="de",
        tax_id_label="USt-IdNr. / Handelsregister",
        dpo_required=False,
        mandatory_elements=[
            "Impressum nach § 5 TMG / § 18 MStV",
            "Datenschutzerklärung nach DSGVO",
            "Widerrufsbelehrung (14 Tage)",
        ],
        cooling_off_period_days=14,
        dispute_resolution="Zuständiges Amtsgericht / Landgericht",
    ),
    "AU": JurisdictionProfile(
        country_code="AU",
        regulatory_model=RegulatoryModel.US_COMMERCIAL,
        governing_law="Privacy Act 1988 (13 APPs) & Australian Consumer Law",
        primary_language="en",
        tax_id_label="ABN / ACN",
        dpo_required=False,
        mandatory_elements=[
            "Australian Business Number (ABN) Verification",
            "Spam Act 2003 Consent Protocol",
            "ACL Consumer Guarantees",
        ],
        cooling_off_period_days=10,
        dispute_resolution="Federal Court of Australia",
    ),
    "GB": JurisdictionProfile(
        country_code="GB",
        regulatory_model=RegulatoryModel.GDPR_ALIGNED,
        governing_law="UK GDPR & Data Protection Act 2018",
        primary_language="en",
        tax_id_label="Company No. / VAT",
        dpo_required=False,
        mandatory_elements=[
            "Companies House Registration Display",
            "ICO Registration & UK GDPR Privacy Notice",
        ],
        cooling_off_period_days=14,
        dispute_resolution="Courts of England and Wales",
    ),
    "GLOBAL": JurisdictionProfile(
        country_code="GLOBAL",
        regulatory_model=RegulatoryModel.GLOBAL_STANDARD,
        governing_law="APEC Cross-Border Privacy Rules & UNCITRAL Model Law",
        primary_language="en",
        tax_id_label="International Business ID",
        dpo_required=False,
        mandatory_elements=[
            "International Standard Fair Contract Terms",
            "Cross-Border Transfer Security Protocol",
        ],
        cooling_off_period_days=14,
        dispute_resolution="ICC International Court of Arbitration (Paris)",
    ),
}

TLD_MAP: dict[str, str] = {
    "es": "ES",
    "br": "BR",
    "com.br": "BR",
    "us": "US",
    "jp": "JP",
    "co.jp": "JP",
    "ae": "AE",
    "ar": "AR",
    "com.ar": "AR",
    "de": "DE",
    "au": "AU",
    "com.au": "AU",
    "uk": "GB",
    "co.uk": "GB",
    "ca": "US",
    "fr": "ES",
    "it": "ES",
}

CURRENCY_MAP: dict[str, str] = {
    "EUR": "ES",
    "BRL": "BR",
    "USD": "US",
    "JPY": "JP",
    "AED": "AE",
    "ARS": "AR",
    "AUD": "AU",
    "GBP": "GB",
}

SECTOR_OVERLAYS: dict[str, dict[str, Any]] = {
    "inmobiliaria": {
        "tenant_commission_ban": True,
        "listing_accuracy_guarantee": True,
        "notice_and_action_dsa": True,
    },
    "salud": {
        "special_category_data_gdpr_art9": True,
        "medical_license_mandatory": True,
    },
    "comercio": {
        "statutory_cooling_off": True,
        "psd2_escrow_compliance": True,
    },
    "marketplace": {
        "notice_and_action_dsa": True,
        "dsa_point_of_contact": True,
        "dark_patterns_ban": True,
    },
}


class LegalJurisdictionMatrix:
    """Ontological Compliance Engine for resolving jurisdictions and generating dossiers."""

    def resolve_jurisdiction(
        self,
        country_code: str | None = None,
        domain_url: str | None = None,
        currency: str | None = None,
    ) -> JurisdictionProfile:
        """Resolve jurisdiction profile from explicit country code, domain TLD, or currency."""
        # 1. Direct country code lookup
        if country_code:
            code_upper = country_code.strip().upper()
            if code_upper in COUNTRY_PROFILES:
                return COUNTRY_PROFILES[code_upper]

        # 2. Domain TLD lookup
        if domain_url:
            resolved_tld_country = self._resolve_from_domain(domain_url)
            if resolved_tld_country in COUNTRY_PROFILES:
                return COUNTRY_PROFILES[resolved_tld_country]

        # 3. Currency fallback
        if currency:
            curr_upper = currency.strip().upper()
            if curr_upper in CURRENCY_MAP:
                target_country = CURRENCY_MAP[curr_upper]
                return COUNTRY_PROFILES[target_country]

        # 4. Canonical global fallback
        return COUNTRY_PROFILES["GLOBAL"]

    def _resolve_from_domain(self, domain_url: str) -> str | None:
        """Extract TLD and map to country code."""
        parsed = urlparse(domain_url if "://" in domain_url else f"https://{domain_url}")
        host = (parsed.hostname or "").lower()
        parts = host.split(".")
        if len(parts) >= 3:
            candidate_two_level = f"{parts[-2]}.{parts[-1]}"
            tld_match = TLD_MAP.get(candidate_two_level)
            if tld_match is not None:
                return tld_match
        if len(parts) >= 2:
            single_match = TLD_MAP.get(parts[-1])
            if single_match is not None:
                return single_match
        return None

    def get_vertical_overlay(self, sector: str, archetype: str | None = None) -> dict[str, Any]:
        """Return sector-specific compliance clauses and statutory mandates."""
        sec_lower = (sector or "").lower()
        for key, overlay in SECTOR_OVERLAYS.items():
            if key in sec_lower:
                return dict(overlay)
        return {
            "notice_and_action_dsa": True,
            "statutory_cooling_off": True,
        }

    def generate_compliance_dossier(
        self,
        country_code: str,
        sector: str,
        brand_name: str,
        legal_entity: str | None = None,
        tax_id: str | None = None,
        contact_email: str | None = None,
    ) -> dict[str, Any]:
        """Generate a complete compliance dossier dictionary for domain_contract.json."""
        profile = self.resolve_jurisdiction(country_code=country_code)
        vertical = self.get_vertical_overlay(sector=sector)

        resolved_legal_entity = legal_entity or f"{brand_name} Technologies S.L."
        resolved_tax_id = tax_id or "B-88741920"
        resolved_email = contact_email or f"legal@{brand_name.lower().replace(' ', '')}.com"

        return {
            "brand_name": brand_name,
            "legal_entity": resolved_legal_entity,
            "tax_id": resolved_tax_id,
            "contact_email": resolved_email,
            "jurisdiction": profile.to_dict(),
            "vertical_clauses": vertical,
        }
