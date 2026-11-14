"""Universal Multi-Tenant Tower Payload Hydrator.

Hydrates raw tower blueprint payloads with authoritative tenant corporate telemetry,
ensuring 100% Declarative AST compilation compatibility across arbitrary technical domains.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Final, List, Mapping, Optional

from assessment_engine.domain.actuarial_scale_calibrator import (
    resolve_iso_currency_code as _resolve_iso_currency_code,
)
from assessment_engine.domain.actuarial_scale_calibrator import (
    safe_float,
)
from assessment_engine.domain.exceptions import PayloadIntegrityError
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
                    from assessment_engine.domain.taxonomy_resolver import (
                        get_taxonomy_resolver,
                    )
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
                    from assessment_engine.domain.governance import GovernanceScaleEngine

                    risk_res = GovernanceScaleEngine.get_instance().resolve_financial_risk(latent.annual_loss_expectancy)
                    severity = risk_res.severity.value
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
                    from assessment_engine.domain.validation.semantic_gatekeeper import (
                        OntologicalGatekeeper,
                    )
                    from assessment_engine.infrastructure.ontology.taxonomy_loader import (
                        DomainTaxonomyRegistry,
                    )

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

                                # RFC 083: Hydrate pillar declared scores from questionnaire SSOT
                                s_pillar_scores = score_data.get("pillar_scores") or []
                                s_score_map: Dict[str, float] = {}
                                for sp in s_pillar_scores:
                                    sp_id = str(sp.get("pillar_id", "")).strip().upper()
                                    sp_score = (
                                        sp.get("score_exact")
                                        if sp.get("score_exact") is not None
                                        else sp.get("score")
                                    )
                                    if sp_id and sp_score is not None:
                                        s_score_map[sp_id] = float(sp_score)
                                        if "." in sp_id:
                                            s_score_map[sp_id.split(".")[-1]] = float(sp_score)

                                if s_score_map and raw_payload.get("pillars_analysis"):
                                    for pil in raw_payload["pillars_analysis"]:
                                        if isinstance(pil, dict):
                                            p_raw_id = str(
                                                pil.get("pillar_id") or pil.get("id") or ""
                                            ).strip().upper()
                                            dec_s = s_score_map.get(p_raw_id)
                                            if dec_s is None and "." in p_raw_id:
                                                dec_s = s_score_map.get(p_raw_id.split(".")[-1])
                                            if dec_s is not None and pil.get("declared_score") is None:
                                                pil["declared_score"] = dec_s
                                                pil["survey_declared_score"] = dec_s
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

        # Delegate risk quantification exclusively to CanonicalRiskOrchestrator (SR 11-7 SSOT)
        from assessment_engine.application.services.canonical_risk_orchestrator import (
            CanonicalRiskOrchestrator,
        )

        hydrated_map, manifest = CanonicalRiskOrchestrator.quantify_payloads(
            payloads_by_tower=hydrated_map,
            global_context=global_payload,
            persist_to_disk=persist_to_disk,
            client_id=client_id_norm,
            doc_lang=doc_lang,
        )

        if manifest:
            global_payload["portfolio_summary"] = manifest.expected_portfolio_outputs

        return hydrated_map
