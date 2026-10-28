from __future__ import annotations

import importlib
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable

_NUMBER_TOKEN_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9])([+-]?\d[\d.,]*(?:[eE][+-]?\d+)?)\s*([kKmMbB])?(?![a-zA-Z0-9])"
)
_MULTIPLIERS = {"k": 1e3, "m": 1e6, "b": 1e9}


from pydantic import BaseModel, ConfigDict, Field

from assessment_engine.infrastructure.config_loader import (
    resolve_canonical_program_id,
)


class StrategicInitiative(BaseModel):
    """Strongly-typed domain model for individual initiatives before aggregation."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    id: str
    tower: str
    title: str
    objective: str = ""
    priority: str = "Alta"
    expected_outcome: str = ""
    capex_estimate: str = "0"
    raw_data: dict[str, Any] = Field(default_factory=dict)


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
        val = float(raw_capex)
        return max(0.0, val) if math.isfinite(val) else 0.0
    if not isinstance(raw_capex, str):
        return 0.0

    match = _NUMBER_TOKEN_PATTERN.search(raw_capex.strip())
    if not match:
        return 0.0

    num_str, suffix = match.group(1), match.group(2)
    multiplier = _MULTIPLIERS.get(suffix.lower(), 1.0) if suffix else 1.0

    if "e" in num_str.lower():
        try:
            val = float(num_str.replace(",", ".")) * multiplier
            return max(0.0, val) if math.isfinite(val) else 0.0
        except ValueError:
            return 0.0

    sign = -1.0 if num_str.startswith("-") else 1.0
    cleaned = re.sub(r"[^\d.,]", "", num_str)
    if not cleaned:
        return 0.0

    normalized = _normalize_capex_separators(cleaned)
    try:
        val = sign * float(normalized) * multiplier
        return max(0.0, val) if math.isfinite(val) else 0.0
    except ValueError:
        return 0.0


def _build_work_package(initiative: StrategicInitiative | dict[str, Any]) -> WorkPackage:
    if isinstance(initiative, StrategicInitiative):
        init_dict = initiative.model_dump()
    else:
        init_dict = dict(initiative)

    capex_raw = init_dict.get("capex_estimate", "")
    capex_str = str(capex_raw) if capex_raw is not None else ""
    raw_num = init_dict.get("capex_numeric")
    capex_val = (
        raw_num
        if raw_num is not None
        else (capex_raw if capex_raw != "" else 0.0)
    )
    capex_num = _parse_capex_estimate(capex_val)
    return WorkPackage(
        id=str(init_dict.get("id", "")),
        tower=str(init_dict.get("tower", "UNKNOWN")),
        title=str(init_dict.get("title", "")),
        objective=str(init_dict.get("objective", "")),
        priority=str(init_dict.get("priority", "")),
        expected_outcome=str(init_dict.get("expected_outcome", "")),
        capex_estimate=capex_str,
        capex_numeric=capex_num,
        raw_data=init_dict,
    )


def _extract_initiative_search_text(initiative: StrategicInitiative | dict[str, Any]) -> str:
    if isinstance(initiative, StrategicInitiative):
        return f"{initiative.title} {initiative.objective} {initiative.expected_outcome}".strip()
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


def aggregate_corporate_projects(
    initiatives: list[StrategicInitiative | dict[str, Any]],
    program_resolver: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
    if not initiatives:
        return {"programs": [], "standalone_initiatives": []}

    resolver = program_resolver or resolve_canonical_program_id
    grouped_packages: dict[str, list[WorkPackage]] = {}
    standalone_initiatives: list[dict[str, Any]] = []

    for initiative in initiatives:
        init_dict = (
            initiative.model_dump()
            if isinstance(initiative, StrategicInitiative)
            else dict(initiative)
        )
        search_text = _extract_initiative_search_text(initiative)
        explicit_pid = init_dict.get("program_id")
        program_id = (
            str(explicit_pid).strip()
            if explicit_pid
            else resolver(search_text)
        )

        if not program_id:
            standalone_initiatives.append(init_dict)
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