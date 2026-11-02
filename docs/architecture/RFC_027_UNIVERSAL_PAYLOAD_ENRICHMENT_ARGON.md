# Architectural RFC: Universal Payload Enricher & Elimination of Split-Brain Telemetry

| Metadata | Details |
| :--- | :--- |
| **Status** | APPROVED FOR IMPLEMENTATION |
| **Author** | Principal Systems Architect & Core Pipeline Engineering |
| **Scope** | Core Assessment Engine (`T1` through `T10` Universal Execution) |
| **Target Deprecation** | `scripts/polish_payload_and_render.py` |
| **Language Compliance** | 100% Technical English (Zero hardcoded locales/tenants) |

---

## 1. Executive Summary & Problem Statement

### 1.1 The "Split-Brain" Anti-Pattern
Currently, the Assessment Engine suffers from a severe **Pet vs. Cattle** architectural anti-pattern:
* **The "Pet" (`T1`):** Tower 1 payloads are manually intercepted post-pipeline by an ad-hoc, unscalable script (`scripts/polish_payload_and_render.py`). This script hardcodes client names, locale-specific narratives, localized taxonomy strings, and 21 advanced structural keys directly into the JSON payload before rendering.
* **The "Cattle" (`T2..T10`):** Towers 2 through 10 bypass this manual script, exiting the pipeline with only 11 basic structural keys, unlocalized English capability identifiers, raw unformatted numbers, and missing forensic evidence bindings.

### 1.2 Architectural Objective
Eradicate `scripts/polish_payload_and_render.py` and introduce a deterministic, idempotent, and tenant-agnostic pipeline stage: the **`UniversalPayloadEnricher`**. Every tower (`T1..T10`), regardless of client size, industry vertical, ISO-4217 currency, or ISO-639-1 language code, must pass through the exact same enrichment, localization, and financial computation gates before document rendering.

---

## 2. Target Architecture & Directory Structure

Following Domain-Driven Design (DDD) and Clean Architecture principles, we separate **Domain Models** (the 21-key schema contract), **Infrastructure Adapters** (catalog loaders, currency formatters), and **Application Services** (the enrichment orchestrator).

```text
src/
└── assessment_engine/
    ├── domain/
    │   ├── contracts/
    │   │   └── enriched_payload_schema.py      # Strict Pydantic v2 contract (All 21 keys)
    │   └── services/
    │       ├── localization_resolver.py        # Multilingual taxonomy & locale formatting
    │       ├── financial_telemetry_binder.py   # CFO Actuarial Gate & ISO-4217 binding
    │       └── forensic_narrative_synthesizer.py # Dynamic evidence-to-pillar synthesis
    ├── infrastructure/
    │   └── repositories/
    │       ├── taxonomy_repository.py          # Loads taxonomy_multilingual.json
    │       └── actuarial_repository.py         # Loads cfo_actuarial_gate outputs
    ├── application/
    │   └── universal_payload_enricher.py       # Core Orchestrator (Replaces the hack script)
    └── cli/
        └── enrich_tower_payload_cli.py         # Subprocess entrypoint for run_tower_pipeline.py
```

---

## 3. Core Blueprints (100% Technical English)

### 3.1 Domain Contract: Enforcing the 21-Key Parity
**File:** `src/assessment_engine/domain/contracts/enriched_payload_schema.py`

This module guarantees that no tower can proceed to the DOCX renderer with only 11 keys. If any of the 21 structural keys are missing, validation fails deterministically.

```python
"""Domain schema definitions for the enriched tower annex payload.

Enforces structural parity across all assessment towers (T1..T10) prior to
document rendering, preventing split-brain schema degradation.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    """Tenant and localization metadata extracted from runtime configuration."""

    model_config = ConfigDict(extra="allow")

    client_name: str = Field(..., min_length=1)
    tower_id: str = Field(..., pattern=r"^T([1-9]|10)$")
    language: str = Field(..., pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
    doc_lang: str = Field(..., pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
    currency_code: str = Field(..., pattern=r"^[A-Z]{3}$")
    vertical_industry: str = Field(default="enterprise_general")


class EnrichedPillarProfile(BaseModel):
    """Enriched structural representation of a single capability pillar."""

    model_config = ConfigDict(extra="allow")

    pillar_id: str
    pillar_label: str
    raw_score: float = Field(..., ge=0.0, le=5.0)
    formatted_score: str
    maturity_tier_label: str
    executive_reading: str
    deficient_kpi_labels: list[str] = Field(default_factory=list)
    forensic_evidence_refs: list[str] = Field(default_factory=list)


class FinancialTelemetryBlock(BaseModel):
    """Actuarial and financial exposure metrics bound from the CFO Gate."""

    model_config = ConfigDict(extra="allow")

    currency_code: str
    total_annualized_risk_exposure: float
    formatted_risk_exposure: str
    remediation_capex_estimate: float
    formatted_capex_estimate: str
    remediation_opex_estimate: float
    formatted_opex_estimate: str
    actuarial_confidence_band: str


class EnrichedTowerPayload(BaseModel):
    """Master contract enforcing the 21 mandatory structural keys across all towers."""

    model_config = ConfigDict(extra="allow")

    # Core 11 Base Keys (Normalized)
    document_meta: DocumentMetadata
    executive_summary: dict[str, Any]
    tower_score_summary: dict[str, Any]
    pillar_score_profile: dict[str, list[EnrichedPillarProfile] | Any]
    kpi_assessment_matrix: list[dict[str, Any]]
    findings_register: list[dict[str, Any]]
    risk_heatmap_data: dict[str, Any]
    remediation_roadmap: dict[str, Any]
    architecture_topology: dict[str, Any]
    compliance_mapping: dict[str, Any]
    appendix_glossary: dict[str, Any]

    # Advanced 10 Enriched Keys (Previously exclusive to T1 manual scripts)
    financial_telemetry: FinancialTelemetryBlock
    forensic_evidence_ledger: list[dict[str, Any]]
    localized_taxonomy_map: dict[str, str]
    pillar_executive_narratives: dict[str, str]
    benchmark_peer_comparison: dict[str, Any]
    operational_blast_radius: dict[str, Any]
    target_operating_model_gaps: list[dict[str, Any]]
    technical_debt_quantification: dict[str, Any]
    governance_control_deficiencies: list[dict[str, Any]]
    enrichment_audit_trail: dict[str, str]
```

---

### 3.2 Domain Services: Localization & Financial Resolution
**File:** `src/assessment_engine/domain/services/localization_resolver.py`

Replaces all hardcoded translations and number formatting (e.g., `2,50` vs `2.50`) with deterministic locale-driven resolution against `taxonomy_multilingual.json`.

```python
"""Multilingual taxonomy resolution and locale-aware formatting service."""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

logger = logging.getLogger(__name__)


class LocalizationResolver:
    """Resolves taxonomy identifiers and formats numbers dynamically by ISO locale."""

    # Locale-specific decimal and thousand separators
    LOCALE_NUMERIC_CONVENTIONS: dict[str, tuple[str, str]] = {
        "en": (".", ","),
        "ja": (".", ","),
        "es": (",", "."),
        "pt": (",", "."),
        "de": (",", "."),
        "fr": (",", " "),
    }

    def __init__(self, taxonomy_catalog: dict[str, Any], target_language: str) -> None:
        self._catalog = taxonomy_catalog
        self._lang = target_language.split("-")[0].lower()
        if self._lang not in self.LOCALE_NUMERIC_CONVENTIONS:
            logger.warning(
                "Unsupported language '%s' requested; falling back to 'en'.",
                self._lang,
            )
            self._lang = "en"

    def resolve_tower_label(self, tower_id: str) -> str:
        """Resolves the localized display name for a given Tower ID."""
        node = self._catalog.get("towers", {}).get(tower_id, {})
        return self._extract_localized_string(node, fallback=tower_id)

    def resolve_pillar_label(self, tower_id: str, pillar_id: str) -> str:
        """Resolves the localized display name for a given Pillar ID."""
        node = (
            self._catalog.get("towers", {})
            .get(tower_id, {})
            .get("pillars", {})
            .get(pillar_id, {})
        )
        return self._extract_localized_string(node, fallback=pillar_id)

    def resolve_kpi_label(self, kpi_id: str) -> str:
        """Resolves the full localized string for a KPI identifier (e.g., T2.P1.K3)."""
        node = self._catalog.get("kpis", {}).get(kpi_id, {})
        localized_name = self._extract_localized_string(node, fallback="Unmapped Capability")
        return f"{kpi_id} - {localized_name}"

    def resolve_maturity_tier(self, score: float) -> str:
        """Maps a numerical score (0.0 - 5.0) to its localized maturity tier label."""
        tiers = self._catalog.get("maturity_tiers", {})
        bucket = str(int(Decimal(str(score)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
        node = tiers.get(bucket, {})
        return self._extract_localized_string(node, fallback=f"Tier {bucket}")

    def format_decimal(self, value: float, decimal_places: int = 2) -> str:
        """Formats a float according to the target language's typographic conventions."""
        quantizer = Decimal("10") ** -decimal_places
        dec_val = Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)
        raw_str = f"{dec_val:,.{decimal_places}f}"

        dec_sep, thousand_sep = self.LOCALE_NUMERIC_CONVENTIONS[self._lang]
        # Swap via placeholder to avoid collision
        return (
            raw_str.replace(",", "__THOUSAND__")
            .replace(".", dec_sep)
            .replace("__THOUSAND__", thousand_sep)
        )

    def format_currency(self, amount: float, currency_code: str) -> str:
        """Formats monetary values with ISO-4217 currency code and locale separators."""
        formatted_num = self.format_decimal(amount, decimal_places=0)
        return f"{formatted_num} {currency_code.upper()}"

    def _extract_localized_string(self, node: dict[str, Any], fallback: str) -> str:
        """Extracts language-specific text from a taxonomy dictionary node."""
        if not isinstance(node, dict):
            return fallback
        labels = node.get("labels", {})
        return labels.get(self._lang) or labels.get("en") or fallback
```

---

### 3.3 Application Service: The Universal Payload Enricher
**File:** `src/assessment_engine/application/universal_payload_enricher.py`

This is the core engine that replaces `scripts/polish_payload_and_render.py`. It orchestrates metadata normalization, taxonomy resolution, forensic evidence binding, and financial telemetry injection across any tower (`T1..T10`).

```python
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

        target_lang = self._tenant.get("language", "en")
        self._resolver = LocalizationResolver(
            taxonomy_catalog=self._taxonomy,
            target_language=target_lang,
        )

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

        # Stage 1: Normalize Document & Tenant Metadata
        working["document_meta"] = self._build_document_metadata(
            working.get("document_meta", {}), tower_id
        )
        lang = working["document_meta"]["language"]
        currency = working["document_meta"]["currency_code"]

        # Stage 2: Resolve Multilingual Taxonomy & Enrich Pillar Profiles
        localized_map: dict[str, str] = {}
        pillar_narratives: dict[str, str] = {}
        self._enrich_pillars_and_kpis(
            working=working,
            tower_id=tower_id,
            localized_map=localized_map,
            pillar_narratives=pillar_narratives,
        )

        # Stage 3: Bind CFO Actuarial Gate Financial Telemetry
        working["financial_telemetry"] = self._bind_financial_telemetry(
            tower_id=tower_id, currency_code=currency
        )

        # Stage 4: Bind Forensic Evidence & Blast Radius keys (Completing the 21 keys)
        tower_forensics = self._forensics.get(tower_id, {})
        working["forensic_evidence_ledger"] = tower_forensics.get("evidence_items", [])
        working["localized_taxonomy_map"] = localized_map
        working["pillar_executive_narratives"] = pillar_narratives
        working["benchmark_peer_comparison"] = tower_forensics.get("benchmarks", {})
        working["operational_blast_radius"] = tower_forensics.get("blast_radius", {})
        working["target_operating_model_gaps"] = tower_forensics.get("tom_gaps", [])
        working["technical_debt_quantification"] = self._quantify_technical_debt(
            tower_id, currency
        )
        working["governance_control_deficiencies"] = tower_forensics.get(
            "governance_deficiencies", []
        )
        working["enrichment_audit_trail"] = {
            "enricher_version": "2.0.0-universal",
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tower_id": tower_id,
            "locale_applied": lang,
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
        """Merges runtime tenant configuration with payload metadata without hardcoding."""
        lang = self._tenant.get("language") or existing_meta.get("language") or "en"
        return {
            **existing_meta,
            "client_name": self._tenant.get("client_name")
            or existing_meta.get("client_name", "Enterprise Client"),
            "tower_id": tower_id,
            "tower_label": self._resolver.resolve_tower_label(tower_id),
            "language": lang,
            "doc_lang": lang,
            "currency_code": self._tenant.get("currency_code")
            or existing_meta.get("currency_code", "USD"),
            "vertical_industry": self._tenant.get("vertical_industry", "enterprise_general"),
        }

    def _enrich_pillars_and_kpis(
        self,
        working: dict[str, Any],
        tower_id: str,
        localized_map: dict[str, str],
        pillar_narratives: dict[str, str],
    ) -> None:
        """Resolves pillar/KPI taxonomy labels and synthesizes forensic executive readings."""
        profile_block = working.setdefault("pillar_score_profile", {})
        pillars = profile_block.get("pillars", [])

        section_templates = self._taxonomy.get("narrative_templates", {}).get(
            self._tenant.get("language", "en"),
            self._taxonomy.get("narrative_templates", {}).get("en", {}),
        )

        for pillar in pillars:
            pillar_id = pillar.get("pillar_id", "P0")
            raw_score = float(pillar.get("raw_score", pillar.get("score", 0.0)))

            # Resolve localized labels dynamically
            localized_label = self._resolver.resolve_pillar_label(tower_id, pillar_id)
            pillar["pillar_id"] = pillar_id
            pillar["pillar_label"] = localized_label
            pillar["raw_score"] = raw_score
            pillar["formatted_score"] = (
                f"{self._resolver.format_decimal(raw_score)} / "
                f"{self._resolver.format_decimal(5.0)}"
            )
            pillar["maturity_tier_label"] = self._resolver.resolve_maturity_tier(raw_score)
            localized_map[pillar_id] = localized_label

            # Resolve deficient KPIs
            deficient_kpis = pillar.get("deficient_kpis", [])
            resolved_kpis = [self._resolver.resolve_kpi_label(k) for k in deficient_kpis]
            pillar["deficient_kpi_labels"] = resolved_kpis
            for k_id, k_label in zip(deficient_kpis, resolved_kpis):
                localized_map[k_id] = k_label

            # Synthesize deterministic forensic narrative if not already enriched
            narrative = self._synthesize_pillar_narrative(
                pillar=pillar,
                section_templates=section_templates,
            )
            pillar["executive_reading"] = narrative
            pillar_narratives[pillar_id] = narrative

    def _synthesize_pillar_narrative(
        self,
        pillar: dict[str, Any],
        section_templates: dict[str, str],
    ) -> str:
        """Constructs structured executive reading from forensic evidence and templates."""
        header_kpi = section_templates.get("kpi_status_header", "**Capability Status (KPIs):**")
        header_gaps = section_templates.get(
            "operational_gaps_header", "**Operational Gaps & Consequences:**"
        )
        header_just = section_templates.get(
            "score_justification_header", "**Score Justification:**"
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
        self, tower_id: str, currency_code: str
    ) -> dict[str, Any]:
        """Extracts and formats tower-specific financial metrics from the CFO Actuarial Gate."""
        tower_fin = self._actuarial.get("towers", {}).get(tower_id, {})
        risk_exp = float(tower_fin.get("annualized_risk_exposure", 0.0))
        capex = float(tower_fin.get("remediation_capex", 0.0))
        opex = float(tower_fin.get("remediation_opex", 0.0))

        return {
            "currency_code": currency_code,
            "total_annualized_risk_exposure": risk_exp,
            "formatted_risk_exposure": self._resolver.format_currency(risk_exp, currency_code),
            "remediation_capex_estimate": capex,
            "formatted_capex_estimate": self._resolver.format_currency(capex, currency_code),
            "remediation_opex_estimate": opex,
            "formatted_opex_estimate": self._resolver.format_currency(opex, currency_code),
            "actuarial_confidence_band": tower_fin.get("confidence_band", "P50-P90"),
        }

    def _quantify_technical_debt(
        self, tower_id: str, currency_code: str
    ) -> dict[str, Any]:
        """Calculates localized technical debt metrics from actuarial data."""
        tower_fin = self._actuarial.get("towers", {}).get(tower_id, {})
        debt_principal = float(tower_fin.get("technical_debt_principal", 0.0))
        debt_interest = float(tower_fin.get("annual_maintenance_penalty", 0.0))
        return {
            "principal_amount": debt_principal,
            "formatted_principal": self._resolver.format_currency(debt_principal, currency_code),
            "annual_interest_penalty": debt_interest,
            "formatted_interest_penalty": self._resolver.format_currency(
                debt_interest, currency_code
            ),
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
```

---

## 4. Pipeline Integration (`run_tower_pipeline.py`)

To preserve the isolated subprocess DAG architecture of `run_tower_pipeline.py`, we expose `UniversalPayloadEnricher` via a dedicated CLI entrypoint (`src/assessment_engine/cli/enrich_tower_payload_cli.py`) and register it as a mandatory stage immediately preceding the DOCX rendering step for **every tower (`T1..T10`)**.

### 4.1 Subprocess CLI Entrypoint
**File:** `src/assessment_engine/cli/enrich_tower_payload_cli.py`

```python
"""CLI entrypoint for executing UniversalPayloadEnricher within an isolated pipeline step."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from assessment_engine.application.universal_payload_enricher import (
    UniversalPayloadEnricher,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("enrich_tower_payload_cli")


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for the universal enrichment step."""
    parser = argparse.ArgumentParser(
        description="Enrich raw tower payload with taxonomy, forensics, and CFO telemetry."
    )
    parser.add_argument("--tower-id", required=True, help="Tower ID (T1..T10)")
    parser.add_argument("--input-payload", type=Path, required=True)
    parser.add_argument("--output-payload", type=Path, required=True)
    parser.add_argument("--taxonomy-path", type=Path, required=True)
    parser.add_argument("--actuarial-gate-path", type=Path, required=True)
    parser.add_argument("--forensic-ledger-path", type=Path, required=True)
    parser.add_argument("--tenant-config-path", type=Path, required=True)
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    if not path.exists():
        logger.warning("File not found at '%s'; returning empty dict.", path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    """Executes the enrichment pipeline stage."""
    args = parse_args()

    raw_payload = _load_json(args.input_payload)
    if not raw_payload:
        logger.error("Input payload at '%s' is empty or missing.", args.input_payload)
        return 1

    enricher = UniversalPayloadEnricher(
        taxonomy_catalog=_load_json(args.taxonomy_path),
        actuarial_gate_data=_load_json(args.actuarial_gate_path),
        forensic_ledger=_load_json(args.forensic_ledger_path),
        tenant_config=_load_json(args.tenant_config_path),
    )

    enriched_model = enricher.enrich(raw_payload=raw_payload, tower_id=args.tower_id)

    args.output_payload.parent.mkdir(parents=True, exist_ok=True)
    args.output_payload.write_text(
        enriched_model.model_dump_json(indent=2),
        encoding="utf-8",
    )
    logger.info("Enriched payload written to '%s'.", args.output_payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 4.2 Hooking into `run_tower_pipeline.py`
Within `run_tower_pipeline.py`, the DAG execution loop iterates dynamically over all configured towers (`T1..T10`) and invokes the enrichment step before rendering:

```python
# Inside run_tower_pipeline.py orchestration loop:

ALL_TOWERS: tuple[str, ...] = tuple(f"T{i}" for i in range(1, 11))

async def execute_enrichment_and_render_stage(
    tower_id: str,
    case_runtime_dir: Path,
    env: dict[str, str],
) -> None:
    """Executes universal enrichment followed by DOCX rendering for a single tower."""
    python_bin = resolve_python_bin()
    raw_payload_path = resolve_blueprint_payload_path(case_runtime_dir, tower_id, enriched=False)
    enriched_payload_path = resolve_blueprint_payload_path(case_runtime_dir, tower_id, enriched=True)
    template_path = resolve_tower_annex_template_path()

    # Step A: Universal Payload Enrichment (Applies to T1..T10 identically)
    enrich_cmd = [
        python_bin,
        "-m",
        "assessment_engine.cli.enrich_tower_payload_cli",
        "--tower-id", tower_id,
        "--input-payload", str(raw_payload_path),
        "--output-payload", str(enriched_payload_path),
        "--taxonomy-path", str(case_runtime_dir / "catalogs/taxonomy_multilingual.json"),
        "--actuarial-gate-path", str(case_runtime_dir / "actuarial/cfo_actuarial_gate.json"),
        "--forensic-ledger-path", str(case_runtime_dir / "forensics/evidence_ledger.json"),
        "--tenant-config-path", str(case_runtime_dir / "config/tenant_meta.json"),
    ]
    await run_step_async(
        cmd_args=enrich_cmd,
        env=env,
        step_name=f"universal_payload_enricher_{tower_id.lower()}",
    )

    # Step B: Deterministic DOCX Rendering from Validated 21-Key Payload
    render_cmd = [
        python_bin,
        "-m",
        "assessment_engine.cli.render_tower_docx_cli",
        "--payload-path", str(enriched_payload_path),
        "--template-path", str(template_path),
        "--output-docx", str(case_runtime_dir / "out" / tower_id / f"{tower_id}_ASIS_MASTER.docx"),
    ]
    await run_step_async(
        cmd_args=render_cmd,
        env=env,
        step_name=f"render_master_docx_{tower_id.lower()}",
    )
```

---

## 5. Verification Matrix & Anti-Pattern Eradication Guarantee

| Architectural Dimension | Legacy State (`polish_payload_and_render.py`) | Target State (`UniversalPayloadEnricher`) |
| :--- | :--- | :--- |
| **Tower Coverage** | `T1` only (Manual execution). `T2..T10` left raw. | **100% Universal (`T1..T10`)** via automated DAG step. |
| **Schema Structural Keys** | Asymmetric: 21 keys in `T1`, 11 keys in `T2..T10`. | **Strict 21-Key Contract** enforced via Pydantic `EnrichedTowerPayload`. |
| **Tenant & Locale Hardcoding** | Hardcoded client names, `"es"` locale, and local facility names in Python script. | **Zero Hardcoding.** Extracted dynamically from `tenant_meta.json` and `evidence_ledger.json`. |
| **Taxonomy & Language Support** | Manual string overrides in source code. | **Dynamic Resolution** via `LocalizationResolver` (`en`, `es`, `pt`, `fr`, `de`, `ja`). |
| **Financial & Currency Support** | Unbound or static strings. | **ISO-4217 Dynamic Binding** directly from `cfo_actuarial_gate.json`. |
| **Codebase Language Standard** | Mixed English code and hardcoded non-English strings. | **100% Technical English** across all modules, identifiers, and docstrings. |

### Deprecation Protocol
1. Merge `UniversalPayloadEnricher` and its CLI wrapper into `src/assessment_engine/`.
2. Update `run_tower_pipeline.py` to execute `universal_payload_enricher_t{1..10}` prior to document rendering.
3. Run `git rm scripts/polish_payload_and_render.py` and add a CI/CD linter rule blocking ad-hoc payload mutation scripts in `scripts/`.