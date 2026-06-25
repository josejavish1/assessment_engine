import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


def _flatten_to_string(value: Any) -> str:
    """Parses, sanitizes, and formats AI model output into a standardized string."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Identifies common key names (e.g., 'evidence', 'summary') as anchors to locate data sections within unstructured AI responses.
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
    """Coerces the input value to a list of strings to ensure type consistency."""
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
        # Normalizes unstructured heading labels (e.g., 'Title', 'Subtitle') from AI-generated content to a canonical H1/H2/H3 semantic hierarchy to ensure consistent document structure and rendering.
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
    """Represents a single business driver statement.

    This data model encapsulates the name of a business driver, along with optional
    references to an internal data fragment or an external URL.

    Attributes:
        name (str): The descriptive name of the business driver.
        fragment_id (Optional[str]): An optional identifier for an internal source
            document fragment.
        external_url (Optional[str]): An optional URL pointing to an external
            reference.
    """

    name: str
    fragment_id: Optional[str] = None
    external_url: Optional[str] = None


class ObservationFact(BaseModel):
    """Represent a single, atomic fact with optional source provenance."""

    fact: str
    fragment_id: Optional[str] = None
    external_url: Optional[str] = None


class RestrictionFact(BaseModel):
    """Model a single restriction statement with optional source identifiers."""

    restriction: str
    fragment_id: Optional[str] = None
    external_url: Optional[str] = None


class RegulatoryHarvest(BaseModel):
    """Represents structured findings from regulatory intelligence analysis.

    Encapsulates key findings extracted from a source document concerning the
    regulatory environment of a specific industry sector.

    Attributes:
        sector: The industry or market sector under analysis.
        frameworks: A list of relevant regulatory or legal frameworks identified
            in the source material.
        regulatory_pressures: A list of identified drivers or pressures for
            regulatory change. Defaults to an empty list if not provided.
        source_evidence: A direct quotation or text snippet from the source
            document that substantiates the analysis. Defaults to a placeholder
            string if not explicitly provided.
    """

    sector: str
    frameworks: List[str]
    regulatory_pressures: List[str] = Field(default_factory=list)
    source_evidence: str = Field(default="Evidence extracted from context.")


class BusinessHarvest(BaseModel):
    """A data model for key business intelligence insights.

    This model structures critical information about a business's strategic
    direction, financial standing, and operational context. It includes a
    built-in pre-validation layer that normalizes raw input data from various
    sources to ensure schema conformance. Key transformations include flattening
    nested structures, coercing values into lists, and standardizing financial
    tier and business driver notations.

    Attributes:
        ceo_agenda: The primary strategic focus or agenda of the CEO.
        business_drivers: A list of key factors or initiatives driving the business.
        financial_tier: The company's financial classification (e.g., "Tier 1").
        priority_markets: A list of key geographical or demographic markets.
        business_lines: A list of the company's distinct lines of business.
        active_transformations: A list of ongoing major organizational or
            technological transformations.
        business_constraints: A list of known limitations or constraints affecting
            the business.
        source_evidence: A citation or description of the source from which the
            data was extracted.
    """

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
        """Normalize raw input data prior to Pydantic model validation.

        This class method, acting as a Pydantic `before` validator, standardizes
        raw input data to ensure schema conformance. It accommodates varied data formats
        by performing several key transformations: `ceo_agenda` and `source_evidence`
        are flattened into single strings; `business_drivers` list items are wrapped
        in `{'name': ...}` dictionaries if they are not already dictionaries;
        `priority_markets`, `business_lines`, `active_transformations`, and
        `business_constraints` are coerced into lists; and `financial_tier` is
        normalized to a 'Tier [1-3]' format, defaulting to 'Tier 2' for
        unrecognized inputs.

        Args:
            cls (type): The model class on which the validator is defined.
            data (Any): The raw input data to be processed. Non-dictionary inputs
                are returned without modification.

        Returns:
            Any: The normalized data dictionary for subsequent validation, or the
                original data if it was not a dictionary.
        """
        if not isinstance(data, dict):
            return data
        data["ceo_agenda"] = _flatten_to_string(data.get("ceo_agenda", ""))

        # Provides a compatibility layer for the 'business_drivers' field, transforming legacy or unstructured data formats into the required schema.
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
    """Models a structured analysis of an organization's technology infrastructure.

    This data model aggregates disparate data points concerning a corporate
    technology footprint, including group-level standards, subsidiary-specific
    overrides, technical debt, architectural components, and operational constraints.
    It is designed to provide a comprehensive view for technical due diligence and
    strategic analysis. A pre-validation step normalizes list-based fields to
    ensure a consistent structure of dictionary elements.

    Attributes:
        group_level_stack: The standardized set of technologies and platforms used
            across the parent company or corporate group (e.g., AWS, SAP,
            Oracle).
        entity_specific_overrides: An inventory of technology components deployed
            exclusively within a specific subsidiary that are not part of the
            standard corporate technology stack (e.g., 400GE at Reintel).
        technical_debt_and_eol: A list of identified software components,
            including their versions and End-of-Life (EoL) risk assessment.
        architecture_and_topology: Analysis of network diagrams, detailing topology
            and identifying key architectural elements such as Demilitarized Zones
            (DMZs), data diodes, and redundancy mechanisms.
        specific_infrastructure_metrics: A list of dictionaries containing
            specific, quantifiable metrics extracted from source data.
        tech_footprint_narrative: A prose summary of the overall technology
            footprint.
        operating_constraints: A list of identified operational limitations or
            constraints.
        source_evidence: A string describing the origin or evidence for the
            aggregated data.
    """

    # Implements a cascading attribution model for multi-level analysis.
    group_level_stack: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="The standardized set of technologies and platforms used across the parent company or corporate group (e.g., AWS, SAP, Oracle).",
    )
    entity_specific_overrides: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="An inventory of technology components deployed exclusively within a specific subsidiary that are not part of the standard corporate technology stack (e.g., 400GE at Reintel).",
    )

    # Identifies indicators of technical debt and software versioning anomalies to assess system maturity.
    technical_debt_and_eol: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A list of identified software components, including their versions and End-of-Life (EoL) risk assessment.",
    )

    # Extracts and analyzes architectural components from textual and diagrammatic data sources.
    architecture_and_topology: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Analysis of network diagrams, detailing topology and identifying key architectural elements such as Demilitarized Zones (DMZs), data diodes, and redundancy mechanisms.",
    )

    # Aggregates extracted data points into metrics and generates a summary.
    specific_infrastructure_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    tech_footprint_narrative: str
    operating_constraints: List[str] = Field(default_factory=list)
    source_evidence: str = Field(default="Evidence extracted from context.")

    @model_validator(mode="before")
    @classmethod
    def normalize_tech_fields(cls, data: Any) -> Any:
        """Normalize specific fields to a list-of-dictionaries format.

        A Pydantic model validator that operates before standard validation
        (`mode="before"`) to enforce a consistent structure for specific data fields.
        The validator targets the following fields: `group_level_stack`,
        `entity_specific_overrides`, `technical_debt_and_eol`,
        `architecture_and_topology`, and `specific_infrastructure_metrics`.

        The normalization process involves two key transformations:
        1.  If a target field is missing from the input data or its value is not a
            list, it is replaced with an empty list.
        2.  If a target field's value is a list, each element is inspected. Any
            element that is not a dictionary is wrapped into a dictionary with the
            structure `{'item': str(element), 'entity': 'Global/Group'}`.

        This pre-processing step makes the model more robust to varied or malformed
        input, ensuring that subsequent validation logic can safely expect a
        list-of-dictionaries for these fields.

        Args:
            cls: The model class on which the validator is defined.
            data: The raw input data to be validated. If this is not a dictionary,
                it is returned unmodified.

        Returns:
            The input data with the specified fields normalized. Returns the
            original data object if it is not a dictionary.
        """
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
    """Model a confidence score with its associated qualitative label and provenance."""

    score: int
    label: str
    method: str = "custom"


class SourceV3(BaseModel):
    """Represent an information source with its textual content and an optional URL."""

    source: str
    url: Optional[str] = None


class SourcedTextV3(BaseModel):
    """Represents a textual summary with its confidence score and supporting sources.

    This data model encapsulates a generated textual summary, its associated
    confidence level, and a list of sources that substantiate its content.

    Attributes:
        summary: The generated textual summary.
        confidence: An object representing the confidence level of the summary.
        sources: A list of source objects that provide evidence or context for the
            summary. Defaults to an empty list.
    """

    summary: str
    confidence: ConfidenceV3
    sources: List[SourceV3] = Field(default_factory=list)


class TransformationHorizonV3(BaseModel):
    """Data model for a single transformation horizon assessment (v3).

    The transformation horizon framework (H1, H2, H3) is a strategic model used to
    categorize initiatives based on their projected time to impact and proximity
    to an organization's core business.

    Attributes:
        stage (Literal["H1", "H2", "H3"]): The transformation horizon category.
            'H1' typically denotes incremental improvements, 'H2' represents
            adjacent opportunities, and 'H3' signifies disruptive innovations.
        label (str): A human-readable name for the assigned horizon.
        rationale (str): A detailed justification for the horizon classification.
        confidence (ConfidenceV3): A data structure representing the confidence level
            associated with the assessment.
        sources (List[SourceV3]): A list of data sources or references that
            support the assessment.
    """

    stage: Literal["H1", "H2", "H3"]
    label: str
    rationale: str
    confidence: ConfidenceV3
    sources: List[SourceV3] = Field(default_factory=list)


class ClientDossierV3(BaseModel):
    r"""{'docstring': 'Represents a structured dossier of client intelligence data, version 3.0.\n\nThis model serves as the canonical schema for capturing comprehensive client\ninformation, including their profile, business and technology contexts,\nregulatory landscape, and strategic priorities. It is designed to be populated\nfrom various data sources and includes robust pre-validation logic to handle\nstructural inconsistencies.\n\nAttributes:\n    version: The schema version identifier.\n    client_name: The legal name of the client entity.\n    metadata: A dictionary for metadata, such as creation timestamps or source IDs.\n    profile: A dictionary containing client profile information (e.g., industry, size).\n    regulatory_context: A list of dictionaries detailing the relevant regulatory environment.\n    business_context: A dictionary describing the client\'s business landscape, including strategic goals.\n    technology_context: A dictionary detailing the client\'s technology stack, architecture, and drivers.\n    tower_overrides: A dictionary for custom overrides related to specific business units or "towers".\n    claims: A list of verifiable assertions made about the client.\n    review: A dictionary containing review status and quality assurance metadata.\n    extensions: A dictionary for custom, non-standard data extensions.'}."""

    version: str = "3.0"
    client_name: str
    metadata: Dict[str, Any]
    profile: Dict[str, Any]
    regulatory_context: List[Dict[str, Any]]
    business_context: Dict[str, Any]
    technology_context: Dict[str, Any]  #
    tower_overrides: Dict[str, Any] = Field(default_factory=dict)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    review: Dict[str, Any]
    extensions: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def total_semantic_resilience(cls, data: Any) -> Any:
        """Pre-processes and normalizes raw input data before model validation.

        This Pydantic `model_validator` operates in 'before' mode to enforce a
        consistent input schema, primarily for handling structural variations from
        sources like large language model outputs. It performs several normalization
        steps: it ensures the existence of critical keys within `technology_context`
        (e.g., `technical_stack`), transforms list-based fields like
        `strategic_priorities` and `technology_drivers` into structured
        dictionaries, and injects default confidence scores and source lists if
        they are absent. This pre-validation enhances data resilience and prevents
        downstream parsing errors.

        Args:
            cls: The model class to which the validator is attached.
            data: The raw input data, expected to be a dictionary, to be normalized.

        Returns:
            The normalized data dictionary prepared for subsequent Pydantic validation.
        """
        if not isinstance(data, dict):
            return data

        # The context block parser is designed to accommodate variations in AI model output formats to prevent downstream parsing errors.
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

            # Validates the presence and structure of critical data fields (e.g., TechnicalStack, FieldMetrics, HardTechSpecs) that are required for subsequent analysis.
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
    """A data model for a version 2.0 client dossier.

    This model provides a structured, versioned format for client information,
    ensuring data integrity and compatibility across systems. It serves as the
    authoritative schema for client-related intelligence data.

    Attributes:
        version (str): The schema version identifier, fixed to "2.0".
        client_name (str): The legal or common name of the client.
        metadata (Dict[str, Any]): A dictionary containing dossier metadata, such as
            creation date and author.
        profile (Dict[str, Any]): A dictionary containing client profile
            information, such as industry, size, and location.
        regulatory_context (List[Dict[str, Any]]): A list of dictionaries, each
            describing an applicable regulatory environment (e.g., GDPR, CCPA).
        business_context (Dict[str, Any]): A dictionary describing the client's
            business domain, operational model, and strategic objectives.
        technology_context (Dict[str, Any]): A dictionary detailing the client's
            technology stack, key systems, and infrastructure.
        tower_overrides (Dict[str, Any]): An optional dictionary for overrides
            applied to specific business units or "towers". Defaults to an empty
            dictionary.
        claims (List[Dict[str, Any]]): An optional list of dictionaries representing
            specific claims or assertions made within the dossier. Defaults to an
            empty list.
        review (Dict[str, Any]): A dictionary containing the review status, history,
            and approver information for the dossier.
    """

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
