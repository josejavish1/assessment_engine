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
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Final, List, Mapping, Optional

from assessment_engine.domain.actuarial_scale_calibrator import safe_float

logger = logging.getLogger(__name__)

DEFAULT_ANNUAL_REVENUE: Final[float] = 1_000_000_000.0
HOURS_IN_YEAR: Final[float] = 8760.0
DEFAULT_REVENUE_EXPOSURE_FACTOR: Final[float] = 0.001
DEFAULT_RECOVERY_CEILING_HOURS: Final[float] = 24.0
DEFAULT_PERIMETER_WEIGHT_PCT: Final[float] = 100.0
DEFAULT_ENGAGEMENT_PERIOD: Final[str] = "000000"
DEFAULT_TENANT_PLACEHOLDER_UPPER: Final[str] = "ENTERPRISE"
DEFAULT_TENANT_PLACEHOLDER_TITLE: Final[str] = "Enterprise"
DEFAULT_CURRENCY_CODE: Final[str] = "USD"
DEFAULT_SECTOR_BENCHMARK_LABEL: Final[str] = "Industry Baseline"

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


class TowerPayloadHydrator:
    """Hydrates raw tower blueprint payloads with authoritative corporate telemetry."""

    @staticmethod
    def load_and_hydrate_all_towers(
        repo_root: Path,
        global_payload: Dict[str, Any],
        doc_lang: str = "en",
        target_towers: Optional[List[str]] = None,
        persist_to_disk: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """Loads and hydrates all requested tower payloads."""
        if target_towers is None:
            target_towers = [f"T{i}" for i in range(1, 11)]

        meta = global_payload.get("meta", {})
        client_name = str(
            meta.get("client") or meta.get("client_name") or DEFAULT_TENANT_PLACEHOLDER_UPPER
        ).strip()
        client_id_norm = _sanitize_tenant_slug(client_name)
        currency = str(meta.get("currency") or DEFAULT_CURRENCY_CODE).strip()

        fin_tel = global_payload.get("financial_telemetry") or meta.get("financial_telemetry", {})
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

            tower_fin_tel = raw_payload.get("financial_telemetry") or {}
            effective_tower_hourly_rate = (
                safe_float(raw_payload.get("hourly_downtime_rate"), locale=doc_lang)
                or safe_float(raw_payload.get("hourly_burn_rate"), locale=doc_lang)
                or safe_float(tower_fin_tel.get("authoritative_hourly_downtime_cost"), locale=doc_lang)
                or hourly_rate
            )

            raw_payload["annual_revenue"] = annual_revenue
            raw_payload["hourly_downtime_rate"] = effective_tower_hourly_rate
            raw_payload["hourly_burn_rate"] = effective_tower_hourly_rate

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
                "operational_recovery_ceiling_hours": (
                    safe_float(tower_fin_tel.get("operational_recovery_ceiling_hours"), locale=doc_lang)
                    or DEFAULT_RECOVERY_CEILING_HOURS
                ),
            }

            doc_meta = dict(raw_payload.get("document_meta") or {})
            existing_tower_name = str(
                raw_payload.get("tower_name") or doc_meta.get("tower_name") or ""
            ).strip()
            resolved_tower_name = existing_tower_name or CANONICAL_TOWER_NAMES.get(
                code_upper, f"Domain {code_upper}"
            )
            raw_payload["tower_name"] = resolved_tower_name
            doc_meta["client_name"] = client_name
            doc_meta["currency"] = currency
            doc_meta["doc_lang"] = doc_lang
            doc_meta["annual_revenue"] = annual_revenue
            doc_meta["tower_code"] = code_upper
            doc_meta["tower_name"] = resolved_tower_name
            raw_payload["document_meta"] = doc_meta

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
                            pass
                    if os.path.exists(tmp_path_str):
                        try:
                            os.unlink(tmp_path_str)
                        except OSError:
                            pass
                    raise

            hydrated_map[code_upper] = raw_payload
            logger.info("Successfully hydrated payload for tower %s", code_upper)

        return hydrated_map
