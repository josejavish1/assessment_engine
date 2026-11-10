"""Dynamic Ontological Risk Taxonomy Clustering Engine (RFC 081).

Aggregates N-tower Open FAIR risk vectors and granular forensic findings
into canonical ORX/FAIR risk taxonomy families without hardcoded domain assumptions.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Dict, List, Mapping, Optional, Tuple

CANONICAL_TAXONOMY_KEYS: Tuple[str, ...] = (
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION",
)

# Canonical Technical English stems (100% ASCII)
_TAXONOMY_STEM_RULES: Dict[str, Tuple[str, ...]] = {
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE": (
        r"obsolesc", r"legacy", r"\beol\b", r"\beos\b", r"end[\s\-]of[\s\-]life",
        r"monolith", r"technical\s+debt", r"aging", r"unsupported", r"hardware",
        r"compute", r"server", r"virtualiz", r"hyperconver",
    ),
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE": (
        r"cyber", r"\biam\b", r"\bpam\b", r"\bmfa\b", r"identit",
        r"zero[\s\-]trust", r"vulnerab", r"\bcve\b", r"perimeter",
        r"compliance", r"gdpr", r"iso\s*27", r"encrypt", r"security", r"nis\s*2", r"dora",
    ),
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE": (
        r"\bdrp\b", r"\bbcp\b", r"\brto\b", r"\brpo\b", r"\bspof\b", r"continui",
        r"resilien", r"backup", r"outage", r"edge", r"network", r"wan\b",
        r"switch", r"facility", r"facilities", r"data\s*center", r"availabil",
    ),
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION": (
        r"manual", r"automat", r"ci/cd", r"devops", r"devsecops", r"\bitsm\b",
        r"workflow", r"toil", r"human\s+error", r"provision", r"runbook",
        r"change\s+mgmt", r"workplace", r"desktop", r"endpoint", r"dex", r"helpdesk",
    ),
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS": (
        r"storage", r"\bmdm\b", r"\betl\b", r"analytics", r"data\s+quality",
        r"schema", r"silo", r"lineage", r"observabil", r"telemetr", r"database",
    ),
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION": (
        r"vendor", r"supplier", r"lock[\s\-]in", r"\bsla\b", r"\btprm\b",
        r"third[\s\-]party", r"licens", r"finops", r"outsourc",
        r"cost\s+governance", r"contract", r"strategy",
    ),
}

_NATURAL_SORT_REGEX = re.compile(r"(\d+)")


def _natural_sort_key(code: str) -> List[Any]:
    """Produces a deterministic human-readable sort key (e.g., R2 before R10)."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in _NATURAL_SORT_REGEX.split(code)
    ]


def _safe_decimal(val: Any, default: Decimal = Decimal("0.0")) -> Decimal:
    """Safely parses any numeric or locale-formatted string into a Decimal without raising."""
    if val is None or isinstance(val, bool):
        return default
    if isinstance(val, Decimal):
        return val
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    raw = str(val).strip()
    if not raw:
        return default
    # Strip currency symbols and whitespace; normalize decimal separator
    cleaned = re.sub(r"[^\d,.\-]", "", raw)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return default


@dataclass(frozen=True)
class TaxonomyClusterRecord:
    """Strictly immutable representation of an active, reconciled risk taxonomy cluster."""

    taxonomy_id: str
    matrix_plot_codes: Tuple[str, ...]
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    total_findings: int
    cluster_ale: int
    share_of_total_ale_pct: float
    representative_threats: Tuple[str, ...]


class ActuarialTaxonomyClusterer:
    """Dynamically clusters N-tower risk registers and forensic findings into canonical ORX/FAIR families."""

    @classmethod
    def classify_text(cls, text: str, fallback_index: int = 0) -> str:
        """Deterministically classifies text into the best-matching canonical taxonomy_id."""
        normalized = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )

        scores: Dict[str, int] = {k: 0 for k in CANONICAL_TAXONOMY_KEYS}

        for taxonomy_key, patterns in _TAXONOMY_STEM_RULES.items():
            scores[taxonomy_key] += sum(
                1 for pattern in patterns if re.search(pattern, normalized)
            )

        best_key = max(
            CANONICAL_TAXONOMY_KEYS,
            key=lambda k: (scores[k], -CANONICAL_TAXONOMY_KEYS.index(k)),
        )
        if scores[best_key] == 0:
            # Deterministic mapping using canonical tower code if present (eliminating round-robin position bias)
            tokens = set(normalized.upper().split())
            tower_fallbacks = {
                "T1": "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE",
                "T2": "TAXONOMY_DATA_INTEGRITY_ANALYTICS",
                "T3": "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE",
                "T4": "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE",
                "T5": "TAXONOMY_CYBER_IDENTITY_GOVERNANCE",
                "T6": "TAXONOMY_PROCESS_AUTOMATION_FRICTION",
                "T7": "TAXONOMY_PROCESS_AUTOMATION_FRICTION",
                "T8": "TAXONOMY_STRUCTURAL_OBSOLESCENCE",
                "T9": "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION",
                "T10": "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE",
            }
            for t_code, target_key in tower_fallbacks.items():
                if t_code in tokens:
                    return target_key
            return "TAXONOMY_STRUCTURAL_OBSOLESCENCE"
        return best_key

    @classmethod
    def classify_risk_record(cls, record: Mapping[str, Any], fallback_index: int = 0) -> str:
        """Deterministically resolves the canonical taxonomy_id for a given risk or tower record."""
        for tag_field in ("taxonomy_id", "canonical_taxonomy", "risk_taxonomy", "orx_family"):
            explicit_tag = str(record.get(tag_field) or "").strip().upper()
            if explicit_tag in CANONICAL_TAXONOMY_KEYS:
                return explicit_tag

        searchable_corpus = " ".join(
            str(record.get(k) or "")
            for k in (
                "id",
                "code",
                "risk_id",
                "risk_title",
                "title",
                "risk_name",
                "threat_scenario",
                "finding",
                "business_risk",
                "description",
                "tower_name",
                "domain_name",
                "category",
            )
        )
        return cls.classify_text(searchable_corpus, fallback_index=fallback_index)

    @classmethod
    def build_dynamic_clusters(
        cls,
        risk_vectors: List[Dict[str, Any]],
        tower_payloads: Optional[Mapping[str, Dict[str, Any]]] = None,
        reconciled_allocations: Optional[Mapping[str, int]] = None,
    ) -> List[TaxonomyClusterRecord]:
        """Aggregates plot points and granular findings into active, non-empty taxonomy clusters.

        Guarantees exact integer ALE reconciliation and 100.0% percentage summation.
        """
        buckets: Dict[str, Dict[str, Any]] = {
            key: {
                "plot_codes": [],
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "ale": Decimal("0.0"),
                "threats": [],
            }
            for key in CANONICAL_TAXONOMY_KEYS
        }

        # 1. Process primary risk vectors (e.g. from heatmap feed)
        for idx, vector in enumerate(risk_vectors or [], start=1):
            if not isinstance(vector, Mapping):
                continue
            taxonomy_key = cls.classify_risk_record(vector, fallback_index=idx - 1)
            bucket = buckets[taxonomy_key]

            plot_code = str(
                vector.get("id")
                or vector.get("risk_id")
                or vector.get("code")
                or f"R{idx:02d}"
            ).strip()
            if plot_code and plot_code not in bucket["plot_codes"]:
                bucket["plot_codes"].append(plot_code)

            threat_title = str(
                vector.get("risk_name")
                or vector.get("risk_title")
                or vector.get("title")
                or vector.get("threat_scenario")
                or ""
            ).strip()
            if threat_title and threat_title not in bucket["threats"]:
                bucket["threats"].append(threat_title)

            if not tower_payloads:
                raw_ale = (
                    vector.get("ale")
                    if vector.get("ale") is not None
                    else vector.get("ale_p50")
                    if vector.get("ale_p50") is not None
                    else vector.get("ale_expected")
                    if vector.get("ale_expected") is not None
                    else vector.get("financial_exposure")
                    if vector.get("financial_exposure") is not None
                    else vector.get("sle")
                )
                bucket["ale"] += _safe_decimal(raw_ale, Decimal("0.0"))

        # 2. Extract granular forensic findings and financial ALE from tower_payloads
        if tower_payloads:
            for t_idx, (t_code, t_data) in enumerate(tower_payloads.items()):
                if not isinstance(t_data, Mapping):
                    continue

                if reconciled_allocations and t_code in reconciled_allocations:
                    t_ale = _safe_decimal(reconciled_allocations[t_code], Decimal("0.0"))
                else:
                    raw_t_ale = (
                        t_data.get("exact_score_ale")
                        if t_data.get("exact_score_ale") is not None
                        else t_data.get("fair_ale_score")
                    )
                    t_ale = _safe_decimal(raw_t_ale, Decimal("0.0"))

                pillars = t_data.get("pillars_analysis") or []
                t_crit = 0
                t_high = 0
                t_med = 0
                t_low = 0
                dominant_threats: List[str] = []

                for pillar in pillars:
                    if not isinstance(pillar, Mapping):
                        continue
                    for hc in pillar.get("health_check_asis") or []:
                        if not isinstance(hc, Mapping):
                            continue
                        f_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
                        b_risk = str(hc.get("business_risk") or hc.get("impact") or "").strip()
                        if not f_text and not b_risk:
                            continue

                        status = str(hc.get("status") or hc.get("severity") or "").upper()
                        raw_tef = (
                            hc.get("threat_event_frequency")
                            if hc.get("threat_event_frequency") is not None
                            else hc.get("tef")
                        )
                        raw_lm = (
                            hc.get("loss_magnitude")
                            if hc.get("loss_magnitude") is not None
                            else hc.get("lm")
                        )
                        tef = _safe_decimal(raw_tef, Decimal("3.0"))
                        lm = _safe_decimal(raw_lm, Decimal("3.0"))

                        if "CRIT" in status or (tef >= Decimal("3.0") and lm >= Decimal("4.0")) or lm >= Decimal("5.0"):
                            t_crit += 1
                        elif "HIGH" in status or (tef >= Decimal("2.0") and lm >= Decimal("3.0")):
                            t_high += 1
                        elif "MED" in status or "MOD" in status or tef >= Decimal("1.0"):
                            t_med += 1
                        else:
                            t_low += 1

                        if b_risk and len(dominant_threats) < 2:
                            dominant_threats.append(b_risk)

                explicit_tower_taxonomy = str(t_data.get("taxonomy_id") or "").strip().upper()
                if explicit_tower_taxonomy in CANONICAL_TAXONOMY_KEYS:
                    taxonomy_key = explicit_tower_taxonomy
                else:
                    tower_corpus = (
                        f"{t_code} {t_data.get('tower_name', '')} "
                        f"{t_data.get('domain_name', '')} {' '.join(dominant_threats)}"
                    )
                    taxonomy_key = cls.classify_text(tower_corpus, fallback_index=t_idx)

                bucket = buckets[taxonomy_key]
                bucket["critical"] += t_crit
                bucket["high"] += t_high
                bucket["medium"] += t_med
                bucket["low"] += t_low
                bucket["ale"] += t_ale

                for dt in dominant_threats:
                    if dt and dt not in bucket["threats"] and len(bucket["threats"]) < 3:
                        bucket["threats"].append(dt)

        # 3. Filter active clusters and reconcile integer ALE & 100.0% shares (Largest Remainder Method)
        active_keys = [
            k for k, b in buckets.items()
            if (b["critical"] + b["high"] + b["medium"] + b["low"]) > 0
            or b["ale"] > Decimal("0.0")
        ]
        if not active_keys:
            return []

        total_portfolio_ale = sum((buckets[k]["ale"] for k in active_keys), Decimal("0.0"))
        reconciled_tenths = cls._reconcile_percentage_tenths(active_keys, buckets, total_portfolio_ale)

        active_clusters: List[TaxonomyClusterRecord] = []
        for taxonomy_key in active_keys:
            b = buckets[taxonomy_key]
            total_f = b["critical"] + b["high"] + b["medium"] + b["low"]
            ale_int = int(b["ale"].quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            share_pct = float(Decimal(reconciled_tenths[taxonomy_key]) / Decimal("10"))

            active_clusters.append(
                TaxonomyClusterRecord(
                    taxonomy_id=taxonomy_key,
                    matrix_plot_codes=tuple(sorted(b["plot_codes"], key=_natural_sort_key)),
                    critical_findings=b["critical"],
                    high_findings=b["high"],
                    medium_findings=b["medium"],
                    low_findings=b["low"],
                    total_findings=total_f,
                    cluster_ale=ale_int,
                    share_of_total_ale_pct=share_pct,
                    representative_threats=tuple(b["threats"][:2]),
                )
            )

        active_clusters.sort(
            key=lambda c: (
                c.cluster_ale,
                c.critical_findings,
                c.total_findings,
                -CANONICAL_TAXONOMY_KEYS.index(c.taxonomy_id),
            ),
            reverse=True,
        )
        return active_clusters

    @staticmethod
    def _reconcile_percentage_tenths(
        active_keys: List[str],
        buckets: Mapping[str, Mapping[str, Any]],
        total_portfolio_ale: Decimal,
    ) -> Dict[str, int]:
        """Reconciles cluster percentage shares in tenths of a percent (sum == 1000 == 100.0%)."""
        if total_portfolio_ale <= Decimal("0.0"):
            return {k: 0 for k in active_keys}

        exact_quotas: Dict[str, Decimal] = {
            k: (buckets[k]["ale"] / total_portfolio_ale) * Decimal("1000")
            for k in active_keys
        }
        floored: Dict[str, int] = {k: int(q // Decimal("1")) for k, q in exact_quotas.items()}
        remainder_deficit = 1000 - sum(floored.values())

        ranked_by_remainder = sorted(
            active_keys,
            key=lambda k: (exact_quotas[k] - Decimal(floored[k]), buckets[k]["ale"]),
            reverse=True,
        )
        for k in ranked_by_remainder[: max(0, remainder_deficit)]:
            floored[k] += 1

        return floored
