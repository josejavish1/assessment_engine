"""Universal Multi-Tenant Tower Payload Hydrator.

Hydrates raw tower blueprint payloads with authoritative tenant corporate telemetry,
ensuring 100% Declarative AST compilation compatibility across arbitrary technical domains.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import tempfile
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Final, List, Mapping, Optional

from assessment_engine.domain.actuarial import (
    ActuarialCalibrationEngine,
    IndustryArchetype,
)
from assessment_engine.domain.actuarial_calculator import calculate_severity_weighted_sle
from assessment_engine.domain.exceptions import PayloadIntegrityError
from assessment_engine.domain.actuarial_scale_calibrator import (
    resolve_iso_currency_code as _resolve_iso_currency_code,
)
from assessment_engine.domain.actuarial_scale_calibrator import (
    safe_float,
)
from assessment_engine.domain.taxonomy_resolver import (
    extract_pillar_identifiers,
    get_taxonomy_resolver,
)
from assessment_engine.infrastructure.localization import t

logger = logging.getLogger(__name__)

DEFAULT_ANNUAL_REVENUE: Final[float] = 100_000_000.0
HOURS_IN_YEAR: Final[float] = 8760.0
DEFAULT_REVENUE_EXPOSURE_FACTOR: Final[float] = 0.001
DEFAULT_BASELINE_RISK_FACTOR: Final[float] = 0.000801
DEFAULT_FACILITY_REVENUE_SHARE: Final[float] = 0.35
DEFAULT_RECOVERY_CEILING_HOURS: Final[float] = 24.0
DEFAULT_PERIMETER_WEIGHT_PCT: Final[float] = 100.0
DEFAULT_ENGAGEMENT_PERIOD: Final[str] = "000000"
DEFAULT_TENANT_PLACEHOLDER_UPPER: Final[str] = "ENTERPRISE"
DEFAULT_TENANT_PLACEHOLDER_TITLE: Final[str] = "Enterprise"
DEFAULT_CURRENCY_CODE: Final[str] = "EUR"
DEFAULT_CURRENCY_SYMBOL: Final[str] = "€"
DEFAULT_SECTOR_BENCHMARK_LABEL: Final[str] = "Industry Baseline"

CANONICAL_TOWER_ZONE_MAPPING: Final[dict[str, str]] = {
    "T1": "TIER_1_MISSION_CRITICAL",
    "T2": "TIER_1_MISSION_CRITICAL",
    "T3": "TIER_3_EDGE_DISTRIBUTION",
    "T4": "TIER_1_MISSION_CRITICAL",
    "T5": "TIER_2_CORE_OPERATIONS",
    "T6": "TIER_2_CORE_OPERATIONS",
    "T7": "TIER_2_CORE_OPERATIONS",
    "T8": "TIER_1_MISSION_CRITICAL",
    "T9": "TIER_3_EDGE_DISTRIBUTION",
    "T10": "TIER_3_EDGE_DISTRIBUTION",
}


def _round_currency_half_up(val: float | int | Decimal | str | None) -> float:
    """Deterministic half-up rounding to 2 decimal places with NaN/Infinity and type-safety guards."""
    if val is None or isinstance(val, bool):
        return 0.0
    try:
        if isinstance(val, Decimal):
            dec_val = val
        elif isinstance(val, (int, float)):
            dec_val = Decimal(str(val))
        else:
            cleaned = str(val).strip()
            if not cleaned:
                return 0.0
            dec_val = Decimal(cleaned)

        if not dec_val.is_finite():
            return 0.0
        return float(dec_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, OverflowError, TypeError):
        return 0.0


def _reconcile_finding_scores_half_up(
    findings: List[Dict[str, Any]],
    score_key: str,
    target_total: float,
    locale: str | None = None,
) -> None:
    """Proportionally scales finding scores using exact Decimal arithmetic and Largest Remainder reconciliation."""
    if not findings:
        return
    clean_target = safe_float(target_total, locale=locale, allow_zero=True) or 0.0
    try:
        target_dec = Decimal(str(clean_target))
        if not target_dec.is_finite() or target_dec < Decimal("0"):
            target_dec = Decimal("0")
    except (InvalidOperation, ValueError):
        target_dec = Decimal("0")

    target_cents = int(
        (target_dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    raw_weights: List[Decimal] = []
    for hc in findings:
        raw_val = safe_float(hc.get(score_key), locale=locale, allow_zero=True) or 0.0
        try:
            w_dec = Decimal(str(raw_val))
            if not w_dec.is_finite() or w_dec < Decimal("0"):
                w_dec = Decimal("0")
        except (InvalidOperation, ValueError):
            w_dec = Decimal("0")
        raw_weights.append(w_dec)

    total_weight = sum(raw_weights, Decimal("0"))
    n = len(findings)

    exact_quotas: List[Decimal] = []
    for w in raw_weights:
        if total_weight > Decimal("0"):
            exact_quotas.append((Decimal(target_cents) * w) / total_weight)
        else:
            exact_quotas.append(Decimal(target_cents) / Decimal(n))

    floored_cents = [int(q.to_integral_value(rounding="ROUND_FLOOR")) for q in exact_quotas]
    remainders = [(idx, exact_quotas[idx] - Decimal(floored_cents[idx])) for idx in range(n)]
    remainders.sort(key=lambda item: (-item[1], item[0]))

    shortfall_cents = target_cents - sum(floored_cents)
    for i in range(max(0, shortfall_cents)):
        winner_idx = remainders[i % n][0]
        floored_cents[winner_idx] += 1

    for idx, hc in enumerate(findings):
        hc[score_key] = float(
            (Decimal(floored_cents[idx]) / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )


_SAFE_TENANT_SLUG_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9_]+")
_FILENAME_TOKEN_SPLIT_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9]+")

CANONICAL_TOWER_NAMES: Final[Mapping[str, str]] = MappingProxyType({
    "T1": "Physical Data Center & Critical Facilities",
    "T2": "Hybrid Cloud, Compute & Virtualization",
    "T3": "Enterprise Networks & WAN Connectivity",
    "T4": "Storage Platforms & Corporate Backup",
    "T5": "Operational Continuity & Disaster Recovery",
    "T6": "Cybersecurity & Identity Governance",
    "T7": "Enterprise Databases & ITSM Operations",
    "T8": "Core Business Applications & ERP",
    "T9": "Digital Workplace & Unified Communications",
    "T10": "Mission-Critical Operations & Local Infrastructure",
})


def _sanitize_tenant_slug(client_name: str) -> str:
    """Produces a filesystem-safe lowercase tenant directory slug preventing path traversal."""
    raw = str(client_name or DEFAULT_TENANT_PLACEHOLDER_UPPER).strip().lower().replace(" ", "_")
    slug = _SAFE_TENANT_SLUG_PATTERN.sub("_", raw).strip("_")
    return slug or DEFAULT_TENANT_PLACEHOLDER_UPPER.lower()


def resolve_canonical_filename(
    tower_code: str,
    client_name: str = DEFAULT_TENANT_PLACEHOLDER_UPPER,
    period: str = DEFAULT_ENGAGEMENT_PERIOD,
) -> str:
    """Dynamically resolves canonical annex filename aligned with domain taxonomy."""
    code_upper = _FILENAME_TOKEN_SPLIT_PATTERN.sub("", tower_code.strip().upper()) or "T1"
    clean_words = [
        w if w.isupper() and len(w) > 1 else w.capitalize()
        for w in _FILENAME_TOKEN_SPLIT_PATTERN.split(client_name.strip())
        if w
    ]
    clean_client = "_".join(clean_words) or DEFAULT_TENANT_PLACEHOLDER_TITLE
    clean_period = _FILENAME_TOKEN_SPLIT_PATTERN.sub("", str(period).strip()) or DEFAULT_ENGAGEMENT_PERIOD
    return f"{clean_client}_{clean_period}_Annex_{code_upper}_ASIS.docx"


def _generate_canonical_kpi_finding(
    tower_id: str,
    pillar_id: str,
    doc_lang: str,
    repo_root: Path,
) -> Optional[Dict[str, Any]]:
    """Synthesizes a clean, domain-anchored health check finding from official KPI definitions."""
    from assessment_engine.application.services.actuarial_inference_engine import (
        ActuarialInferenceEngine,
    )
    try:
        t_id_u = tower_id.upper()
        def_path = repo_root / f"engine_config/towers/{t_id_u}/tower_definition_{t_id_u}.json"
        if not def_path.exists():
            def_path = repo_root / "engine_config/towers" / f"tower_definition_{t_id_u}.json"
        if def_path.exists():
            with open(def_path, "r", encoding="utf-8-sig") as f:
                t_def = json.load(f)
            for p in t_def.get("pillars", []):
                p_code = str(p.get("pillar_id", "")).upper()
                if p_code == pillar_id.upper() or p_code.endswith(f".{pillar_id.upper()}"):
                    cap_name = str(p.get("pillar_name", "")).strip()
                    kpis = p.get("kpis", [])
                    raw_k_name = str(kpis[-1].get("kpi_name", "")).strip() if kpis else cap_name
                    from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
                    resolver = get_taxonomy_resolver()
                    k_name = resolver.resolve_capability_name(raw_k_name, default=raw_k_name, locale=doc_lang)

                    # Use RFC 084 ActuarialInferenceEngine for mathematical calibration
                    act_engine = ActuarialInferenceEngine()
                    latent = act_engine.calculate_latent_risk(
                        tower_code=t_id_u,
                        pillar_id=pillar_id,
                        pillar_name=cap_name,
                    )

                    from assessment_engine.infrastructure.localization import t

                    severity = "HIGH" if latent.annual_loss_expectancy > 150000.0 else "MEDIUM"
                    finding_text = t(
                        "calib_fallback_neg_template",
                        locale=doc_lang,
                        kpi_name=k_name,
                    )
                    impact_text = t(
                        "calib_fallback_impact_template",
                        locale=doc_lang,
                        kpi_name=k_name,
                    )

                    return {
                        "node_id": f"{pillar_id}-CANONICAL-01",
                        "capability": cap_name,
                        "finding": finding_text,
                        "risk_observed": finding_text,
                        "impact_severity": severity,
                        "impact": severity,
                        "severity": severity,
                        "business_risk": impact_text,
                        "primary_impact": impact_text,
                        "threat_event_frequency": round(latent.loss_event_frequency * 10, 1),
                        "loss_magnitude": 3.0,
                        "fair_ale_score": latent.annual_loss_expectancy,
                        "fair_p90_score": latent.value_at_risk_90,
                        "fair_min_score": round(latent.annual_loss_expectancy * 0.25, 2),
                        "fair_max_score": round(latent.value_at_risk_90 * 1.5, 2),
                        "epistemic_state": "UNOBSERVED_BLINDSPOT",
                    }
    except Exception as exc:
        logger.warning("Could not synthesize canonical KPI finding for %s: %s", pillar_id, exc)
    return None


class TowerPayloadHydrator:
    """Hydrates raw tower blueprint payloads with authoritative corporate telemetry."""

    @staticmethod
    def _hydrate_epistemic_ledger_evidence(
        raw_payload: Dict[str, Any],
        code_upper: str,
        ledger_entries_by_tower: Dict[str, Dict[str, Any]],
    ) -> None:
        """Attaches reconciled epistemic evidence from immutable ledger (RFC 082)."""
        if code_upper not in ledger_entries_by_tower:
            return

        t_entry = ledger_entries_by_tower[code_upper]
        raw_payload["epistemic_ledger_entry"] = t_entry
        raw_payload["epistemic_truth_status"] = t_entry.get("truth_status")
        raw_payload["epistemic_composite_confidence"] = t_entry.get("composite_confidence")
        frags = t_entry.get("supporting_fragments", [])
        raw_payload["epistemic_supporting_fragments"] = frags

        pos_facts = [
            str(f.get("canonical_assertion", "")).strip()
            for f in frags
            if isinstance(f, dict) and f.get("polarity") == "POSITIVE" and f.get("canonical_assertion")
        ]
        neg_facts = [
            str(f.get("canonical_assertion", "")).strip()
            for f in frags
            if isinstance(f, dict) and f.get("polarity") == "NEGATIVE" and f.get("canonical_assertion")
        ]
        if pos_facts:
            raw_payload["epistemic_positive_assertions"] = pos_facts
        if neg_facts:
            raw_payload["epistemic_negative_assertions"] = neg_facts

        resolved_entities_list: List[Dict[str, Any]] = []
        for f in frags:
            if isinstance(f, dict):
                f_meta = f.get("metadata", {})
                if isinstance(f_meta, dict):
                    for ent in f_meta.get("resolved_entities", []):
                        if isinstance(ent, dict) and ent not in resolved_entities_list:
                            resolved_entities_list.append(ent)
        if resolved_entities_list:
            raw_payload["verified_entities"] = resolved_entities_list

    @staticmethod
    def _enforce_ontological_gatekeeping(
        raw_payload: Dict[str, Any],
        code_upper: str,
        active_gatekeeper: Any,
        doc_lang: str,
        resolved_repo_root: Path,
    ) -> None:
        """Enforces Ontological Semantic Gatekeeping on payload findings before disk persistence."""
        if not active_gatekeeper:
            return

        for pil in raw_payload.get("pillars_analysis", []):
            if not isinstance(pil, dict):
                continue
            p_id = str(pil.get("pillar_id") or "").strip().upper()

            # Refresh existing canonical findings with latest localized templates
            current_findings = pil.get("health_check_asis", [])
            if isinstance(current_findings, list):
                for f_idx, f_item in enumerate(current_findings):
                    if isinstance(f_item, dict) and str(f_item.get("node_id", "")).endswith("-CANONICAL-01"):
                        refreshed = _generate_canonical_kpi_finding(
                            tower_id=code_upper,
                            pillar_id=p_id,
                            doc_lang=doc_lang,
                            repo_root=resolved_repo_root,
                        )
                        if refreshed:
                            current_findings[f_idx] = refreshed

            raw_findings = current_findings
            if isinstance(raw_findings, list) and raw_findings and p_id:
                sanitized_findings, quarantined = active_gatekeeper.sanitize_pillar_findings(
                    pillar_id=p_id,
                    findings=raw_findings,
                    tower_id=code_upper,
                )
                if quarantined:
                    logger.info(
                        "[Payload Hydrator] Quarantined %d out-of-domain findings in %s -> %s",
                        len(quarantined),
                        code_upper,
                        p_id,
                    )
                    if not sanitized_findings:
                        nexus_findings = [
                            f
                            for f in raw_findings
                            if isinstance(f, dict)
                            and (
                                f.get("is_nexus")
                                or "NEXUS" in str(f.get("node_id", "")).upper()
                            )
                        ]
                        if nexus_findings:
                            logger.info(
                                "[Payload Hydrator] Preserving %d cross-cutting nexus findings in %s -> %s",
                                len(nexus_findings),
                                code_upper,
                                p_id,
                            )
                            sanitized_findings = nexus_findings
                        else:
                            logger.info(
                                "[Payload Hydrator] All findings quarantined in %s -> %s; generating canonical KPI finding fallback",
                                code_upper,
                                p_id,
                            )
                            canonical_fallback = _generate_canonical_kpi_finding(
                                tower_id=code_upper,
                                pillar_id=p_id,
                                doc_lang=doc_lang,
                                repo_root=resolved_repo_root,
                            )
                            sanitized_findings = [canonical_fallback] if canonical_fallback else []

                    pil["health_check_asis"] = sanitized_findings

            asis_desc = str(pil.get("asis_architecture_description") or "").strip()
            if asis_desc and p_id:
                state_val = active_gatekeeper.validate_text_for_pillar(
                    text=asis_desc,
                    target_pillar_id=p_id,
                    tower_id=code_upper,
                )
                if state_val.verdict.value == "QUARANTINED_FOREIGN_DOMAIN":
                    sentences = re.split(
                        r"(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)(?<=[.!?])\s+", asis_desc
                    )
                    clean_sentences = [
                        s.strip()
                        for s in sentences
                        if active_gatekeeper.validate_text_for_pillar(
                            text=s, target_pillar_id=p_id, tower_id=code_upper
                        ).verdict.value != "QUARANTINED_FOREIGN_DOMAIN"
                        and len(s.strip()) > 10
                    ]
                    if clean_sentences:
                        pil["asis_architecture_description"] = " ".join(clean_sentences)
                    else:
                        pil["asis_architecture_description"] = t(
                            "asis_architecture_description_fallback",
                            locale=doc_lang,
                            pillar_name=pil.get("pillar_name", p_id),
                        )

    @staticmethod
    def compute_canonical_score(payload: Dict[str, Any], doc_lang: str = "en") -> float:
        """Computes the canonical maturity score strictly from pillars_analysis (weighted sum)

        or falls back to exact_score / score when pillars are absent.
        """
        pa = payload.get("pillars_analysis") or []
        if pa:
            weighted_sum = Decimal("0.0")
            total_weight = Decimal("0.0")
            simple_scores = []

            for p_item in pa:
                if isinstance(p_item, dict):
                    raw_sc = (
                        p_item.get("score")
                        if p_item.get("score") is not None
                        else p_item.get("maturity_score")
                    )
                    sc_f = safe_float(raw_sc, locale=doc_lang, allow_zero=True)
                    raw_wt = p_item.get("weight") if p_item.get("weight") is not None else p_item.get("weight_pct")
                    wt_f = safe_float(raw_wt, locale=doc_lang, allow_zero=True)

                    if sc_f is not None:
                        sc_dec = Decimal(str(sc_f))
                        simple_scores.append(sc_dec)
                        if wt_f is not None and wt_f > 0.0:
                            wt_dec = Decimal(str(wt_f))
                            weighted_sum += sc_dec * wt_dec
                            total_weight += wt_dec

            if total_weight > Decimal("0.0"):
                if total_weight > Decimal("1.5"):  # Percentage weights (sum ~ 100)
                    normalized_score = (weighted_sum / total_weight).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                else:  # Normalized weights (sum ~ 1.0)
                    normalized_score = (weighted_sum / total_weight).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                return float(normalized_score)

            if simple_scores:
                simple_avg = (sum(simple_scores) / Decimal(str(len(simple_scores)))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                return float(simple_avg)

        raw_ext = payload.get("exact_score") or payload.get("score")
        parsed_ext = safe_float(raw_ext, locale=doc_lang, allow_zero=True)
        if parsed_ext is not None:
            return float(Decimal(str(parsed_ext)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        t_code = str(payload.get("tower_code") or payload.get("tower_id") or "UNKNOWN")
        raise PayloadIntegrityError(
            tower_id=t_code,
            control_id="GLOBAL_MATURITY",
            missing_attribute="score",
            context={"reason": "Payload lacks verifiable pillars_analysis and explicit maturity score."},
        )

    @staticmethod
    def load_and_hydrate_all_towers(
        repo_root: Path,
        global_payload: Dict[str, Any],
        doc_lang: str = "en",
        target_towers: Optional[List[str]] = None,
        persist_to_disk: bool = True,
        gatekeeper: Optional[Any] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Loads and hydrates all requested tower payloads."""
        if target_towers is None:
            target_towers = [f"T{i}" for i in range(1, 11)]

        meta = global_payload.get("meta", {})
        client_name = str(
            meta.get("client") or meta.get("client_name") or DEFAULT_TENANT_PLACEHOLDER_UPPER
        ).strip()
        client_id_norm = _sanitize_tenant_slug(client_name)
        fin_tel = global_payload.get("financial_telemetry") or meta.get("financial_telemetry", {})
        currency = str(
            meta.get("currency")
            or meta.get("currency_symbol")
            or fin_tel.get("currency")
            or DEFAULT_CURRENCY_SYMBOL
        ).strip()

        annual_revenue = (
            safe_float(fin_tel.get("annual_revenue"), locale=doc_lang)
            or safe_float(meta.get("annual_revenue"), locale=doc_lang)
            or DEFAULT_ANNUAL_REVENUE
        )
        hourly_rate = (
            safe_float(fin_tel.get("consolidated_hourly_downtime_rate"), locale=doc_lang)
            or safe_float(fin_tel.get("hourly_downtime_rate"), locale=doc_lang)
            or (annual_revenue / HOURS_IN_YEAR)
        )

        hydrated_map: Dict[str, Dict[str, Any]] = {}

        resolved_repo_root = repo_root.resolve()
        active_gatekeeper = gatekeeper
        if active_gatekeeper is None:
            ontology_file = resolved_repo_root / "engine_config/ontologies/global_tech_ontology.yaml"
            towers_dir = resolved_repo_root / "engine_config/towers"
            if ontology_file.exists() and towers_dir.exists():
                try:
                    from assessment_engine.infrastructure.ontology.taxonomy_loader import DomainTaxonomyRegistry
                    from assessment_engine.domain.validation.semantic_gatekeeper import OntologicalGatekeeper

                    registry = DomainTaxonomyRegistry.from_config_directories(ontology_file, towers_dir)
                    active_gatekeeper = OntologicalGatekeeper(registry)
                except Exception as exc:
                    logger.warning("Could not initialize OntologicalGatekeeper in hydrator: %s", exc)
        extra_roots = global_payload.get("search_roots") or []
        safe_extra_roots: List[Path] = []
        for r in extra_roots:
            if isinstance(r, (str, Path)):
                candidate_path = Path(r).resolve()
                if candidate_path == resolved_repo_root or resolved_repo_root in candidate_path.parents:
                    safe_extra_roots.append(candidate_path)
                else:
                    logger.warning(
                        "Rejected out-of-bounds search_root '%s' outside repo_root '%s'",
                        candidate_path,
                        resolved_repo_root,
                    )

        candidate_roots = [resolved_repo_root / "working" / client_id_norm] + safe_extra_roots

        # RFC 082: Load immutable multi-source epistemic ledger if present in candidate roots
        epistemic_ledger_data: Optional[Dict[str, Any]] = None
        for base_dir in candidate_roots:
            ledger_candidate = base_dir / "epistemic_ledger.json"
            if ledger_candidate.exists():
                try:
                    with open(ledger_candidate, "r", encoding="utf-8-sig") as lf:
                        loaded_ledger = json.load(lf)
                    if isinstance(loaded_ledger, dict):
                        epistemic_ledger_data = loaded_ledger
                        logger.info("Loaded epistemic ledger from: %s", ledger_candidate)
                        break
                except (OSError, ValueError, TypeError) as e:
                    logger.warning("Could not parse epistemic ledger from %s: %s", ledger_candidate, e)

        ledger_entries_by_tower: Dict[str, Dict[str, Any]] = {}
        if epistemic_ledger_data and isinstance(epistemic_ledger_data, dict):
            for entry in epistemic_ledger_data.get("epistemic_entries", []):
                if isinstance(entry, dict):
                    t_ref = str(entry.get("domain_taxonomy_ref", "")).strip().upper()
                    if t_ref:
                        ledger_entries_by_tower[t_ref] = entry

        taxonomy_resolver = get_taxonomy_resolver()

        for tower_code in target_towers:
            code_upper = _FILENAME_TOKEN_SPLIT_PATTERN.sub("_", tower_code.strip().upper()).strip("_")
            if not code_upper:
                continue
            code_lower = code_upper.lower()
            raw_payload: Optional[Dict[str, Any]] = None

            for base_dir in candidate_roots:
                if not base_dir.exists():
                    continue

                tower_dir = base_dir / code_upper
                if not tower_dir.exists():
                    tower_dir = base_dir / code_lower
                if not tower_dir.exists():
                    continue

                candidate_files = [
                    tower_dir / f"blueprint_{code_lower}_payload.json",
                    tower_dir / f"approved_annex_{code_lower}.template_payload.json",
                    tower_dir / f"approved_annex_{code_lower}.enriched_payload.json",
                ]

                for p_file in candidate_files:
                    if p_file.exists():
                        try:
                            with open(p_file, "r", encoding="utf-8-sig") as f:
                                loaded = json.load(f)
                            if isinstance(loaded, dict):
                                raw_payload = dict(loaded)
                                break
                        except (OSError, ValueError, TypeError) as e:
                            logger.warning("Error reading %s: %s", p_file, e)

                if raw_payload is not None:
                    scoring_file = tower_dir / "scoring_output.json"
                    if scoring_file.exists():
                        try:
                            with open(scoring_file, "r", encoding="utf-8-sig") as sf:
                                score_data = json.load(sf)
                                disk_score = score_data.get("tower_score_exact")
                                if disk_score is not None:
                                    raw_payload["exact_score"] = float(disk_score)
                        except Exception as ex:
                            logger.debug("Could not read scoring_output in %s: %s", tower_dir, ex)
                    break

            if raw_payload is None:
                logger.warning(
                    "Could not find raw payload for tower %s; generating fallback structure",
                    code_upper,
                )
                raw_payload = {
                    "tower_code": code_upper,
                    "tower_name": CANONICAL_TOWER_NAMES.get(code_upper, f"Domain {code_upper}"),
                }

            # 1. Collect findings for portfolio evaluation later
            pillars = raw_payload.get("pillars_analysis") or []
            for pil in pillars:
                if isinstance(pil, dict):
                    p_id, p_name = extract_pillar_identifiers(pil)
                    if p_id and "pillar_id" not in pil:
                        pil["pillar_id"] = p_id
                    if p_name and "pillar_name" not in pil:
                        pil["pillar_name"] = p_name

            # RFC 075: Compute canonical maturity score strictly from compute_canonical_score SSOT
            canonical_score_float = TowerPayloadHydrator.compute_canonical_score(
                raw_payload, doc_lang=doc_lang
            )
            canonical_score_str = f"{canonical_score_float:.2f}"

            raw_payload["score"] = canonical_score_float
            raw_payload["exact_score"] = canonical_score_float
            raw_payload["maturity_score"] = canonical_score_float
            raw_payload["overall_score"] = canonical_score_float

            exec_summary = raw_payload.get("executive_summary")
            if not isinstance(exec_summary, dict):
                exec_summary = {}
                raw_payload["executive_summary"] = exec_summary
            exec_summary["global_score"] = canonical_score_str
            exec_summary["global_score_numeric"] = canonical_score_float

            tower_fin_tel = raw_payload.get("financial_telemetry") or {}
            explicit_tower_rate = (
                safe_float(raw_payload.get("hourly_downtime_rate"), locale=doc_lang)
                or safe_float(raw_payload.get("hourly_burn_rate"), locale=doc_lang)
                or safe_float(tower_fin_tel.get("authoritative_hourly_downtime_cost"), locale=doc_lang)
            )
            local_facility_domains = {
                str(d).strip().upper()
                for d in (fin_tel.get("local_facility_domains") or ())
                if str(d).strip()
            }
            is_local_facility_domain = (
                bool(raw_payload.get("is_local_facility"))
                or code_upper in local_facility_domains
            )
            if is_local_facility_domain:
                facility_share = (
                    safe_float(tower_fin_tel.get("primary_facility_revenue_share"), locale=doc_lang)
                    or safe_float(fin_tel.get("primary_facility_revenue_share"), locale=doc_lang)
                    or DEFAULT_FACILITY_REVENUE_SHARE
                )
                local_facility_rate = (
                    safe_float(fin_tel.get("local_facility_hourly_rate"), locale=doc_lang)
                    or explicit_tower_rate
                    or _round_currency_half_up(hourly_rate * facility_share)
                )
                effective_tower_hourly_rate = local_facility_rate
            else:
                effective_tower_hourly_rate = (
                    explicit_tower_rate
                    or safe_float(fin_tel.get("consolidated_hourly_downtime_rate"), locale=doc_lang)
                    or safe_float(fin_tel.get("hourly_downtime_rate"), locale=doc_lang)
                    or hourly_rate
                )

            resolved_currency_code = str(
                meta.get("currency_code")
                or fin_tel.get("currency_code")
                or _resolve_iso_currency_code(currency, locale=doc_lang)
            ).strip()

            raw_payload["annual_revenue"] = annual_revenue
            raw_payload["hourly_downtime_rate"] = effective_tower_hourly_rate
            raw_payload["hourly_burn_rate"] = effective_tower_hourly_rate
            raw_payload["explicit_hourly_downtime_cost"] = effective_tower_hourly_rate
            raw_payload["currency"] = currency
            raw_payload["currency_code"] = resolved_currency_code

            raw_payload["financial_telemetry"] = {
                "consolidated_annual_revenue": annual_revenue,
                "annual_revenue": annual_revenue,
                "global_annual_revenue": annual_revenue,
                "perimeter_revenue_weight_pct": (
                    safe_float(tower_fin_tel.get("perimeter_revenue_weight_pct"), locale=doc_lang)
                    or DEFAULT_PERIMETER_WEIGHT_PCT
                ),
                "effective_exposed_revenue": (
                    safe_float(tower_fin_tel.get("effective_exposed_revenue"), locale=doc_lang)
                    or annual_revenue
                ),
                "sector_benchmark_source": str(
                    tower_fin_tel.get("sector_benchmark_source") or DEFAULT_SECTOR_BENCHMARK_LABEL
                ),
                "hourly_revenue_exposure_factor": (
                    safe_float(tower_fin_tel.get("hourly_revenue_exposure_factor"), locale=doc_lang)
                    or DEFAULT_REVENUE_EXPOSURE_FACTOR
                ),
                "authoritative_hourly_downtime_cost": effective_tower_hourly_rate,
                "explicit_hourly_downtime_cost": effective_tower_hourly_rate,
                "operational_recovery_ceiling_hours": (
                    safe_float(tower_fin_tel.get("operational_recovery_ceiling_hours"), locale=doc_lang)
                    or DEFAULT_RECOVERY_CEILING_HOURS
                ),
                "currency": currency,
                "currency_code": resolved_currency_code,
            }

            doc_meta = dict(raw_payload.get("document_meta") or {})
            existing_tower_name = str(
                raw_payload.get("tower_name") or doc_meta.get("tower_name") or ""
            ).strip()
            resolved_tower_name = (
                existing_tower_name
                or taxonomy_resolver.resolve_tower_name(
                    code_upper,
                    locale=doc_lang,
                    default=CANONICAL_TOWER_NAMES.get(code_upper, f"Domain {code_upper}"),
                )
            )

            raw_payload["tower_name"] = resolved_tower_name
            doc_meta["client_name"] = client_name
            doc_meta["currency"] = currency
            doc_meta["doc_lang"] = doc_lang
            doc_meta["annual_revenue"] = annual_revenue
            doc_meta["tower_code"] = code_upper
            doc_meta["tower_name"] = resolved_tower_name
            raw_payload["document_meta"] = doc_meta

            # RFC 082: Attach reconciled epistemic evidence from immutable ledger
            TowerPayloadHydrator._hydrate_epistemic_ledger_evidence(
                raw_payload, code_upper, ledger_entries_by_tower
            )

            # Phase 5: Enforce Ontological Semantic Gatekeeping on Payload Findings before disk persistence
            TowerPayloadHydrator._enforce_ontological_gatekeeping(
                raw_payload, code_upper, active_gatekeeper, doc_lang, resolved_repo_root
            )

            if persist_to_disk:
                local_tower_dir = resolved_repo_root / "working" / client_id_norm / code_upper
                local_tower_dir.mkdir(parents=True, exist_ok=True)
                local_payload_path = local_tower_dir / f"blueprint_{code_lower}_payload.json"

                fd, tmp_path_str = tempfile.mkstemp(
                    dir=str(local_tower_dir),
                    prefix=f".tmp_{code_lower}_",
                    suffix=".json",
                )
                fd_closed = False
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                        fd_closed = True
                        json.dump(raw_payload, tmp_f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path_str, local_payload_path)
                except Exception:
                    if not fd_closed:
                        try:
                            os.close(fd)
                        except OSError:
                            _ = True  # Handled fallback
                    if os.path.exists(tmp_path_str):
                        try:
                            os.unlink(tmp_path_str)
                        except OSError:
                            _ = True  # Handled fallback
                    raise

            hydrated_map[code_upper] = raw_payload
            logger.info("Successfully hydrated payload for tower %s", code_upper)

        # Dynamic Finding-Driven Actuarial Allocation (RFC 084 + RFC 056)
        domain_weights = fin_tel.get("domain_weights") or {}
        has_explicit_weights = bool(
            domain_weights and any(code in domain_weights for code in hydrated_map)
        )

        actuarial_cfg = global_payload.get("actuarial_configuration") or {}
        tower_zone_map = actuarial_cfg.get("tower_zone_map") or CANONICAL_TOWER_ZONE_MAPPING

        annual_rev = (
            safe_float(fin_tel.get("annual_revenue"), locale=doc_lang)
            or safe_float(meta.get("annual_revenue"), locale=doc_lang)
            or 0.0
        )
        base_downtime_rate = (
            safe_float(fin_tel.get("consolidated_hourly_downtime_rate"), locale=doc_lang)
            or (annual_rev / 8760.0 if annual_rev > 0 else 1000.0)
            or 1000.0
        )
        plant_downtime_rate = (
            safe_float(fin_tel.get("local_facility_hourly_rate"), locale=doc_lang)
            or (base_downtime_rate * DEFAULT_FACILITY_REVENUE_SHARE)
        )
        from assessment_engine.domain.actuarial_reconciler import ActuarialReconciler

        def _derive_cmmi_rto(cmmi_val: float, sev_val: str, spof_val: bool) -> float:
            """Continuous convex mapping from CMMI maturity [1.0, 5.0] to recovery hours.

            CMMI 5.0 -> 1.0h (automated HA continuous operations); CMMI 1.0 -> 18.0h (unmitigated manual rebuild).
            Zero hardcoded tower IDs, zero language-specific keywords, universally scale-invariant.
            """
            clamped_m = max(1.0, min(5.0, cmmi_val))
            ratio = (5.0 - clamped_m) / 4.0
            base_rto = 1.0 + 17.0 * (ratio ** 1.35)
            if spof_val or sev_val == "CRITICAL":
                return min(22.0, round(base_rto * 1.20, 1))
            elif sev_val == "HIGH":
                return max(1.0, round(base_rto * 0.70, 1))
            elif sev_val == "MEDIUM":
                return max(0.5, round(base_rto * 0.40, 1))
            else:
                return max(0.25, round(base_rto * 0.20, 1))

        tef_mapping: Final[Dict[int, float]] = {1: 0.05, 2: 0.12, 3: 0.25, 4: 0.40, 5: 0.65}

        if has_explicit_weights:
            reconciled_allocations = {
                code_u: int(round(safe_float(domain_weights.get(code_u), locale=doc_lang, allow_zero=True) or 0.0))
                for code_u in hydrated_map
            }
        else:
            raw_scores: List[tuple[str, Decimal]] = []
            for code_u, payload in hydrated_map.items():
                is_facility_edge = (
                    tower_zone_map.get(code_u) in ("ZONE_LOGISTICS_EDGE", "TIER_3_EDGE_DISTRIBUTION")
                    or any(k in code_u.lower() for k in ("edge", "facility", "plant", "site"))
                )
                effective_rate = plant_downtime_rate if is_facility_edge else base_downtime_rate
                cmmi = (
                    float(payload["score"])
                    if "score" in payload and payload["score"] is not None
                    else TowerPayloadHydrator.compute_canonical_score(payload, doc_lang=doc_lang)
                )
                vuln = max(0.12, min(0.95, (5.0 - cmmi) / 4.0))

                t_score = 0.0
                tower_sles: List[float] = []
                for pil in payload.get("pillars_analysis", []):
                    if not isinstance(pil, dict):
                        continue
                    for hc in pil.get("health_check_asis", []):
                        if not isinstance(hc, dict):
                            continue
                        raw_sev = str(hc.get("severity") or hc.get("impact_severity") or "").upper()
                        raw_lm = safe_float(hc.get("loss_magnitude"), locale=doc_lang) or 3.0
                        raw_tef = safe_float(hc.get("threat_event_frequency"), locale=doc_lang) or 3.0

                        if raw_sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                            sev = raw_sev
                        elif raw_lm >= 4.0:
                            sev = "CRITICAL"
                        elif raw_lm >= 3.0:
                            sev = "HIGH"
                        else:
                            sev = "MEDIUM"

                        is_spof = bool(hc.get("is_spof")) or (sev == "CRITICAL" and raw_lm >= 4.0)

                        tef = tef_mapping.get(int(raw_tef), 0.25)

                        explicit_rto = safe_float(hc.get("recovery_time_hours"), locale=doc_lang)
                        if explicit_rto is None:
                            explicit_rto = safe_float(hc.get("rto_hours_mode"), locale=doc_lang)

                        f_rto = (
                            float(explicit_rto)
                            if explicit_rto is not None
                            else _derive_cmmi_rto(cmmi, sev, is_spof)
                        )

                        sle, f_alpha, f_repl, f_sec = calculate_severity_weighted_sle(
                            rto_hours=f_rto,
                            effective_rate=effective_rate,
                            severity=sev,
                            is_spof=is_spof,
                        )
                        ale = tef * vuln * sle
                        t_score += ale
                        tower_sles.append(sle)

                tower_sle_max = max(tower_sles) if tower_sles else (effective_rate * 5.0)
                if tower_sle_max > 0.0 and t_score > 0.0:
                    # Open FAIR Shared-Fate Saturation Barrier (Poisson-Weibull Coupling)
                    # Guarantees strictly: 0 < ale_eff < tower_sle_max
                    hazard_ratio = float(t_score) / float(tower_sle_max)
                    ale_eff = float(tower_sle_max) * (1.0 - math.exp(-hazard_ratio))
                else:
                    ale_eff = float(effective_rate * 0.5)

                raw_scores.append((code_u, Decimal(str(round(ale_eff, 2)))))

            raw_corp_ale = safe_float(fin_tel.get("total_fair_ale"), locale=doc_lang, allow_zero=True)
            if raw_corp_ale is not None:
                corporate_pool = int(round(raw_corp_ale))
            else:
                # Derived organically from bottom-up empirical finding risks across all towers (ZERO hardcoding)
                corporate_pool = int(round(sum(float(s[1]) for s in raw_scores))) if raw_scores else int(round((annual_rev * base_risk_factor) or 100000.0))

            reconciled_allocations = ActuarialReconciler.reconcile_domain_allocations(
                target_corporate_ale=corporate_pool,
                domain_raw_exposures=raw_scores,
            )

        for code_u, payload in hydrated_map.items():
            target_domain_ale = reconciled_allocations.get(code_u, 0)

            is_facility_dom = (
                tower_zone_map.get(code_u) in ("ZONE_LOGISTICS_EDGE", "TIER_3_EDGE_DISTRIBUTION")
                or any(k in code_u.lower() for k in ("edge", "facility", "plant", "site"))
            )
            effective_dom_rate = plant_downtime_rate if is_facility_dom else base_downtime_rate
            cmmi_u = (
                float(payload["score"])
                if "score" in payload and payload["score"] is not None
                else TowerPayloadHydrator.compute_canonical_score(payload, doc_lang=doc_lang)
            )

            finding_sles: List[float] = []
            finding_rtos: List[float] = []

            for pillar in payload.get("pillars_analysis", []):
                if isinstance(pillar, dict):
                    for hc in pillar.get("health_check_asis", []):
                        if isinstance(hc, dict):
                            raw_sev = str(hc.get("severity") or hc.get("impact_severity") or "").upper()
                            raw_lm = safe_float(hc.get("loss_magnitude"), locale=doc_lang) or 3.0

                            if raw_sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                                s_val = raw_sev
                            elif raw_lm >= 4.0:
                                s_val = "CRITICAL"
                            elif raw_lm >= 3.0:
                                s_val = "HIGH"
                            else:
                                s_val = "MEDIUM"

                            spof_val = bool(hc.get("is_spof")) or (s_val == "CRITICAL" and raw_lm >= 4.0)

                            r_val = safe_float(hc.get("recovery_time_hours"), locale=doc_lang)
                            if r_val is None:
                                r_val = safe_float(hc.get("rto_hours_mode"), locale=doc_lang)

                            h_rto = float(r_val) if r_val is not None else _derive_cmmi_rto(cmmi_u, s_val, spof_val)
                            finding_rtos.append(h_rto)

                            h_sle, h_alpha, h_repl, h_sec = calculate_severity_weighted_sle(
                                rto_hours=h_rto,
                                effective_rate=effective_dom_rate,
                                severity=s_val,
                                is_spof=spof_val,
                            )
                            finding_sles.append(h_sle)

            dom_max_rto = round(max(finding_rtos), 1) if finding_rtos else _derive_cmmi_rto(cmmi_u, "HIGH", False)
            target_domain_p90 = _round_currency_half_up(max(finding_sles)) if finding_sles else _round_currency_half_up(target_domain_ale * 1.5)
            target_domain_max = _round_currency_half_up(target_domain_p90 * 1.25)

            payload["worst_crisis_event"] = target_domain_p90
            payload["worst_crisis_rto_hours"] = dom_max_rto
            payload["total_fair_ale"] = target_domain_ale
            payload["total_fair_p90"] = target_domain_p90
            payload["total_fair_max"] = target_domain_max

            pillars = payload.get("pillars_analysis") or []
            all_findings = [
                hc
                for pillar in pillars
                if isinstance(pillar, dict)
                for hc in pillar.get("health_check_asis", [])
                if isinstance(hc, dict)
            ]
            if all_findings:
                # Severity-weighted proportional allocation to preserve corporate actuarial pool and enforce monotonicity
                severity_allocation_weights = {
                    "CRITICAL": Decimal("10.0"),
                    "HIGH": Decimal("4.5"),
                    "MEDIUM": Decimal("1.8"),
                    "LOW": Decimal("0.8"),
                }
                for hc in all_findings:
                    raw_sev = str(hc.get("severity") or hc.get("impact_severity") or "").upper()
                    if not raw_sev or raw_sev not in severity_allocation_weights:
                        # Dynamic fallback: map CMMI score to inverse risk severity
                        cmmi_val = safe_float(hc.get("score") or hc.get("maturity_score"), locale=doc_lang)
                        if cmmi_val is not None:
                            if cmmi_val <= 1.59:
                                sev = "CRITICAL"
                            elif cmmi_val <= 2.59:
                                sev = "HIGH"
                            elif cmmi_val <= 3.59:
                                sev = "MEDIUM"
                            else:
                                sev = "LOW"
                        else:
                            sev = "MEDIUM"
                        hc["severity"] = sev
                        hc["impact_severity"] = sev
                    else:
                        sev = raw_sev
                        hc["severity"] = sev
                    hc["fair_ale_score"] = float(severity_allocation_weights.get(sev, Decimal("1.8")))

                _reconcile_finding_scores_half_up(
                    all_findings, "fair_ale_score", target_domain_ale, locale=doc_lang
                )

                # Dynamically derive P90, min, and max using industry-tailored Monte Carlo skewness
                from assessment_engine.domain.actuarial.actuarial_calibration_engine import (
                    ActuarialCalibrationEngine,
                )

                dynamic_p90_ratio = ActuarialCalibrationEngine.calculate_dynamic_p90_ratio(
                    maturity_score=cmmi_u,
                    industry=fin_tel.get("industry_vertical") or meta.get("industry_vertical") or "manufacturing",
                )

                for hc in all_findings:
                    ale_val = float(hc.get("fair_ale_score") or 0.0)
                    p90_val = _round_currency_half_up(ale_val * dynamic_p90_ratio)
                    hc["fair_p90_score"] = p90_val
                    hc["fair_min_score"] = _round_currency_half_up(ale_val * 0.25)
                    hc["fair_max_score"] = _round_currency_half_up(p90_val * 1.40)

                payload["total_fair_ale"] = _round_currency_half_up(sum(hc["fair_ale_score"] for hc in all_findings))
                payload["total_fair_p90"] = _round_currency_half_up(sum(hc["fair_p90_score"] for hc in all_findings))
                payload["total_fair_max"] = _round_currency_half_up(max(hc["fair_max_score"] for hc in all_findings))
                payload["worst_crisis_event"] = payload["total_fair_p90"]


        # RFC 084: Run Bayesian FAIR Copula Engine across all collected payloads
        from assessment_engine.domain.bayesian_fair_copula_engine import (
            BayesianFairCopulaEngine,
            FindingTelemetry,
            OperationalZone,
        )

        actuarial_cfg = fin_tel.get("actuarial_calibration") or {}
        num_sims = int(actuarial_cfg.get("simulation_iterations") or 8192)
        copula_df = int(actuarial_cfg.get("copula_df") or 4)
        engine = BayesianFairCopulaEngine(num_simulations=num_sims, copula_df=copula_df)

        # Resolve baseline hourly revenue burn rate dynamically from tenant telemetry
        tenant_revenue = (
            safe_float(fin_tel.get("annual_revenue"), locale=doc_lang)
            or safe_float(meta.get("annual_revenue"), locale=doc_lang)
            or 0.0
        )
        annual_op_hours = (
            safe_float(fin_tel.get("operating_hours_per_year"), locale=doc_lang)
            or safe_float(fin_tel.get("annual_operating_hours"), locale=doc_lang)
            or 8760.0
        )
        derived_hourly_rate = (
            hourly_rate
            if (hourly_rate is not None and hourly_rate > 0.0)
            else (tenant_revenue / max(1.0, annual_op_hours))
        )
        if derived_hourly_rate <= 0.0:
            derived_hourly_rate = 1000.0  # Resilient absolute baseline floor

        # Dynamic, Vertical-Agnostic Operational Tiers scaled to tenant baseline hourly rate
        configured_zones = actuarial_cfg.get("operational_zones") or {}
        zones: Dict[str, OperationalZone] = {}
        if configured_zones:
            for z_id, z_data in configured_zones.items():
                if isinstance(z_data, dict):
                    rate_multiplier = float(z_data.get("burn_rate_multiplier", 1.0))
                    explicit_burn_rate = safe_float(z_data.get("hourly_burn_rate"), locale=doc_lang)
                    effective_rate = (
                        explicit_burn_rate
                        if (explicit_burn_rate is not None and explicit_burn_rate >= 0.0)
                        else (derived_hourly_rate * rate_multiplier)
                    )
                    max_outage = float(
                        z_data.get("max_annual_outage_hours", annual_op_hours * 0.04)
                    )
                    zones[z_id] = OperationalZone(
                        zone_id=z_id,
                        hourly_burn_rate=effective_rate,
                        max_annual_outage_hours=max(1.0, max_outage),
                        secondary_loss_retention_factor=float(
                            z_data.get("secondary_loss_retention_factor", 0.85)
                        ),
                    )

        if not zones:
            zones = {
                "TIER_1_MISSION_CRITICAL": OperationalZone(
                    zone_id="TIER_1_MISSION_CRITICAL",
                    hourly_burn_rate=round(derived_hourly_rate * 1.00, 2),
                    max_annual_outage_hours=round(annual_op_hours * 0.041, 1),
                ),
                "TIER_2_CORE_OPERATIONS": OperationalZone(
                    zone_id="TIER_2_CORE_OPERATIONS",
                    hourly_burn_rate=round(derived_hourly_rate * 0.65, 2),
                    max_annual_outage_hours=round(annual_op_hours * 0.055, 1),
                ),
                "TIER_3_EDGE_DISTRIBUTION": OperationalZone(
                    zone_id="TIER_3_EDGE_DISTRIBUTION",
                    hourly_burn_rate=round(derived_hourly_rate * 0.38, 2),
                    max_annual_outage_hours=round(annual_op_hours * 0.068, 1),
                ),
                "TIER_4_ENTERPRISE_SUPPORT": OperationalZone(
                    zone_id="TIER_4_ENTERPRISE_SUPPORT",
                    hourly_burn_rate=round(derived_hourly_rate * 0.10, 2),
                    max_annual_outage_hours=round(annual_op_hours * 0.082, 1),
                ),
            }

        tower_zone_map = actuarial_cfg.get("tower_zone_mapping") or CANONICAL_TOWER_ZONE_MAPPING

        default_zone = zones.get("TIER_4_ENTERPRISE_SUPPORT") or next(iter(zones.values()))

        # Secondary loss priors scaled proportionally to tenant hourly burn rate
        priors = actuarial_cfg.get("severity_priors") or {
            "CRITICAL": {
                "tef_min": 0.15,
                "tef_mode": 0.35,
                "tef_max": 0.85,
                "rto_min": 5.0,
                "rto_mode": 8.5,
                "rto_max": 18.0,
                "sec_burn_hours_equiv": 3.5,
                "is_spof": True,
                "systemic_rho": 0.70,
            },
            "HIGH": {
                "tef_min": 0.08,
                "tef_mode": 0.22,
                "tef_max": 0.50,
                "rto_min": 3.0,
                "rto_mode": 5.5,
                "rto_max": 12.0,
                "sec_burn_hours_equiv": 1.8,
                "is_spof": False,
                "systemic_rho": 0.50,
            },
            "MEDIUM": {
                "tef_min": 0.04,
                "tef_mode": 0.12,
                "tef_max": 0.30,
                "rto_min": 1.0,
                "rto_mode": 2.5,
                "rto_max": 6.0,
                "sec_burn_hours_equiv": 0.8,
                "is_spof": False,
                "systemic_rho": 0.30,
            },
            "LOW": {
                "tef_min": 0.02,
                "tef_mode": 0.05,
                "tef_max": 0.15,
                "rto_min": 0.5,
                "rto_mode": 1.0,
                "rto_max": 3.0,
                "sec_burn_hours_equiv": 0.4,
                "is_spof": False,
                "systemic_rho": 0.15,
            },
        }

        tef_scale = actuarial_cfg.get("tef_qualitative_scale") or {
            1: 0.05, 2: 0.12, 3: 0.22, 4: 0.35, 5: 0.55
        }
        rto_scale = actuarial_cfg.get("rto_qualitative_scale") or {
            1: 1.0, 2: 2.0, 3: 4.0, 4: 7.0, 5: 11.0
        }
        sec_hours_scale = actuarial_cfg.get("secondary_hours_equiv_scale") or {
            1: 0.5, 2: 1.0, 3: 1.5, 4: 2.5, 5: 3.5
        }

        all_telemetry: List[FindingTelemetry] = []
        for code, payload in hydrated_map.items():
            pillars = payload.get("pillars_analysis") or []
            z_id = tower_zone_map.get(code, "TIER_4_ENTERPRISE_SUPPORT")
            zone = zones.get(z_id, default_zone)
            finding_seq = 0

            for pillar in pillars:
                if not isinstance(pillar, dict):
                    continue
                raw_cmmi = safe_float(
                    pillar.get("score") if pillar.get("score") is not None else payload.get("score"),
                    locale=doc_lang,
                    allow_zero=True,
                )
                cmmi = float(raw_cmmi if raw_cmmi is not None and raw_cmmi > 0.0 else payload["score"])

                for hc in pillar.get("health_check_asis", []):
                    if not isinstance(hc, dict):
                        continue

                    finding_seq += 1
                    finding_id = str(hc.get("node_id") or f"{code}_F{finding_seq:03d}")
                    hc["node_id"] = finding_id
                    title = str(hc.get("capability") or f"Architectural Finding {finding_id}")

                    raw_sev = str(hc.get("severity") or hc.get("impact_severity") or "").upper()
                    raw_lm = safe_float(hc.get("loss_magnitude"), locale=doc_lang)
                    raw_tef_rating = safe_float(hc.get("threat_event_frequency"), locale=doc_lang)

                    if raw_sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                        sev = raw_sev
                    elif raw_lm is not None and raw_lm >= 4.0:
                        sev = "CRITICAL"
                    elif raw_lm is not None and raw_lm >= 3.0:
                        sev = "HIGH"
                    elif raw_lm is not None and raw_lm >= 2.0:
                        sev = "MEDIUM"
                    else:
                        sev = "LOW"

                    prior = priors.get(sev, priors["MEDIUM"])
                    default_sec_mean = float(
                        prior.get(
                            "sec_mean",
                            derived_hourly_rate * float(prior.get("sec_burn_hours_equiv", 0.50)),
                        )
                    )

                    if (
                        raw_tef_rating is not None
                        and 1.0 <= raw_tef_rating <= 5.0
                        and raw_tef_rating == int(raw_tef_rating)
                    ):
                        tef_mode_val = float(tef_scale.get(int(raw_tef_rating), prior["tef_mode"]))
                    else:
                        explicit_tef_mode = safe_float(hc.get("tef_pert_mode"), locale=doc_lang)
                        if explicit_tef_mode is not None:
                            tef_mode_val = float(explicit_tef_mode)
                        elif raw_tef_rating is not None and 0.0 < raw_tef_rating < 1.0:
                            tef_mode_val = float(raw_tef_rating)
                        else:
                            tef_mode_val = float(prior["tef_mode"])

                    if (
                        raw_lm is not None
                        and 1.0 <= raw_lm <= 5.0
                        and raw_lm == int(raw_lm)
                    ):
                        rating_key = int(raw_lm)
                        rto_mode_val = float(rto_scale.get(rating_key, prior["rto_mode"]))
                        sec_mean_val = float(
                            derived_hourly_rate * sec_hours_scale.get(rating_key, 1.0)
                        )
                    else:
                        explicit_rto = safe_float(hc.get("recovery_time_hours"), locale=doc_lang)
                        if explicit_rto is None:
                            explicit_rto = safe_float(hc.get("rto_hours_mode"), locale=doc_lang)
                        rto_mode_val = (
                            float(explicit_rto)
                            if explicit_rto is not None
                            else float(prior["rto_mode"])
                        )

                        explicit_sec = safe_float(hc.get("secondary_loss_mean"), locale=doc_lang)
                        sec_mean_val = (
                            float(explicit_sec)
                            if explicit_sec is not None
                            else default_sec_mean
                        )

                    spof_flag = (
                        bool(hc.get("is_spof"))
                        or bool(prior.get("is_spof", False))
                        or (sev == "CRITICAL" and raw_lm is not None and raw_lm >= 4.0)
                    )
                    if spof_flag:
                        tef_mode_val = max(tef_mode_val, 0.30)
                        rto_mode_val = max(rto_mode_val, 4.50)
                        sec_mean_val = max(sec_mean_val, derived_hourly_rate * 2.65)

                    explicit_rho = safe_float(hc.get("shared_dependence_factor"), locale=doc_lang)
                    rho_val = (
                        float(explicit_rho)
                        if explicit_rho is not None
                        else (0.65 if spof_flag else float(prior.get("systemic_rho", 0.45)))
                    )

                    explicit_tef_min = safe_float(hc.get("tef_pert_min"), locale=doc_lang, allow_zero=True)
                    explicit_tef_max = safe_float(hc.get("tef_pert_max"), locale=doc_lang)
                    explicit_rto_min = safe_float(hc.get("rto_hours_min"), locale=doc_lang, allow_zero=True)
                    explicit_rto_max = safe_float(hc.get("rto_hours_max"), locale=doc_lang)

                    is_core_zone = z_id in ("TIER_1_MISSION_CRITICAL", "TIER_2_CORE_OPERATIONS")
                    alpha_val = (
                        0.85
                        if (spof_flag and is_core_zone)
                        else (0.70 if spof_flag or sev == "CRITICAL" else (0.40 if sev == "HIGH" else 0.20))
                    )
                    cat_rto = 24.0 if spof_flag else 16.0
                    repl_cost = (derived_hourly_rate * 2.5) if spof_flag else 0.0

                    # Wire Epistemic Dissonance if present
                    dissonance_obj = None
                    if hc.get("dissonance_flag") or hc.get("has_dissonance"):
                        from assessment_engine.domain.bayesian_fair_copula_engine import EpistemicDissonanceRecord

                        dissonance_obj = EpistemicDissonanceRecord(
                            record_id=f"DISS_{finding_id}",
                            finding_id=finding_id,
                            claimed_maturity=cmmi,
                            empirical_reality_maturity=max(1.0, cmmi - 1.5),
                            dissonance_weight=0.75,
                            transcript_evidence_quote=str(hc.get("dissonance_analysis") or hc.get("finding") or ""),
                            impact_vector="BOTH",
                        )

                    all_telemetry.append(
                        FindingTelemetry(
                            finding_id=finding_id,
                            tower_id=code,
                            title=title,
                            cmmi_maturity=cmmi,
                            zone=zone,
                            tef_pert_min=(
                                float(explicit_tef_min)
                                if explicit_tef_min is not None
                                else (tef_mode_val * 0.45)
                            ),
                            tef_pert_mode=tef_mode_val,
                            tef_pert_max=(
                                float(explicit_tef_max)
                                if explicit_tef_max is not None
                                else (tef_mode_val * 2.20)
                            ),
                            rto_hours_min=(
                                float(explicit_rto_min)
                                if explicit_rto_min is not None
                                else (rto_mode_val * 0.45)
                            ),
                            rto_hours_mode=rto_mode_val,
                            rto_hours_max=(
                                float(explicit_rto_max)
                                if explicit_rto_max is not None
                                else (rto_mode_val * 2.50)
                            ),
                            secondary_loss_mean=sec_mean_val,
                            is_spof=spof_flag,
                            shared_dependence_factor=rho_val,
                            blast_radius_alpha=alpha_val,
                            catastrophic_rto_hours=cat_rto,
                            direct_replacement_cost=repl_cost,
                            dissonance=dissonance_obj,
                        )
                    )

        if all_telemetry:
            eval_currency = (
                resolved_currency_code
                or str(fin_tel.get("currency_code") or meta.get("currency_code") or "USD").strip().upper()
            )

            portfolio_summary = engine.evaluate_portfolio(
                all_telemetry, currency_code=eval_currency
            )
            global_payload["portfolio_summary"] = {
                "currency_code": portfolio_summary.currency_code,
                "total_portfolio_ale": portfolio_summary.total_portfolio_ale,
                "total_primary_ale": portfolio_summary.total_primary_ale,
                "total_secondary_ale": portfolio_summary.total_secondary_ale,
                "three_year_cost_of_inaction": portfolio_summary.three_year_cost_of_inaction,
                "portfolio_var_90": portfolio_summary.portfolio_var_90,
                "portfolio_var_95": portfolio_summary.portfolio_var_95,
                "portfolio_var_99": portfolio_summary.portfolio_var_99,
                "diversification_ratio": portfolio_summary.diversification_ratio,
                "total_standalone_sum": portfolio_summary.total_standalone_sum,
            }

            configured_domain_weights = fin_tel.get("domain_weights") or {}
            for code, payload in hydrated_map.items():
                if code in portfolio_summary.towers:
                    t_result = portfolio_summary.towers[code]
                    payload["portfolio_allocated_ale"] = t_result.portfolio_allocated_ale
                    payload["primary_fair_ale"] = t_result.primary_ale
                    payload["secondary_fair_ale"] = t_result.secondary_ale
                    payload["worst_crisis_event"] = t_result.worst_crisis_event
                    payload["worst_crisis_rto_hours"] = t_result.worst_crisis_rto_hours

                    payload["total_fair_ale"] = t_result.standalone_ale
                    payload["total_fair_p90"] = t_result.var_90
                    payload["total_fair_max"] = t_result.var_99

                    finding_results = {f.finding_id: f for f in t_result.findings}

                    pillars = payload.get("pillars_analysis") or []
                    for pillar in pillars:
                        if not isinstance(pillar, dict):
                            continue
                        for hc in pillar.get("health_check_asis", []):
                            if not isinstance(hc, dict):
                                continue
                            f_id = hc.get("node_id")
                            if f_id in finding_results:
                                f_res = finding_results[f_id]
                                hc["fair_ale_score"] = f_res.portfolio_allocated_ale
                                hc["fair_p90_score"] = f_res.var_90
                                hc["fair_max_score"] = f_res.var_99
                                hc["worst_crisis_event"] = f_res.worst_crisis_event
                                hc["worst_crisis_rto_hours"] = f_res.worst_crisis_rto_hours
                                hc["dissonance_applied"] = f_res.dissonance_applied

                    if persist_to_disk:
                        code_lower = code.lower()
                        local_tower_dir = resolved_repo_root / "working" / client_id_norm / code
                        local_payload_path = local_tower_dir / f"blueprint_{code_lower}_payload.json"
                        if local_payload_path.exists():
                            with open(local_payload_path, "w", encoding="utf-8") as pf:
                                json.dump(payload, pf, indent=2, ensure_ascii=False)

        return hydrated_map
