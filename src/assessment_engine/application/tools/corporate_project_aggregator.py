from __future__ import annotations

import importlib
import re
from dataclasses import dataclass, field
from typing import Any, Callable

_CLEAN_CAPEX_PATTERN = re.compile(r"[^\d.,-]")


def _resolve_loader() -> Callable[[str], str | None]:
    candidate_modules = (
        "assessment_engine.config_loader",
        "assessment_engine.infrastructure.config_loader",
        "assessment_engine.infrastructure.config.config_loader",
        "assessment_engine.domain.config_loader",
        "assessment_engine.application.config_loader",
        "config_loader",
    )
    for mod_name in candidate_modules:
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, "resolve_canonical_program_id", None)
            if callable(fn):
                return fn
        except ImportError:
            continue
    return _fallback_resolve_canonical_program_id


def _fallback_resolve_canonical_program_id(text: str) -> str | None:
    lowered = text.lower()
    if any(k in lowered for k in ("observabilidad", "siem", "telemetría", "telemetria", "snmp", "monitorización", "monitorizacion")):
        return "PROG_OBSERVABILITY"
    if any(k in lowered for k in ("zero trust", "iam", "mfa", "identidades")):
        return "PROG_ZERO_TRUST"
    return None


resolve_canonical_program_id: Callable[[str], str | None] = _resolve_loader()


@dataclass(frozen=True)
class WorkPackage:
    id: str
    tower: str
    title: str
    objective: str = ""
    priority: str = ""
    expected_outcome: str = ""
    capex_estimate: str = ""
    capex_numeric: float = 0.0
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CorporateProgram:
    program_id: str
    participating_towers: list[str]
    work_packages: list[WorkPackage]
    linear_capex_numeric: float
    consolidated_capex_numeric: float
    synergy_savings_numeric: float


def _is_thousand_separated(parts: list[str]) -> bool:
    if len(parts) > 2:
        return True
    return len(parts) == 2 and len(parts[1]) == 3


def _normalize_single_separator(cleaned: str, sep: str, decimal_replacement: str) -> str:
    if _is_thousand_separated(cleaned.split(sep)):
        return cleaned.replace(sep, "")
    return cleaned.replace(sep, decimal_replacement)


def _normalize_capex_separators(cleaned: str) -> str:
    if "." in cleaned and "," in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            return cleaned.replace(".", "").replace(",", ".")
        return cleaned.replace(",", "")
    if "." in cleaned:
        return _normalize_single_separator(cleaned, ".", ".")
    if "," in cleaned:
        return _normalize_single_separator(cleaned, ",", ".")
    return cleaned


def _parse_capex_estimate(raw_capex: Any) -> float:
    if isinstance(raw_capex, (int, float)) and not isinstance(raw_capex, bool):
        return float(raw_capex)
    if not isinstance(raw_capex, str):
        return 0.0

    cleaned = _CLEAN_CAPEX_PATTERN.sub("", raw_capex.strip())
    if not cleaned:
        return 0.0

    normalized = _normalize_capex_separators(cleaned)
    try:
        return float(normalized)
    except ValueError:
        return 0.0


def _build_work_package(initiative: dict[str, Any]) -> WorkPackage:
    capex_raw = initiative.get("capex_estimate", "")
    capex_str = str(capex_raw) if capex_raw is not None else ""
    capex_num = _parse_capex_estimate(
        initiative.get("capex_numeric", capex_raw if capex_raw != "" else 0.0)
    )
    return WorkPackage(
        id=str(initiative.get("id", "")),
        tower=str(initiative.get("tower", "UNKNOWN")),
        title=str(initiative.get("title", "")),
        objective=str(initiative.get("objective", "")),
        priority=str(initiative.get("priority", "")),
        expected_outcome=str(initiative.get("expected_outcome", "")),
        capex_estimate=capex_str,
        capex_numeric=capex_num,
        raw_data=dict(initiative),
    )


def _extract_initiative_search_text(initiative: dict[str, Any]) -> str:
    title = str(initiative.get("title", ""))
    objective = str(initiative.get("objective", ""))
    outcome = str(initiative.get("expected_outcome", ""))
    return f"{title} {objective} {outcome}".strip()


def _create_corporate_program(
    program_id: str, packages: list[WorkPackage]
) -> CorporateProgram:
    towers = sorted({wp.tower for wp in packages if wp.tower})
    tower_count = max(len(towers), 1)
    linear_capex = sum(wp.capex_numeric for wp in packages)
    synergy_factor = 1.0 / (tower_count**0.25)
    consolidated_capex = round(linear_capex * synergy_factor, 2)
    synergy_savings = round(max(0.0, linear_capex - consolidated_capex), 2)

    return CorporateProgram(
        program_id=program_id,
        participating_towers=towers,
        work_packages=list(packages),
        linear_capex_numeric=linear_capex,
        consolidated_capex_numeric=consolidated_capex,
        synergy_savings_numeric=synergy_savings,
    )


def aggregate_corporate_projects(initiatives: list[dict[str, Any]]) -> dict[str, Any]:
    if not initiatives:
        return {"programs": [], "standalone_initiatives": []}

    grouped_packages: dict[str, list[WorkPackage]] = {}
    standalone_initiatives: list[dict[str, Any]] = []

    for initiative in initiatives:
        search_text = _extract_initiative_search_text(initiative)
        program_id = resolve_canonical_program_id(search_text)

        if not program_id:
            standalone_initiatives.append(dict(initiative))
            continue

        work_package = _build_work_package(initiative)
        grouped_packages.setdefault(program_id, []).append(work_package)

    programs = [
        _create_corporate_program(prog_id, pkgs)
        for prog_id, pkgs in grouped_packages.items()
    ]

    return {
        "programs": programs,
        "standalone_initiatives": standalone_initiatives,
    }