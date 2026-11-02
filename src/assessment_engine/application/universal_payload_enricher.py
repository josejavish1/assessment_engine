"""Universal Payload Enricher Application Service.

Orchestrates deterministic enrichment, multilingual taxonomy resolution,
forensic evidence binding, and actuarial telemetry injection across all
assessment towers (T1..T10).
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from assessment_engine.domain.contracts.enriched_payload_schema import (
    EnrichedTowerPayload,
)
from assessment_engine.domain.services.localization_resolver import (
    LocalizationResolver,
)
from assessment_engine.infrastructure.localization import t

logger = logging.getLogger(__name__)


class UniversalPayloadEnricher:
    """Deterministic enrichment engine for AS-IS Tower Blueprint Payloads."""

    def __init__(
        self,
        taxonomy_catalog: dict[str, Any],
        actuarial_gate_data: dict[str, Any],
        forensic_ledger: dict[str, Any],
        tenant_config: dict[str, Any],
    ) -> None:
        """Initializes the enricher with external domain catalogs and runtime state.

        Args:
            taxonomy_catalog: Parsed contents of taxonomy_multilingual.json.
            actuarial_gate_data: Validated financial telemetry from cfo_actuarial_gate.
            forensic_ledger: Extracted local forensic evidence indexed by Tower/Pillar.
            tenant_config: Runtime tenant metadata (client_name, language, currency, etc.).
        """
        self._taxonomy = taxonomy_catalog
        self._actuarial = actuarial_gate_data
        self._forensics = forensic_ledger
        self._tenant = tenant_config

    def enrich(self, raw_payload: dict[str, Any], tower_id: str) -> EnrichedTowerPayload:
        """Executes the full enrichment lifecycle on a raw tower payload.

        Args:
            raw_payload: The unpolished JSON dictionary (11 base keys).
            tower_id: Identifier of the current tower (e.g., 'T1', 'T2', ..., 'T10').

        Returns:
            EnrichedTowerPayload: Validated Pydantic model containing all 21 keys.
        """
        logger.info("Starting universal payload enrichment for Tower '%s'.", tower_id)
        working = dict(raw_payload)

        # Stage 1: Normalize Document & Tenant Metadata with primary language subtag
        working["document_meta"] = self._build_document_metadata(
            working.get("document_meta", {}), tower_id
        )
        norm_lang = str(working["document_meta"]["language"]).split("-")[0].lower()
        currency = working["document_meta"]["currency_code"]

        # Bind LocalizationResolver with the verified runtime locale
        resolver = LocalizationResolver(
            taxonomy_catalog=self._taxonomy,
            target_language=norm_lang,
        )
        working["document_meta"]["tower_label"] = resolver.resolve_tower_label(tower_id)

        # Stage 2: Resolve Multilingual Taxonomy & Enrich Pillar Profiles
        localized_map: dict[str, str] = {}
        pillar_narratives: dict[str, str] = {}
        self._enrich_pillars_and_kpis(
            working=working,
            tower_id=tower_id,
            norm_lang=norm_lang,
            resolver=resolver,
            localized_map=localized_map,
            pillar_narratives=pillar_narratives,
        )

        # Stage 3: Bind CFO Actuarial Gate Financial Telemetry
        working["financial_telemetry"] = self._bind_financial_telemetry(
            tower_id=tower_id, currency_code=currency, resolver=resolver
        )

        # Stage 4: Bind Forensic Evidence & Blast Radius keys (Completing 21 keys)
        tower_forensics = self._forensics.get(tower_id, {})
        working["forensic_evidence_ledger"] = tower_forensics.get("evidence_items", [])
        working["localized_taxonomy_map"] = localized_map
        working["pillar_executive_narratives"] = pillar_narratives
        working["benchmark_peer_comparison"] = tower_forensics.get("benchmarks", {})
        working["operational_blast_radius"] = tower_forensics.get("blast_radius", {})
        working["target_operating_model_gaps"] = tower_forensics.get("tom_gaps", [])
        working["technical_debt_quantification"] = self._quantify_technical_debt(
            tower_id, currency, resolver
        )
        working["governance_control_deficiencies"] = tower_forensics.get(
            "governance_deficiencies", []
        )
        working["enrichment_audit_trail"] = {
            "enricher_version": "2.1.0-universal",
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tower_id": tower_id,
            "locale_applied": norm_lang,
            "currency_applied": currency,
        }

        # Stage 5: Ensure Base Keys Exist Prior to Strict Contract Validation
        self._ensure_base_structural_keys(working)

        # Stage 6: Validate against strict 21-key Pydantic schema
        validated_payload = EnrichedTowerPayload.model_validate(working)
        logger.info(
            "Successfully enriched and validated Tower '%s' payload (21/21 keys verified).",
            tower_id,
        )
        return validated_payload

    def _build_document_metadata(
        self, existing_meta: dict[str, Any], tower_id: str
    ) -> dict[str, Any]:
        """Merges runtime tenant configuration with payload metadata dynamically."""
        raw_lang = (
            self._tenant.get("language")
            or existing_meta.get("language")
            or existing_meta.get("doc_lang")
            or "en"
        )
        norm_lang = str(raw_lang).split("-")[0].lower()
        return {
            **existing_meta,
            "client_name": self._tenant.get("client_name")
            or existing_meta.get("client_name", "Enterprise Client"),
            "tower_id": tower_id,
            "language": norm_lang,
            "doc_lang": norm_lang,
            "currency_code": self._tenant.get("currency_code")
            or existing_meta.get("currency_code", "USD"),
            "vertical_industry": self._tenant.get("vertical_industry", "enterprise_general"),
        }

    def _enrich_pillars_and_kpis(
        self,
        working: dict[str, Any],
        tower_id: str,
        norm_lang: str,
        resolver: LocalizationResolver,
        localized_map: dict[str, str],
        pillar_narratives: dict[str, str],
    ) -> None:
        """Resolves pillar/KPI taxonomy labels and synthesizes forensic executive readings."""
        profile_block = working.setdefault("pillar_score_profile", {})
        pillars = profile_block.get("pillars", [])

        # Sourced from taxonomy catalog with normalized locale subtag
        section_templates = self._taxonomy.get("narrative_templates", {}).get(
            norm_lang,
            self._taxonomy.get("narrative_templates", {}).get("en", {}),
        )

        for pillar in pillars:
            pillar_id = pillar.get("pillar_id", "P0")
            raw_score = float(pillar.get("raw_score", pillar.get("score", 0.0)))

            # Resolve localized labels dynamically
            localized_label = resolver.resolve_pillar_label(tower_id, pillar_id)
            pillar["pillar_id"] = pillar_id
            pillar["pillar_label"] = localized_label
            pillar["raw_score"] = raw_score
            pillar["formatted_score"] = (
                f"{resolver.format_decimal(raw_score)} / "
                f"{resolver.format_decimal(5.0)}"
            )
            pillar["maturity_tier_label"] = resolver.resolve_maturity_tier(raw_score)
            localized_map[pillar_id] = localized_label

            # Resolve deficient KPIs
            deficient_kpis = pillar.get("deficient_kpis", [])
            resolved_kpis = [resolver.resolve_kpi_label(k) for k in deficient_kpis]
            pillar["deficient_kpi_labels"] = resolved_kpis
            for k_id, k_label in zip(deficient_kpis, resolved_kpis):
                localized_map[k_id] = k_label

            # Preserve existing non-empty narrative if already present (Finding 4)
            existing_narrative = str(pillar.get("executive_reading") or "").strip()
            if existing_narrative:
                pillar_narratives[pillar_id] = existing_narrative
            else:
                narrative = self._synthesize_pillar_narrative(
                    pillar=pillar,
                    norm_lang=norm_lang,
                    section_templates=section_templates,
                )
                pillar["executive_reading"] = narrative
                pillar_narratives[pillar_id] = narrative

    def _synthesize_pillar_narrative(
        self,
        pillar: dict[str, Any],
        norm_lang: str,
        section_templates: dict[str, str],
    ) -> str:
        """Constructs structured executive reading using localized templates and locales.json."""
        # Use localized dictionary lookup for fallbacks to avoid hardcoded English strings (Finding 4)
        header_kpi = section_templates.get(
            "kpi_status_header",
            f"**{t('pillar_kpi_status_header', locale=norm_lang)}:**",
        )
        header_gaps = section_templates.get(
            "operational_gaps_header",
            f"**{t('pillar_operational_gaps_header', locale=norm_lang)}:**",
        )
        header_just = section_templates.get(
            "score_justification_header",
            f"**{t('pillar_score_justification_header', locale=norm_lang)}:**",
        )

        kpi_summary = pillar.get("kpi_diagnostic_summary") or ", ".join(
            pillar.get("deficient_kpi_labels", [])
        )
        gap_analysis = pillar.get("forensic_gap_analysis", "")
        justification = pillar.get("score_justification_text", "")

        return (
            f"{header_kpi}\n{kpi_summary}\n\n"
            f"{header_gaps}\n{gap_analysis}\n\n"
            f"{header_just}\n{justification}"
        ).strip()

    def _bind_financial_telemetry(
        self, tower_id: str, currency_code: str, resolver: LocalizationResolver
    ) -> dict[str, Any]:
        """Extracts and formats tower-specific financial metrics from the CFO Actuarial Gate."""
        tower_fin = self._actuarial.get("towers", {}).get(tower_id, {})
        risk_exp = float(tower_fin.get("annualized_risk_exposure", 0.0))
        capex = float(tower_fin.get("remediation_capex", 0.0))
        opex = float(tower_fin.get("remediation_opex", 0.0))

        return {
            "currency_code": currency_code,
            "total_annualized_risk_exposure": risk_exp,
            "formatted_risk_exposure": resolver.format_currency(risk_exp, currency_code),
            "remediation_capex_estimate": capex,
            "formatted_capex_estimate": resolver.format_currency(capex, currency_code),
            "remediation_opex_estimate": opex,
            "formatted_opex_estimate": resolver.format_currency(opex, currency_code),
            "actuarial_confidence_band": tower_fin.get("confidence_band", "P50-P90"),
        }

    def _quantify_technical_debt(
        self, tower_id: str, currency_code: str, resolver: LocalizationResolver
    ) -> dict[str, Any]:
        """Calculates localized technical debt metrics from actuarial data."""
        tower_fin = self._actuarial.get("towers", {}).get(tower_id, {})
        debt_principal = float(tower_fin.get("technical_debt_principal", 0.0))
        debt_interest = float(tower_fin.get("annual_maintenance_penalty", 0.0))
        return {
            "principal_amount": debt_principal,
            "formatted_principal": resolver.format_currency(debt_principal, currency_code),
            "annual_interest_penalty": debt_interest,
            "formatted_interest_penalty": resolver.format_currency(debt_interest, currency_code),
        }

    @staticmethod
    def _ensure_base_structural_keys(working: dict[str, Any]) -> None:
        """Guarantees that all 11 base keys exist with safe defaults if omitted upstream."""
        defaults: dict[str, Any] = {
            "executive_summary": {},
            "tower_score_summary": {},
            "pillar_score_profile": {"pillars": []},
            "kpi_assessment_matrix": [],
            "findings_register": [],
            "risk_heatmap_data": {},
            "remediation_roadmap": {},
            "architecture_topology": {},
            "compliance_mapping": {},
            "appendix_glossary": {},
        }
        for key, default_val in defaults.items():
            working.setdefault(key, default_val)
