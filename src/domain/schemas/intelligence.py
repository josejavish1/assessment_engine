import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


def _flatten_to_string(value: Any) -> str:
    """Helper to convert complex AI responses into clean strings."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Look for typical evidence/summary keys
        for key in [
            "summary",
            "source_evidence",
            "source",
            "evidence",
            "message",
            "reason",
            "audit_id",
            "name",
            "claim",
            "regulation",
            "title",
            "rationale",
        ]:
            if key in value:
                return _flatten_to_string(value[key])
        return str(list(value.values())[0])
    if isinstance(value, list):
        if not value:
            return ""
        return " ".join([_flatten_to_string(x) for x in value])
    return str(value)


def _ensure_list(value: Any) -> List[str]:
    """Helper to ensure a field is always a list of strings."""
    if isinstance(value, list):
        return [_flatten_to_string(x) for x in value]
    if isinstance(value, str):
        if (
            not value.strip()
            or "no hay" in value.lower()
            or "no se encontr" in value.lower()
        ):
            return []
        return [value]
    return []


def _ensure_sourced_text(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict) and "summary" in value:
        return value
    return {
        "summary": _flatten_to_string(value),
        "confidence": {"score": 80, "label": "high", "method": "custom"},
        "sources": [],
    }


def _ensure_transformation(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict) and "stage" in value:
        # Map labels to H1, H2, H3 if AI uses words
        val = str(value.get("stage", "")).upper()
        if "TERM" in val or "H1" in val:
            value["stage"] = "H1"
        elif "MID" in val or "H2" in val:
            value["stage"] = "H2"
        elif "STRAT" in val or "H3" in val:
            value["stage"] = "H3"
        else:
            value["stage"] = "H2"
        return value

    text = _flatten_to_string(value)
    stage = "H2"
    if "short" in text.lower():
        stage = "H1"
    elif "strat" in text.lower():
        stage = "H3"

    return {
        "stage": stage,
        "label": "Grounded Strategy",
        "rationale": text,
        "confidence": {"score": 80, "label": "high", "method": "custom"},
        "sources": [],
    }


class BusinessDriverFact(BaseModel):
    name: str
    fragment_id: Optional[str] = None
    external_url: Optional[str] = None


class ObservationFact(BaseModel):
    fact: str
    fragment_id: Optional[str] = None
    external_url: Optional[str] = None


class RestrictionFact(BaseModel):
    restriction: str
    fragment_id: Optional[str] = None
    external_url: Optional[str] = None


class RegulatoryHarvest(BaseModel):
    sector: str
    frameworks: List[str]
    regulatory_pressures: List[str] = Field(default_factory=list)
    source_evidence: str = Field(default="Evidence extracted from context.")


class BusinessHarvest(BaseModel):
    ceo_agenda: str
    business_drivers: List[BusinessDriverFact]
    financial_tier: str
    priority_markets: List[str] = Field(default_factory=list)
    business_lines: List[str] = Field(default_factory=list)
    active_transformations: List[str] = Field(default_factory=list)
    business_constraints: List[str] = Field(default_factory=list)
    source_evidence: str = Field(default="Evidence extracted from context.")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data["ceo_agenda"] = _flatten_to_string(data.get("ceo_agenda", ""))

        # business_drivers is structured now, handle legacy or raw AI output
        drivers = data.get("business_drivers", [])
        if isinstance(drivers, list):
            new_drivers = []
            for d in drivers:
                if isinstance(d, dict):
                    new_drivers.append(d)
                else:
                    new_drivers.append({"name": _flatten_to_string(d)})
            data["business_drivers"] = new_drivers

        for field in [
            "priority_markets",
            "business_lines",
            "active_transformations",
            "business_constraints",
        ]:
            data[field] = _ensure_list(data.get(field, []))

        ft = str(data.get("financial_tier", "Tier 2"))
        match = re.search(r"Tier\s*([123])", ft, re.IGNORECASE)
        data["financial_tier"] = f"Tier {match.group(1)}" if match else "Tier 2"

        if "source_evidence" in data:
            data["source_evidence"] = _flatten_to_string(data["source_evidence"])
        return data


class TechHarvest(BaseModel):
    # --- JERARQUÍA SOTA: ATRIBUCIÓN EN CASCADA ---
    group_level_stack: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Stack común a todo el holding o matriz (ej. AWS, SAP, Oracle).",
    )
    entity_specific_overrides: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tecnologías exclusivas de una filial (ej. 400GE en Reintel).",
    )

    # --- MINERÍA DE MADUREZ (DEUDA Y VERSIONES) ---
    technical_debt_and_eol: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Software con versiones detectadas y riesgo de Fin de Vida (EoL).",
    )

    # --- MINERÍA DE ARQUITECTURA (MULTIMODAL) ---
    architecture_and_topology: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Descripción técnica de diagramas: DMZs, Diodos, Redundancia, Topología de red.",
    )

    # --- MÉTRICAS Y RESUMEN ---
    specific_infrastructure_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    tech_footprint_narrative: str
    operating_constraints: List[str] = Field(default_factory=list)
    source_evidence: str = Field(default="Evidence extracted from context.")

    @model_validator(mode="before")
    @classmethod
    def normalize_tech_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        list_fields = [
            "group_level_stack",
            "entity_specific_overrides",
            "technical_debt_and_eol",
            "architecture_and_topology",
            "specific_infrastructure_metrics",
        ]
        for field in list_fields:
            raw = data.get(field, [])
            if isinstance(raw, list):
                data[field] = [
                    x
                    if isinstance(x, dict)
                    else {"item": str(x), "entity": "Global/Group"}
                    for x in raw
                ]
            else:
                data[field] = []
        return data


class ConfidenceV3(BaseModel):
    score: int
    label: str
    method: str = "custom"


class SourceV3(BaseModel):
    source: str
    url: Optional[str] = None


class SourcedTextV3(BaseModel):
    summary: str
    confidence: ConfidenceV3
    sources: List[SourceV3] = Field(default_factory=list)


class TransformationHorizonV3(BaseModel):
    stage: Literal["H1", "H2", "H3"]
    label: str
    rationale: str
    confidence: ConfidenceV3
    sources: List[SourceV3] = Field(default_factory=list)


class ClientDossierV3(BaseModel):
    version: str = "3.0"
    client_name: str
    metadata: Dict[str, Any]
    profile: Dict[str, Any]
    regulatory_context: List[Dict[str, Any]]
    business_context: Dict[str, Any]
    technology_context: Dict[str, Any]  # Contendrá field_metrics y technical_stack
    tower_overrides: Dict[str, Any] = Field(default_factory=dict)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    review: Dict[str, Any]
    extensions: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def total_semantic_resilience(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Ensure context blocks are robust
        if "business_context" in data:
            biz = data["business_context"]
            if "ceo_agenda" in biz:
                biz["ceo_agenda"] = _ensure_sourced_text(biz["ceo_agenda"])
            if "transformation_horizon" in biz:
                biz["transformation_horizon"] = _ensure_transformation(
                    biz["transformation_horizon"]
                )
            if "strategic_priorities" in biz:
                prio = biz["strategic_priorities"]
                if isinstance(prio, list):
                    new_prio = []
                    for p in prio:
                        if isinstance(p, dict) and "name" in p:
                            p["confidence"] = p.get(
                                "confidence",
                                {"score": 80, "label": "high", "method": "custom"},
                            )
                            new_prio.append(p)
                        else:
                            new_prio.append(
                                {
                                    "name": _flatten_to_string(p),
                                    "confidence": {
                                        "score": 80,
                                        "label": "high",
                                        "method": "custom",
                                    },
                                    "sources": [],
                                }
                            )
                    biz["strategic_priorities"] = new_prio

        if "technology_context" in data:
            tech = data["technology_context"]
            if "footprint_summary" in tech:
                tech["footprint_summary"] = _ensure_sourced_text(
                    tech["footprint_summary"]
                )

            # PATRÓN ÉLITE: Asegurar Technical Stack, Field Metrics y Hard Tech Specs
            if "technical_stack" not in tech:
                tech["technical_stack"] = []
            if "field_metrics" not in tech:
                tech["field_metrics"] = []
            if "hard_tech_specs" not in tech:
                tech["hard_tech_specs"] = []

            if "technology_drivers" in tech:
                drivers = tech["technology_drivers"]
                if isinstance(drivers, list):
                    new_drivers = []
                    for d in drivers:
                        if isinstance(d, dict) and "name" in d:
                            d["confidence"] = d.get(
                                "confidence",
                                {"score": 80, "label": "high", "method": "custom"},
                            )
                            new_drivers.append(d)
                        else:
                            new_drivers.append(
                                {
                                    "name": _flatten_to_string(d),
                                    "confidence": {
                                        "score": 80,
                                        "label": "high",
                                        "method": "custom",
                                    },
                                    "sources": [],
                                }
                            )
                    tech["technology_drivers"] = new_drivers

        return data


class ClientDossierV2(BaseModel):
    """Legacy compatibility class."""

    version: str = "2.0"
    client_name: str
    metadata: Dict[str, Any]
    profile: Dict[str, Any]
    regulatory_context: List[Dict[str, Any]]
    business_context: Dict[str, Any]
    technology_context: Dict[str, Any]
    tower_overrides: Dict[str, Any] = Field(default_factory=dict)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    review: Dict[str, Any]
