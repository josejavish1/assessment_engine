from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from assessment_engine.schemas.intelligence import ClientDossierV2, ClientDossierV3

logger = logging.getLogger(__name__)


def _as_list_of_strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _confidence_label_from_score(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def build_confidence_block(score: int = 50, method: str = "custom") -> dict[str, Any]:
    """Construct a confidence block dictionary from a numerical score and a method."""
    return {
        "score": score,
        "label": _confidence_label_from_score(score),
        "method": method,
    }


def _confidence_block(score: int = 50, method: str = "custom") -> dict[str, Any]:
    return build_confidence_block(score=score, method=method)


def _confidence_label(value: Any, default: str = "medium") -> str:
    if isinstance(value, str) and value in {"low", "medium", "high"}:
        return value
    if isinstance(value, dict):
        label = str(value.get("label", "")).strip()
        if label in {"low", "medium", "high"}:
            return label
    return default


def _claim_type_for_v2(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"fact", "inference", "assumption"}:
        return normalized
    if normalized in {"scenario", "alternative_hypothesis"}:
        return "assumption"
    return "inference"


_TOWER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "T2": ("compute", "plataforma", "cloud", "híbrida", "hybrid", "hosting"),
    "T3": ("network", "red", "connectivity", "sd-wan", "conectividad", "carrier"),
    "T5": ("resilience", "continuity", "recovery", "dr", "resiliencia", "continuidad"),
    "T6": ("security", "zero trust", "identity", "ciber", "seguridad"),
    "T7": ("itsm", "operaciones", "service desk", "observability", "observabilidad"),
    "T8": ("finops", "governance", "gobierno", "coste", "cost"),
    "T9": ("workplace", "employee", "puesto", "colaboración", "dex"),
}


def infer_related_towers(*texts: str) -> list[str]:
    r"""{'docstring': "Infer associated tower IDs by matching predefined keywords in text.\n\n    Scans a variable number of input strings for keywords defined in the private\n    `_TOWER_KEYWORDS` mapping. The function performs a case-insensitive,\n    whole-word search.\n\n    All input texts are concatenated into a single string and converted to\n    lowercase before matching. A tower is considered a match if any of its\n    associated keywords are present as distinct words in the combined text. The\n    whole-word matching is implemented using regular expressions to prevent\n    substring matches (e.g., matching 'art' within 'cart').\n\n    Args:\n        *texts: A variable number of string arguments to be scanned.\n\n    Returns:\n        list[str]: A list of tower IDs corresponding to the keywords found.\n            Returns an empty list if no matches are identified."}."""
    joined = " ".join(texts).lower()
    matches: list[str] = []
    for tower_id, keywords in _TOWER_KEYWORDS.items():
        if any(
            re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", joined)
            for keyword in keywords
        ):
            matches.append(tower_id)
    return matches


def estimate_confidence_score(
    *,
    source_count: int = 0,
    source_reliability: int | None = None,
    specificity_signals: int = 0,
    uncertainty_penalty: int = 0,
) -> int:
    """Calculate a confidence score from various intelligence signals.

    The score is computed using a heuristic model. It originates from a base
    value of 40 and is adjusted by several factors:

    - Source Count: +10 points per source, capped at 3 sources.
    - Specificity: +5 points per signal, capped at 4 signals.
    - Source Reliability: Adjusts score by `round((reliability - 50) / 5)`.
    - Uncertainty: A direct penalty subtraction.

    The final score is clamped to the inclusive range [15, 95]. All
    arguments are keyword-only.

    Args:
        source_count: The number of independent sources. Contribution is capped
            at 3.
        source_reliability: An optional aggregate reliability score for the sources,
            typically on a 0-100 scale where 50 is neutral.
        specificity_signals: The number of specific, verifiable details in the
            information. Contribution is capped at 4.
        uncertainty_penalty: A penalty to subtract from the score, reflecting
            ambiguity or contradictory evidence.

    Returns:
        An integer representing the computed confidence score, clamped to a value
        between 15 and 95, inclusive.
    """
    base = 40
    base += min(source_count, 3) * 10
    base += min(specificity_signals, 4) * 5
    if source_reliability is not None:
        base += round((source_reliability - 50) / 5)
    base -= uncertainty_penalty
    return max(15, min(95, base))


def _source_refs(
    values: list[str], source_type: str = "public"
) -> list[dict[str, Any]]:
    return [
        {
            "source": value,
            "source_type": source_type,
            "source_reliability_score": 60,
        }
        for value in values
        if value
    ]


def _source_type_for_legacy_payload(data: dict[str, Any]) -> str:
    evidence_text = " ".join(_as_list_of_strings(data.get("evidences", []))).lower()
    if "sintétic" in evidence_text or "smoke" in evidence_text:
        return "synthetic"
    return "public"


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _append_claim(
    claims: list[dict[str, Any]],
    *,
    claim_id: str,
    claim: str,
    claim_type: str,
    sources: list[dict[str, Any]],
    source_reliability_score: int = 60,
    valid_for_domains: list[str] | None = None,
    related_towers: list[str] | None = None,
    specificity_signals: int = 0,
    uncertainty_penalty: int = 0,
) -> None:
    text = claim.strip()
    if not text or any(existing.get("claim") == text for existing in claims):
        return

    claims.append(
        {
            "claim_id": claim_id,
            "claim": text,
            "claim_type": claim_type,
            "confidence": build_confidence_block(
                estimate_confidence_score(
                    source_count=len(sources),
                    source_reliability=source_reliability_score,
                    specificity_signals=specificity_signals,
                    uncertainty_penalty=uncertainty_penalty,
                )
            ),
            "sources": sources,
            "source_reliability_score": source_reliability_score,
            "valid_for_domains": valid_for_domains or ["tower", "global", "commercial"],
            "related_towers": related_towers or infer_related_towers(text),
        }
    )


def is_client_dossier_v2(data: dict[str, Any]) -> bool:
    """Check if a dictionary conforms to the client dossier v2 schema."""
    return (
        isinstance(data, dict)
        and data.get("version") == "2.0"
        and isinstance(data.get("profile"), dict)
        and isinstance(data.get("business_context"), dict)
    )


def is_client_dossier_v3(data: dict[str, Any]) -> bool:
    """Return whether the input dictionary conforms to the client dossier v3 schema."""
    return (
        isinstance(data, dict)
        and data.get("version") == "3.0"
        and isinstance(data.get("metadata"), dict)
        and isinstance(data.get("profile"), dict)
        and isinstance(data.get("business_context"), dict)
        and isinstance(data.get("technology_context"), dict)
    )


def summarize_transformation_horizon(data: dict[str, Any]) -> str:
    """Generates a summary string from a client's transformation horizon data.

    This function processes a client dossier dictionary to extract and format
    transformation horizon information. It handles multiple dossier schemas by
    probing for data in different locations:
      - For v2/v3 dossiers, it expects a nested dictionary at
        `data['business_context']['transformation_horizon']`.
      - For flat structures, it expects data at the top-level key
        `data['transformation_horizon']`.

    The summary is constructed by combining the 'stage', 'label', and 'rationale'
    fields. The headline is formed from 'stage' and 'label', and the 'rationale'
    is appended as a descriptive sentence.

    Args:
        data (dict[str, Any]): The client dossier dictionary.

    Returns:
        str: A formatted summary, typically "{stage}: {label}. {rationale}".
            The format is adjusted if component parts are missing from the source
            data. Returns 'General' if no specific horizon information can be
            extracted.
    """
    if is_client_dossier_v3(data):
        horizon = data.get("business_context", {}).get("transformation_horizon", {})
    elif is_client_dossier_v2(data):
        horizon = data.get("business_context", {}).get("transformation_horizon", {})
    else:
        return str(data.get("transformation_horizon", "General"))

    stage = str(horizon.get("stage", "")).strip()
    label = str(horizon.get("label", "")).strip()
    rationale = str(horizon.get("rationale", "")).strip()

    parts = [part for part in (stage, label) if part]
    headline = ": ".join(parts) if parts else "General"
    return f"{headline}. {rationale}".strip().rstrip(".") + ("." if rationale else "")


def extract_target_maturity_map(data: dict[str, Any]) -> dict[str, float]:
    """Extracts a map of tower IDs to target maturity scores from a client dossier.

    This function supports two primary dossier schemas, identified by the presence
    of specific keys. The dossier version is determined by external functions
    (`is_client_dossier_v2`, `is_client_dossier_v3`).

    1.  **Legacy Dossier:** Data is sourced from a flat map located under the
        `target_maturity_matrix` key.
        Example schema:
            {
                'target_maturity_matrix': {'tower_a': 3.5, 'tower_b': 4.0}
            }

    2.  **V2/V3 Dossier:** Data is sourced from a nested structure where each
        tower's target maturity is specified under the `tower_overrides` key.
        Example schema:
            {
                'tower_overrides': {
                    'tower_a': {'target_maturity': 3.5},
                    'tower_b': {'target_maturity': 4.0}
                }
            }

    The function normalizes all tower ID keys to uppercase. It is robust
    against malformed data; entries with non-numeric scores or incorrect
    structural types are skipped without raising an exception.

    Args:
        data: The client dossier dictionary, conforming to either the legacy
            or v2/v3 schema.

    Returns:
        A dictionary mapping uppercase tower IDs to their float target maturity
        scores. Returns an empty dictionary if the relevant source keys are
        missing or no valid entries can be parsed.
    """
    target_map: dict[str, float] = {}
    if not is_client_dossier_v2(data) and not is_client_dossier_v3(data):
        raw_map = data.get("target_maturity_matrix", {})
        if not isinstance(raw_map, dict):
            return {}
        for tower_id, score in raw_map.items():
            try:
                target_map[str(tower_id).upper()] = float(score)
            except (TypeError, ValueError):
                continue
        return target_map

    for tower_id, tower_data in data.get("tower_overrides", {}).items():
        if not isinstance(tower_data, dict):
            continue
        target_maturity = tower_data.get("target_maturity")
        if target_maturity is None:
            continue
        try:
            target_map[str(tower_id).upper()] = float(target_maturity)
        except (TypeError, ValueError):
            continue
    return target_map


def get_target_maturity(
    data: dict[str, Any], tower_id: str, default: float = 4.0
) -> float:
    """Return the target maturity for a case-insensitive tower ID, or a default value."""
    return extract_target_maturity_map(data).get(tower_id.upper(), default)


def client_intelligence_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    """Transforms a client intelligence data dictionary into the V2 schema.

    The function handles multiple input schemas. If the data already conforms to
    the V2 schema, it is returned directly. Data conforming to the V3 schema is
    systematically restructured to align with V2 specifications. This includes
    remapping fields, transforming nested objects, and normalizing value types.
    For unrecognized or legacy schemas, a basic coercion mechanism is applied
    as a fallback. The resultant dictionary is validated against the V2 Pydantic
    model before being returned.

    Args:
        data: The input client intelligence dictionary. The data can be structured
            according to the V2, V3, or a legacy schema.

    Returns:
        A dictionary conforming to the V2 client dossier schema.

    Raises:
        pydantic.ValidationError: If the data converted from the V3 or a legacy
            format fails to validate against the V2 schema.
    """
    if is_client_dossier_v2(data):
        return data

    if not is_client_dossier_v3(data):
        return coerce_client_dossier_v2(str(data.get("client_name", "")), data)

    profile = data.get("profile", {})
    business_context = data.get("business_context", {})
    technology_context = data.get("technology_context", {})
    regulatory_context = data.get("regulatory_context", [])
    claims = data.get("claims", [])

    payload = {
        "client_name": data.get("client_name", ""),
        "profile": {
            "industry": profile.get("industry", ""),
            "financial_tier": profile.get("financial_tier", "Tier 2"),
            "operating_model": profile.get("operating_model"),
            "regions": _as_list_of_strings(profile.get("regions", [])),
        },
        "regulatory_frameworks": [
            {
                "name": item.get("name", ""),
                "applicability": item.get("applicability", "medium"),
                "sources": item.get("sources", []),
            }
            for item in regulatory_context
            if isinstance(item, dict)
        ],
        "business_context": {
            "ceo_agenda": {
                "summary": business_context.get("ceo_agenda", {}).get("summary", ""),
                "confidence": _confidence_label(
                    business_context.get("ceo_agenda", {}).get("confidence")
                ),
                "sources": business_context.get("ceo_agenda", {}).get("sources", []),
            },
            "technological_drivers": [
                {
                    "name": item.get("name", ""),
                    "confidence": _confidence_label(item.get("confidence")),
                    "sources": item.get("sources", []),
                }
                for item in technology_context.get("technology_drivers", [])
                if isinstance(item, dict)
            ],
            "osint_footprint": {
                "summary": technology_context.get("footprint_summary", {}).get(
                    "summary", ""
                ),
                "confidence": _confidence_label(
                    technology_context.get("footprint_summary", {}).get("confidence")
                ),
                "sources": technology_context.get("footprint_summary", {}).get(
                    "sources", []
                ),
            },
            "transformation_horizon": {
                "stage": business_context.get("transformation_horizon", {}).get(
                    "stage", "H1"
                ),
                "label": business_context.get("transformation_horizon", {}).get(
                    "label", ""
                ),
                "rationale": business_context.get("transformation_horizon", {}).get(
                    "rationale", ""
                ),
                "confidence": _confidence_label(
                    business_context.get("transformation_horizon", {}).get("confidence")
                ),
                "sources": business_context.get("transformation_horizon", {}).get(
                    "sources", []
                ),
            },
            "constraints": _as_list_of_strings(business_context.get("constraints", []))
            + _as_list_of_strings(technology_context.get("operating_constraints", [])),
        },
        "tower_overrides": {
            tower_id.upper(): {
                "target_maturity": tower_data.get("target_maturity", 4.0),
                "business_criticality": _confidence_label(
                    tower_data.get("business_criticality")
                ),
                "regulatory_pressure": _confidence_label(
                    tower_data.get("regulatory_pressure")
                ),
                "change_urgency": _confidence_label(tower_data.get("change_urgency")),
                "constraints": _as_list_of_strings(tower_data.get("constraints", [])),
            }
            for tower_id, tower_data in data.get("tower_overrides", {}).items()
            if isinstance(tower_data, dict)
        },
        "evidence_register": [
            {
                "claim_id": claim.get("claim_id", ""),
                "claim": claim.get("claim", ""),
                "claim_type": _claim_type_for_v2(claim.get("claim_type", "inference")),
                "confidence": _confidence_label(claim.get("confidence")),
                "sources": claim.get("sources", []),
            }
            for claim in claims
            if isinstance(claim, dict)
        ],
    }
    return ClientDossierV2.model_validate(payload).model_dump(mode="json")


def client_intelligence_to_legacy(data: dict[str, Any]) -> dict[str, Any]:
    """Transforms a client intelligence dossier into a legacy dictionary format.

    This function accepts a client intelligence data structure, which may be in a
    v2 or v3 format, and converts it into a flattened, legacy dictionary. If the
    provided dossier is identified as v3, it is first transformed into the v2
    format. The function then validates if the resulting data conforms to the v2
    dossier structure. If it does not, the original input dictionary is returned
    unmodified.

    Args:
        data: The client intelligence dossier, expected to be in v2 or v3 format.

    Returns:
        A new dictionary representing the flattened legacy format, or the
        original `data` dictionary if the input cannot be processed as a v2
        dossier.
    """
    if is_client_dossier_v3(data):
        data = client_intelligence_to_v2(data)

    if not is_client_dossier_v2(data):
        return data

    profile = data.get("profile", {})
    business_context = data.get("business_context", {})
    regulatory_frameworks = data.get("regulatory_frameworks", [])
    technological_drivers = business_context.get("technological_drivers", [])
    evidence_register = data.get("evidence_register", [])

    return {
        "client_name": data.get("client_name", ""),
        "industry": profile.get("industry", ""),
        "financial_tier": profile.get("financial_tier", "Tier 2"),
        "regulatory_frameworks": [
            str(item.get("name", "")).strip()
            for item in regulatory_frameworks
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        ],
        "ceo_agenda": str(
            business_context.get("ceo_agenda", {}).get("summary", "")
        ).strip(),
        "technological_drivers": [
            str(item.get("name", "")).strip()
            for item in technological_drivers
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        ],
        "osint_footprint": str(
            business_context.get("osint_footprint", {}).get("summary", "")
        ).strip(),
        "transformation_horizon": summarize_transformation_horizon(data),
        "target_maturity_matrix": extract_target_maturity_map(data),
        "evidences": [
            str(item.get("claim", "")).strip()
            for item in evidence_register
            if isinstance(item, dict) and str(item.get("claim", "")).strip()
        ],
        "version": data.get("version", "2.0"),
    }


def build_client_context_packet(
    data: dict[str, Any], tower_id: str | None = None
) -> dict[str, Any]:
    """Constructs a structured client context packet from a client dossier dictionary.

    The function inspects the input `data` to determine if it uses the V3
    dossier schema or a legacy format. If the format is V3, it extracts and
    restructures client information—including profile, business, technology, and
    regulatory contexts—into a standardized dictionary. When a `tower_id` is
    provided, the function filters claims to include only those relevant to the
    specified tower and incorporates any tower-specific context overrides. A
    maximum of six relevant claims are included. For non-V3 dossiers, processing
    is delegated to a legacy conversion function.

    Args:
        data: The client dossier dictionary, which may be in the V3 schema or a
            supported legacy format.
        tower_id: An optional, case-insensitive identifier for a business tower. If
            specified, this is used to select tower-specific context and to
            filter the dossier's claims.

    Returns:
        A dictionary representing the client context packet. The packet contains
        summarized information under keys such as `profile`,
        `business_context`, `technology_context`, and a filtered list of
        `priority_claims`.
    """
    if is_client_dossier_v3(data):
        profile = data.get("profile", {})
        business_context = data.get("business_context", {})
        technology_context = data.get("technology_context", {})
        regulatory_context = data.get("regulatory_context", [])
        tower_map = data.get("tower_overrides", {})
        tower_context = tower_map.get((tower_id or "").upper(), {}) if tower_id else {}
        claims = data.get("claims", [])

        relevant_claims = [
            claim
            for claim in claims
            if isinstance(claim, dict)
            and (
                not tower_id
                or not claim.get("related_towers")
                or str(tower_id).upper()
                in [str(item).upper() for item in claim.get("related_towers", [])]
            )
        ][:6]

        return {
            "client_name": data.get("client_name", ""),
            "profile": {
                "industry": profile.get("industry", ""),
                "financial_tier": profile.get("financial_tier", "Tier 2"),
                "operating_model": profile.get("operating_model"),
                "regions": _as_list_of_strings(profile.get("regions", [])),
                "priority_markets": _as_list_of_strings(
                    profile.get("priority_markets", [])
                ),
                "business_lines": _as_list_of_strings(
                    profile.get("business_lines", [])
                ),
            },
            "business_context": {
                "ceo_agenda": business_context.get("ceo_agenda", {}).get("summary", ""),
                "strategic_priorities": [
                    item.get("name", "")
                    for item in business_context.get("strategic_priorities", [])
                    if isinstance(item, dict)
                ],
                "active_transformations": _as_list_of_strings(
                    business_context.get("active_transformations", [])
                ),
                "business_model_signals": _as_list_of_strings(
                    business_context.get("business_model_signals", [])
                ),
                "transformation_horizon": summarize_transformation_horizon(data),
                "constraints": _as_list_of_strings(
                    business_context.get("constraints", [])
                ),
            },
            "technology_context": {
                "footprint_summary": technology_context.get(
                    "footprint_summary", {}
                ).get("summary", ""),
                "technology_drivers": [
                    item.get("name", "")
                    for item in technology_context.get("technology_drivers", [])
                    if isinstance(item, dict)
                ],
                "vendor_dependencies": _as_list_of_strings(
                    technology_context.get("vendor_dependencies", [])
                ),
                "operating_constraints": _as_list_of_strings(
                    technology_context.get("operating_constraints", [])
                ),
                "recent_incident_signals": _as_list_of_strings(
                    technology_context.get("recent_incident_signals", [])
                ),
            },
            "regulatory_context": [
                item.get("name", "")
                for item in regulatory_context
                if isinstance(item, dict)
            ],
            "tower_context": tower_context,
            "priority_claims": [
                {
                    "claim": claim.get("claim", ""),
                    "type": claim.get("claim_type", "inference"),
                    "confidence_score": claim.get("confidence", {}).get("score", 50),
                }
                for claim in relevant_claims
            ],
            "review_status": data.get("review", {}).get(
                "human_review_status", "pending"
            ),
        }

    return client_intelligence_to_legacy(data)


def build_client_context_text(data: dict[str, Any], tower_id: str | None = None) -> str:
    """Build and serialize a client context packet into a formatted JSON string."""
    packet = build_client_context_packet(data, tower_id=tower_id)
    return json.dumps(packet, ensure_ascii=False, indent=2)


def load_client_intelligence(path: Path) -> dict[str, Any]:
    """Load client intelligence data from a JSON file.

    The file is read with 'utf-8-sig' encoding, which handles an optional
    leading BOM. If the specified path does not exist, an empty dictionary
    is returned.

    Args:
        path: The filesystem path to the client intelligence JSON file.

    Returns:
        A dictionary containing the loaded client intelligence data.

    Raises:
        json.JSONDecodeError: If the file contains malformed JSON.
        OSError: If an I/O error occurs while attempting to read the file.
    """
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_client_intelligence_legacy_view(path: Path) -> dict[str, Any]:
    """Load client intelligence data from a file and return it in the legacy view."""
    return client_intelligence_to_legacy(load_client_intelligence(path))


def _coerce_legacy_to_v2(client_name: str, data: dict[str, Any]) -> dict[str, Any]:
    evidence_values = _as_list_of_strings(data.get("evidences", []))
    sources = [{"source": value} for value in evidence_values]

    payload = {
        "client_name": client_name,
        "profile": {
            "industry": str(data.get("industry", "")),
            "financial_tier": str(data.get("financial_tier", "Tier 2")),
            "operating_model": data.get("operating_model"),
            "regions": _as_list_of_strings(data.get("regions", [])),
        },
        "regulatory_frameworks": [
            {
                "name": framework,
                "applicability": "medium",
                "sources": sources,
            }
            for framework in _as_list_of_strings(data.get("regulatory_frameworks", []))
        ],
        "business_context": {
            "ceo_agenda": {
                "summary": str(data.get("ceo_agenda", "")),
                "confidence": "medium",
                "sources": sources,
            },
            "technological_drivers": [
                {
                    "name": driver,
                    "confidence": "medium",
                    "sources": sources,
                }
                for driver in _as_list_of_strings(data.get("technological_drivers", []))
            ],
            "osint_footprint": {
                "summary": str(data.get("osint_footprint", "")),
                "confidence": "medium",
                "sources": sources,
            },
            "transformation_horizon": {
                "stage": "H1",
                "label": str(data.get("transformation_horizon", "General"))[:120]
                or "General",
                "rationale": str(data.get("transformation_horizon", "General")),
                "confidence": "medium",
                "sources": sources,
            },
            "constraints": _as_list_of_strings(data.get("constraints", [])),
        },
        "tower_overrides": {
            tower_id.upper(): {
                "target_maturity": score,
                "business_criticality": "medium",
                "regulatory_pressure": "medium",
                "change_urgency": "medium",
                "constraints": [],
            }
            for tower_id, score in extract_target_maturity_map(data).items()
        },
        "evidence_register": [
            {
                "claim_id": f"claim_{index + 1}",
                "claim": value,
                "claim_type": "inference",
                "confidence": "medium",
                "sources": [{"source": value}],
            }
            for index, value in enumerate(evidence_values)
        ],
    }
    return ClientDossierV2.model_validate(payload).model_dump(mode="json")


def coerce_client_dossier_v2(client_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Coerces a client intelligence data structure into the V2 dossier format.

    This function normalizes a given dictionary into a validated V2 client
    dossier. It handles three cases based on the input data's detected format:
    - V2 format: The data is validated, enriched with `client_name`, and returned.
    - V3 format: The data is down-converted to the V2 format.
    - Legacy format: The data is coerced into the V2 format.

    Args:
        client_name: The name of the client to associate with the dossier.
        data: The raw client intelligence data dictionary, which may be
            structured in V2, V3, or a legacy format.

    Returns:
        A dictionary representing the client dossier, validated and structured
        according to the V2 format.

    Raises:
        pydantic.ValidationError: If the input `data` is identified as V2 but
            fails Pydantic model validation.
        ValueError: If the input `data` is identified as a legacy format but is
            malformed, preventing coercion to V2.
    """
    if is_client_dossier_v2(data):
        dossier = dict(data)
        dossier["client_name"] = client_name
        return ClientDossierV2.model_validate(dossier).model_dump(mode="json")

    if is_client_dossier_v3(data):
        return client_intelligence_to_v2(data)

    return _coerce_legacy_to_v2(client_name, data)


def coerce_client_dossier_v3(client_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Coerces client data from various formats into a standard V3 dossier.

    This function operates as a data migration and enrichment layer. If the input
    `data` already conforms to the V3 schema, it performs lightweight enrichment,
    such as populating default metadata fields. If the `data` is in a legacy
    or v2 format, the function executes a comprehensive transformation. This
    process involves restructuring disparate fields, normalizing data types, and
    generating a series of standardized claims from various input signals. The
    final output is always validated against the V3 schema before being returned.

    Args:
        client_name (str): The unique identifier or name for the client.
        data (dict[str, Any]): A dictionary containing the client's information,
            which can be in a legacy, v2, or the target v3 format.

    Returns:
        dict[str, Any]: A dictionary representing the client dossier, guaranteed
        to conform to the V3 schema and serialized for JSON compatibility.

    Raises:
        pydantic.ValidationError: If the input data (for an existing V3 payload)
            or the coerced payload (from older formats) fails to validate against
            the `ClientDossierV3` Pydantic model.
    """
    if is_client_dossier_v3(data):
        dossier = dict(data)
        dossier["client_name"] = client_name
        metadata = dict(dossier.get("metadata", {}))
        metadata.setdefault("dossier_id", f"{client_name}-{uuid.uuid4().hex[:12]}")
        metadata.setdefault("schema_version", "3.0")
        metadata.setdefault("created_at", _now_iso())
        metadata.setdefault("modified_at", metadata["created_at"])
        metadata.setdefault("generated_by", "assessment_engine")
        metadata.setdefault("lang", "es")
        dossier["metadata"] = metadata
        return ClientDossierV3.model_validate(dossier).model_dump(mode="json")

    base_v2 = (
        data if is_client_dossier_v2(data) else _coerce_legacy_to_v2(client_name, data)
    )
    profile = base_v2.get("profile", {})
    business_context = base_v2.get("business_context", {})
    regulatory_frameworks = base_v2.get("regulatory_frameworks", [])
    evidence_register = base_v2.get("evidence_register", [])
    drivers = business_context.get("technological_drivers", [])
    osint_sources = business_context.get("osint_footprint", {}).get("sources", [])
    ceo_sources = business_context.get("ceo_agenda", {}).get("sources", [])
    now = _now_iso()

    priority_markets = _as_list_of_strings(data.get("priority_markets", []))
    business_lines = _as_list_of_strings(data.get("business_lines", []))
    vendor_dependencies = _as_list_of_strings(data.get("vendor_dependencies", []))
    recent_incident_signals = _as_list_of_strings(
        data.get("recent_incident_signals", [])
    )
    active_transformations = _as_list_of_strings(data.get("active_transformations", []))
    business_constraints = _as_list_of_strings(data.get("business_constraints", []))
    operating_constraints = _as_list_of_strings(data.get("operating_constraints", []))
    regulatory_pressures = _as_list_of_strings(data.get("regulatory_pressures", []))
    evidence_values = _as_list_of_strings(data.get("evidences", []))
    legacy_source_type = _source_type_for_legacy_payload(data)
    legacy_sources = _source_refs(evidence_values, source_type=legacy_source_type)

    generated_claims: list[dict[str, Any]] = []
    for index, claim in enumerate(evidence_register, start=1):
        if not isinstance(claim, dict):
            continue
        claim_sources = claim.get("sources", []) or legacy_sources
        _append_claim(
            generated_claims,
            claim_id=claim.get("claim_id", f"claim_{index}"),
            claim=claim.get("claim", ""),
            claim_type=claim.get("claim_type", "inference"),
            sources=claim_sources,
            source_reliability_score=60 if legacy_source_type == "public" else 50,
            valid_for_domains=["global", "commercial"],
            specificity_signals=len(infer_related_towers(claim.get("claim", ""))),
            uncertainty_penalty=10
            if claim.get("claim_type") in {"assumption", "alternative_hypothesis"}
            else 0,
        )

    for index, framework in enumerate(
        _unique_strings(_as_list_of_strings(data.get("regulatory_frameworks", []))),
        start=1,
    ):
        _append_claim(
            generated_claims,
            claim_id=f"regulatory_{index}",
            claim=f"El cliente opera bajo presión regulatoria de {framework}.",
            claim_type="fact",
            sources=legacy_sources,
            source_reliability_score=65 if legacy_source_type == "public" else 55,
            specificity_signals=1 + len(regulatory_pressures),
            related_towers=infer_related_towers(
                framework, " ".join(regulatory_pressures)
            ),
        )

    if priority_markets or business_lines:
        _append_claim(
            generated_claims,
            claim_id="business_focus_1",
            claim=(
                "La prioridad estratégica combina foco en "
                f"{', '.join(priority_markets[:3]) or 'mercados prioritarios'} y "
                f"crecimiento en {', '.join(business_lines[:4]) or 'líneas clave de negocio'}."
            ),
            claim_type="inference",
            sources=legacy_sources,
            source_reliability_score=60 if legacy_source_type == "public" else 50,
            valid_for_domains=["global", "commercial"],
            specificity_signals=len(priority_markets) + len(business_lines),
        )

    for index, transformation in enumerate(
        _unique_strings(active_transformations), start=1
    ):
        _append_claim(
            generated_claims,
            claim_id=f"transformation_{index}",
            claim=transformation,
            claim_type="inference",
            sources=legacy_sources,
            source_reliability_score=60 if legacy_source_type == "public" else 50,
            valid_for_domains=["tower", "global", "commercial"],
            specificity_signals=1 + len(priority_markets),
            related_towers=infer_related_towers(
                transformation, " ".join(operating_constraints)
            ),
        )

    for index, vendor in enumerate(_unique_strings(vendor_dependencies), start=1):
        _append_claim(
            generated_claims,
            claim_id=f"vendor_dependency_{index}",
            claim=f"Existe dependencia relevante de {vendor}.",
            claim_type="fact",
            sources=legacy_sources,
            source_reliability_score=60 if legacy_source_type == "public" else 50,
            specificity_signals=1 + len(operating_constraints),
            related_towers=infer_related_towers(
                vendor, " ".join(operating_constraints)
            ),
        )

    for index, incident in enumerate(_unique_strings(recent_incident_signals), start=1):
        _append_claim(
            generated_claims,
            claim_id=f"incident_signal_{index}",
            claim=incident,
            claim_type="scenario",
            sources=legacy_sources,
            source_reliability_score=55 if legacy_source_type == "public" else 45,
            specificity_signals=2,
            uncertainty_penalty=5,
            related_towers=infer_related_towers(
                incident, " ".join(operating_constraints)
            ),
        )

    payload = {
        "client_name": client_name,
        "metadata": {
            "dossier_id": f"{client_name}-{uuid.uuid4().hex[:12]}",
            "schema_version": "3.0",
            "created_at": now,
            "modified_at": now,
            "last_verified_at": None,
            "lang": "es",
            "generated_by": "assessment_engine",
            "prompt_version": None,
            "timeliness": {
                "created_at": now,
                "modified_at": now,
                "stale_after_days": 30,
            },
        },
        "profile": {
            "industry": profile.get("industry", ""),
            "financial_tier": profile.get("financial_tier", "Tier 2"),
            "operating_model": profile.get("operating_model"),
            "regions": _as_list_of_strings(profile.get("regions", [])),
            "priority_markets": priority_markets,
            "business_lines": business_lines,
        },
        "regulatory_context": [
            {
                "name": framework.get("name", ""),
                "applicability": framework.get("applicability", "medium"),
                "confidence": _confidence_block(
                    estimate_confidence_score(
                        source_count=len(framework.get("sources", [])),
                        specificity_signals=1
                        + len(infer_related_towers(framework.get("name", ""))),
                    )
                ),
                "sources": framework.get("sources", []),
                "impacted_domains": infer_related_towers(
                    framework.get("name", ""),
                    " ".join(regulatory_pressures),
                ),
            }
            for framework in regulatory_frameworks
            if isinstance(framework, dict)
        ],
        "business_context": {
            "ceo_agenda": {
                "summary": business_context.get("ceo_agenda", {}).get("summary", ""),
                "confidence": _confidence_block(
                    estimate_confidence_score(
                        source_count=len(ceo_sources),
                        specificity_signals=len(priority_markets) + len(business_lines),
                    )
                ),
                "sources": ceo_sources,
                "evidence_strength": "medium",
            },
            "strategic_priorities": [
                {
                    "name": item.get("name", ""),
                    "confidence": _confidence_block(60),
                    "sources": item.get("sources", []),
                    "rationale": None,
                }
                for item in drivers
                if isinstance(item, dict)
            ],
            "business_model_signals": _as_list_of_strings(
                data.get("business_model_signals", [])
            )
            or business_lines,
            "active_transformations": active_transformations,
            "transformation_horizon": {
                "stage": business_context.get("transformation_horizon", {}).get(
                    "stage", "H1"
                ),
                "label": business_context.get("transformation_horizon", {}).get(
                    "label", "General"
                ),
                "rationale": business_context.get("transformation_horizon", {}).get(
                    "rationale", "General"
                ),
                "confidence": _confidence_block(
                    estimate_confidence_score(
                        source_count=len(
                            business_context.get("transformation_horizon", {}).get(
                                "sources", []
                            )
                        ),
                        specificity_signals=len(active_transformations)
                        + len(business_constraints),
                    )
                ),
                "sources": business_context.get("transformation_horizon", {}).get(
                    "sources", []
                ),
            },
            "constraints": _as_list_of_strings(business_context.get("constraints", []))
            or business_constraints,
        },
        "technology_context": {
            "footprint_summary": {
                "summary": business_context.get("osint_footprint", {}).get(
                    "summary", ""
                ),
                "confidence": _confidence_block(
                    estimate_confidence_score(
                        source_count=len(osint_sources),
                        specificity_signals=len(vendor_dependencies)
                        + len(operating_constraints),
                    )
                ),
                "sources": osint_sources,
                "evidence_strength": "medium",
            },
            "technology_drivers": [
                {
                    "name": item.get("name", ""),
                    "confidence": _confidence_block(55),
                    "sources": item.get("sources", []),
                    "rationale": None,
                }
                for item in drivers
                if isinstance(item, dict)
            ],
            "vendor_dependencies": vendor_dependencies,
            "operating_constraints": operating_constraints
            or _as_list_of_strings(business_context.get("constraints", [])),
            "recent_incident_signals": recent_incident_signals,
        },
        "tower_overrides": {
            tower_id.upper(): {
                "target_maturity": tower_data.get("target_maturity", 4.0),
                "business_criticality": _confidence_block(
                    70 if tower_data.get("business_criticality") == "high" else 50
                ),
                "regulatory_pressure": _confidence_block(
                    70 if tower_data.get("regulatory_pressure") == "high" else 50
                ),
                "change_urgency": _confidence_block(
                    70 if tower_data.get("change_urgency") == "high" else 50
                ),
                "rationale": (
                    f"Target derivado del contexto del cliente para {tower_id.upper()} "
                    f"teniendo en cuenta prioridades, restricciones y señales operativas."
                ),
                "constraints": _as_list_of_strings(tower_data.get("constraints", [])),
                "related_claim_ids": [],
            }
            for tower_id, tower_data in base_v2.get("tower_overrides", {}).items()
            if isinstance(tower_data, dict)
        },
        "claims": generated_claims,
        "review": {
            "human_review_status": "pending",
            "review_notes": [],
        },
        "extensions": {},
    }
    validated_dossier = ClientDossierV3.model_validate(payload)
    serialized = validated_dossier.model_dump(mode="json")
    known_towers = list(serialized.get("tower_overrides", {}).keys())
    if known_towers:
        for claim in serialized.get("claims", []):
            if not claim.get("related_towers"):
                claim["related_towers"] = (
                    known_towers[:1] if len(known_towers) == 1 else known_towers[:3]
                )
    for tower_id, tower_data in serialized.get("tower_overrides", {}).items():
        related_claim_ids = [
            claim["claim_id"]
            for claim in serialized.get("claims", [])
            if tower_id in claim.get("related_towers", [])
        ]
        tower_data["related_claim_ids"] = related_claim_ids
    return serialized
