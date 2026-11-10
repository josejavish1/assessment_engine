"""Universal Tower Synthesizer Application Service.

Delivers multi-tenant, zero-hardcoding generative prompt scoping and validated synthesis
for enterprise architectural assessments across global industry archetypes.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from assessment_engine.application.services.semantic_epistemic_router import (
    EpistemicContextPacket,
)


@dataclass(frozen=True)
class ClientAssessmentContext:
    """Immutable, typed domain context describing an enterprise client engagement."""

    client_name: str
    industry_vertical: str
    annual_revenue: float
    currency_code: str = "USD"
    regulatory_frameworks: tuple[str, ...] = field(default_factory=tuple)
    target_language: str = "en"
    operational_footprint: str = ""


@dataclass(frozen=True)
class ActuarialLossModel:
    """Immutable Actuarial Value Object decomposing Open FAIR primary and secondary loss factors."""

    annual_revenue: float
    currency_code: str = "USD"
    hourly_burn_ratio: float = 0.15

    @property
    def opex_hourly_burn_rate(self) -> float:
        """Baseline operational downtime loss rate per hour of catastrophic business halt."""
        calibrated_burn = (self.annual_revenue / 8760.0) * self.hourly_burn_ratio
        min_floor = max(0.01, self.annual_revenue * 0.000001)
        return max(min_floor, round(calibrated_burn, 2))

    def project_loss_parameters(
        self,
        downtime_hours: float = 4.0,
        emergency_capex_spend: float | None = None,
        threat_event_frequency: float = 2.0,
        vulnerability: float = 0.5,
    ) -> dict[str, float]:
        """Calculates Primary OpEx Loss, Secondary CapEx Spend, and FAIR Expected Loss parameters."""
        primary_opex_loss = round(downtime_hours * self.opex_hourly_burn_rate, 2)
        if emergency_capex_spend is not None and emergency_capex_spend >= 0.0:
            secondary_capex = round(emergency_capex_spend, 2)
        else:
            min_capex_floor = max(0.01, self.annual_revenue * 0.00001)
            secondary_capex = max(min_capex_floor, round(self.annual_revenue * 0.00025, 2))
        single_loss_expectancy = primary_opex_loss + secondary_capex
        fair_ale = round(threat_event_frequency * vulnerability * single_loss_expectancy, 2)
        fair_min = round(fair_ale * 0.25, 2)
        fair_p90 = round(fair_ale * 2.30, 2)
        fair_max = round(fair_ale * 3.80, 2)
        return {
            "opex_hourly_burn_rate": self.opex_hourly_burn_rate,
            "primary_opex_loss": primary_opex_loss,
            "secondary_capex_spend": secondary_capex,
            "fair_ale_score": fair_ale,
            "fair_min_score": fair_min,
            "fair_p90_score": fair_p90,
            "fair_max_score": fair_max,
        }


_SECTOR_DIRECTIVE_REGISTRY: dict[str, str] = {
    "financial": (
        "SECTOR DIRECTIVE (FINANCIAL SERVICES & FINTECH):\n"
        "- Evaluate ledger durability, sub-second transaction consistency, and real-time payment settlement.\n"
        "- Assess regulatory compliance under applicable financial mandates, statutory resilience frameworks, and client policies."
    ),
    "healthcare": (
        "SECTOR DIRECTIVE (HEALTHCARE & LIFE SCIENCES):\n"
        "- Prioritize patient safety, clinical availability (99.999%), and electronic health record confidentiality.\n"
        "- Ensure strict compliance with applicable clinical privacy laws, patient safety regulations, and medical device standards."
    ),
    "critical_infrastructure": (
        "SECTOR DIRECTIVE (CRITICAL INFRASTRUCTURE & ENERGY):\n"
        "- Address OT/SCADA air-gap integrity, grid telemetry continuity, and black-start disaster recovery.\n"
        "- Enforce zero-trust operational mandates and applicable critical infrastructure protection directives."
    ),
    "manufacturing": (
        "SECTOR DIRECTIVE (DISCRETE & PROCESS MANUFACTURING):\n"
        "- Evaluate plant floor OT uptime, industrial network segmentation (Purdue model), SCADA/DCS reliability, PLC safety integrity levels (SIL), and ERP-MES integration.\n"
        "- Assess predictive maintenance telemetry, production line scheduling latency, and industrial cyber security standards."
    ),
    "retail": (
        "SECTOR DIRECTIVE (RETAIL, E-COMMERCE & SUPPLY CHAIN LOGISTICS):\n"
        "- Assess omni-channel order pipeline latency, warehouse automation continuity, and checkout availability.\n"
        "- Evaluate supply chain partner EDI integration resilience and peak seasonality elasticity."
    ),
    "technology": (
        "SECTOR DIRECTIVE (TECHNOLOGY, SAAS & TELECOMMUNICATIONS):\n"
        "- Mandate multi-region active-active topology, automated canary deployments, and strict tenant isolation.\n"
        "- Enforce continuous compliance, rigorous SLA governance, and sub-minute mean time to recovery (MTTR)."
    ),
}


def _resolve_sector_directive(industry_vertical: str) -> str:
    """Resolves tailored domain directives from normalized industry archetype."""
    ind_lower = industry_vertical.lower()
    if any(t in ind_lower for t in ("fintech", "bank", "financial", "insurance", "capital")):
        return _SECTOR_DIRECTIVE_REGISTRY["financial"]
    if any(t in ind_lower for t in ("health", "pharma", "clinical", "hospital", "life sciences", "biotech")):
        return _SECTOR_DIRECTIVE_REGISTRY["healthcare"]
    if any(t in ind_lower for t in ("utilities", "energy", "grid", "oil", "gas", "nuclear", "water")):
        return _SECTOR_DIRECTIVE_REGISTRY["critical_infrastructure"]
    if any(t in ind_lower for t in ("manufacturing", "industrial", "automotive", "aerospace", "materials", "mining")):
        return _SECTOR_DIRECTIVE_REGISTRY["manufacturing"]
    if any(t in ind_lower for t in ("retail", "ecommerce", "logistics", "shipping", "transport", "cpg")):
        return _SECTOR_DIRECTIVE_REGISTRY["retail"]
    if any(t in ind_lower for t in ("tech", "saas", "cloud", "software", "telecom")):
        return _SECTOR_DIRECTIVE_REGISTRY["technology"]
    return (
        f"SECTOR DIRECTIVE ({industry_vertical.upper()}):\n"
        "- Maintain operational continuity and SLA resilience aligned with enterprise business models."
    )


def _format_pillars_description(tower_definition: dict[str, Any], tower_code: str) -> tuple[str, int]:
    """Formats canonical pillar list and returns total pillar count."""
    pillars_meta = tower_definition.get("pillars", {})
    pillars_lines: list[str] = []
    if isinstance(pillars_meta, dict):
        for pid, pdata in sorted(pillars_meta.items()):
            pname = pdata.get("canonical_name", pid) if isinstance(pdata, dict) else str(pdata)
            pillars_lines.append(f"- {pid}: {pname}")
    elif isinstance(pillars_meta, list):
        for p in pillars_meta:
            if isinstance(p, dict):
                pid = str(p.get("pillar_id", ""))
                pname = str(p.get("canonical_name") or p.get("pillar_name") or pid)
                pillars_lines.append(f"- {pid}: {pname}")
    count = len(pillars_lines) if pillars_lines else 5
    desc = "\n".join(pillars_lines) if pillars_lines else f"- {tower_code}.P1 to {tower_code}.P{count}"
    return desc, count


class UniversalTowerSynthesizer:
    """Universal synthesis engine orchestrating dynamic meta-prompts and structured validation."""

    def build_synthesis_prompt(
        self,
        context: ClientAssessmentContext,
        tower_code: str,
        evidence_packet: EpistemicContextPacket,
        tower_definition: dict[str, Any],
    ) -> str:
        """Construct a rigorous, decoupled synthesis prompt parameterized strictly by dynamic context."""
        tower_name = tower_definition.get("tower_name", tower_code)
        frameworks_str = ", ".join(context.regulatory_frameworks) if context.regulatory_frameworks else "Industry Standard Frameworks"
        sector_directives = _resolve_sector_directive(context.industry_vertical)

        # S2A Context Partitioning: Filter out future TO-BE aspirations from AS-IS diagnostic prompt context
        asis_props = (
            evidence_packet.get_asis_facts()
            if hasattr(evidence_packet, "get_asis_facts")
            else evidence_packet.propositions
        )
        propositions_block = (
            "\n".join(
                f"- [Turn {p.turn_index}] ({p.polarity}): {p.text}"
                for p in asis_props
            )
            if asis_props
            else "No direct empirical production propositions recorded for this domain (CONFIRMED_ABSENCE_OF_PRODUCTION_CAPABILITY)."
        )

        pillars_desc, pillar_count = _format_pillars_description(tower_definition, tower_code)

        prompt = f"""### SYSTEM ROLE & MISSION:
You are an elite Principal Enterprise Systems Architect and Lead Forensic Auditor conducting an assessment for:
Client: {context.client_name}
Industry Vertical: {context.industry_vertical}
Annual Revenue: {context.annual_revenue:,.2f} {context.currency_code}
Applicable Regulatory Frameworks: {frameworks_str}
Target Language: {context.target_language}

### TARGET DOMAIN:
Domain Code: {tower_code}
Domain Scope: {tower_name}

CANONICAL {pillar_count} PILLARS FOR {tower_code}:
{pillars_desc}

### EMPIRICAL EVIDENCE DOSSIER:
{propositions_block}

### SECTOR & GOVERNANCE DIRECTIVES:
{sector_directives}

### GROUNDING & SEVERITY RULES:
1. ONLY make claims supported by the evidence above. Never hallucinate non-existent platforms or tools.
2. Calibrate severity strictly based on operational and regulatory impact in {context.industry_vertical}:
   - CRITICAL: Direct production halts, safety/clinical hazards, uncontained single points of failure, unpatched core vulnerabilities (>180 days), shared root/admin credentials, compliance revocation under {frameworks_str}.
   - HIGH: Major resilience, capacity, or recovery time violations (RTO/RPO) without immediate catastrophic halt.
   - MEDIUM: Operational friction, documentation drift, non-critical monitoring delays.
   - LOW: Minor process hygiene.
   - NEVER emit null, empty, or missing severity.
3. ANTI-BOILERPLATE MANDATE:
   - NEVER use generic fill-in-the-blank phrasing like "Deficit in [X] and requirement for technical control automation".
   - Every finding and business risk must be detailed, technical, concrete, and grounded in the client's infrastructure.
   - Ground every observation in observed operational metrics, resource contention, and workload isolation boundaries.
4. STORAGE PROTOCOL ARCHITECTURAL INVARIANT:
   - Accurately distinguish Block, File, and Object storage tiers based strictly on observed workload mechanics. Object storage may only be cited for asynchronous API consumption, backup targets, or log archival; do not assume POSIX consistency for unstructured object stores.
5. EMPIRICAL REALITY OVER SURVEY CLAIMS:
   - If an enterprise has zero empirical deployment or minimal adoption in production for a capability or architectural layer, score that pillar strictly as Initial/Ad-hoc (1.00 to 1.50) regardless of future aspirations. Never award high maturity (Level 4 or 5) to a capability that is purely in planning, PoC, or roadmap phase.
6. PURE AS-IS DIAGNOSTIC INVARIANT (ZERO PRESCRIPTION):
   - Your mandate is strictly diagnostic for Volume 1 (AS-IS Baseline). You evaluate what exists today, how it functions under load, where its structural fault lines lie, and the operational/commercial consequences of status-quo inertia.
   - ZERO PRESCRIPTION: Do NOT suggest fixes, target states, migrations, hardware purchases, hiring plans, or CAPEX/OPEX allocations. Ban all prescriptive verbs and modal imperatives ("must", "should", "needs to", "recommend", "require upgrading", "propose", "migrate").
   - Establish urgency exclusively by projecting the blast-radius of current debt if unmitigated.
7. ANTI-FORMULAIC PROSE & DOMAIN-NATIVE VOICE:
   - Never use a repetitive sentence template across sections. Every tower must read as if written by a senior specialist steeped in the specific architectural physics of that layer (e.g., electromechanical and thermal continuity for Facilities; resource contention and hypervisor headroom for Compute; routing transit and perimeter ingress/egress for Networks; data persistence and storage IOPS for Storage; privilege sprawl and credential governance for Security; core transactional processing and edge operational survivability for Core Systems/Operations).
   - Open directly with the sharpest architectural paradox or bottleneck discovered in the evidence. Never open with generic filler ("In this section...", "The evaluation of [Tower] reveals...").
8. DOMAIN JURISDICTION & ORTHOGONALITY (KILL THE ECHO CHAMBER):
   - A technical fact, strength, or risk may ONLY be cited if it is a primary native mechanism of THIS specific tower.
   - Do NOT use cross-domain facts as generic filler (e.g. do not cite central monitoring tools or remote DBA personnel in towers where they are not primary architectural drivers).

### OUTPUT SCHEMA:
Output ONLY a valid JSON object matching this structure (write prose in {context.target_language}):
{{
  "executive_snapshot": {{
    "bottom_line": "Bespoke diagnostic synthesis of status quo inertia, technical debt, and business blast radius (write prose in {context.target_language})...",
    "operational_benefits": [
      "Specific operational strength native to this domain's architecture...",
      "Specific operational strength 2...",
      "Specific operational strength 3..."
    ],
    "structural_risks": [
      "Concrete structural risk native to this domain [Component/Vendor + Metric/Threshold + Business Blast Radius]...",
      "Concrete structural risk 2...",
      "Concrete structural risk 3..."
    ]
  }},
  "pillars_analysis": [
    {{
      "pillar_id": "{tower_code}.P1",
      "pillar_name": "...",
      "score": 1.25,
      "target_score": 4.0,
      "thought_process": "...",
      "asis_architecture_description": "Comprehensive technical description (2-3 paragraphs)...",
      "health_check_asis": [
        {{
          "node_id": "{tower_code.lower()}-p1-hc-01",
          "capability": "...",
          "finding": "Specific technical finding grounded in primary evidence...",
          "business_risk": "Concrete business and financial impact...",
          "severity": "CRITICAL",
          "literal_evidence": "...",
          "threat_event_frequency": 3,
          "vulnerability_level": 3,
          "loss_magnitude": 3,
          "fair_ale_score": "<calibrated_annual_loss_numeric>",
          "fair_p90_score": "<calibrated_p90_loss_numeric>",
          "fair_min_score": "<calibrated_min_loss_numeric>",
          "fair_max_score": "<calibrated_max_loss_numeric>"
        }}
      ]
    }}
  ]
}}
"""
        return prompt

    def parse_and_validate_synthesis(
        self,
        raw_response: dict[str, Any],
        context: ClientAssessmentContext,
        tower_code: str = "",
    ) -> dict[str, Any]:
        """Validates and heals LLM synthesis payload, enforcing Open FAIR monotonic consistency."""
        validated = copy.deepcopy(raw_response)
        if "pillars_analysis" not in validated or not isinstance(validated["pillars_analysis"], list):
            validated["pillars_analysis"] = []

        actuarial = ActuarialLossModel(
            annual_revenue=float(context.annual_revenue),
            currency_code=context.currency_code,
        )
        default_loss = actuarial.project_loss_parameters()

        for p in validated["pillars_analysis"]:
            if not isinstance(p, dict):
                continue
            if "health_check_asis" not in p or not isinstance(p["health_check_asis"], list):
                p["health_check_asis"] = []
            for hc in p["health_check_asis"]:
                if not isinstance(hc, dict):
                    continue
                if "severity" not in hc or not str(hc["severity"]).strip():
                    hc["severity"] = "MEDIUM"

                def _parse_fair_num(raw_val: Any, fallback: float) -> float:
                    if raw_val is None:
                        return fallback
                    if isinstance(raw_val, (int, float)):
                        return float(raw_val)
                    try:
                        from assessment_engine.domain.actuarial_scale_calibrator import (
                            safe_float as actuarial_safe_float,
                        )
                        res = actuarial_safe_float(raw_val, allow_zero=True)
                        if res is not None:
                            return float(res)
                    except Exception:
                        pass
                    try:
                        import re
                        raw_str = str(raw_val).strip()
                        clean = re.sub(r"^[^\d\-+]+", "", raw_str)
                        clean = re.sub(r"[^\d]+$", "", clean).strip()
                        if "," in clean and "." in clean:
                            clean = clean.replace(",", "") if clean.rfind(".") > clean.rfind(",") else clean.replace(".", "").replace(",", ".")
                        elif "," in clean:
                            clean = clean.replace(",", ".")
                        return float(clean)
                    except (ValueError, TypeError):
                        return fallback

                ale = _parse_fair_num(hc.get("fair_ale_score"), default_loss["fair_ale_score"])
                min_s = _parse_fair_num(hc.get("fair_min_score"), ale * 0.25)
                p90_s = _parse_fair_num(hc.get("fair_p90_score"), ale * 2.30)
                max_s = _parse_fair_num(hc.get("fair_max_score"), ale * 3.80)

                # Enforce Open FAIR monotonicity invariant: min <= ale <= p90 <= max
                min_s = min(min_s, ale)
                p90_s = max(p90_s, ale)
                max_s = max(max_s, p90_s)

                hc["fair_ale_score"] = ale
                hc["fair_min_score"] = min_s
                hc["fair_p90_score"] = p90_s
                hc["fair_max_score"] = max_s
                hc["quantification_status"] = "DRAFT"

        return validated
