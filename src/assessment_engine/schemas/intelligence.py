from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, field_validator


class RegulatoryHarvest(BaseModel):
    """Represent the collected regulatory intelligence for a specific sector."""

    sector: str
    frameworks: List[str]
    regulatory_pressures: List[str] = Field(default_factory=list)
    source_evidence: str


class BusinessHarvest(BaseModel):
    """Represents a structured collection of business intelligence insights for a company.

    This data model captures a snapshot of a company's strategic landscape,
    including leadership priorities, market focus, and operational details. It is
    designed to be populated by automated analysis systems or human researchers.

    Attributes:
        ceo_agenda: The stated or inferred agenda of the company's CEO.
        business_drivers: A list of key factors or initiatives that propel the
            business forward.
        financial_tier: The company's financial classification. Must be one of
            "Tier 1", "Tier 2", or "Tier 3".
        priority_markets: Geographic or demographic markets that are a primary
            focus. Defaults to an empty list.
        business_lines: The different lines of business or product/service
            categories. Defaults to an empty list.
        active_transformations: Major ongoing projects or changes within the
            organization. Defaults to an empty list.
        business_constraints: Known limitations or challenges facing the business.
            Defaults to an empty list.
        source_evidence: A URL or document reference indicating the origin or
            justification for the collected intelligence.
    """

    ceo_agenda: str
    business_drivers: List[str]
    financial_tier: str = Field(..., pattern="^(Tier 1|Tier 2|Tier 3)$")
    priority_markets: List[str] = Field(default_factory=list)
    business_lines: List[str] = Field(default_factory=list)
    active_transformations: List[str] = Field(default_factory=list)
    business_constraints: List[str] = Field(default_factory=list)
    source_evidence: str


class TechHarvest(BaseModel):
    r"""{'docstring': "A structured container for harvested technical intelligence data.\n\n    This Pydantic model aggregates various signals related to an organization's\n    technology stack, strategic trends, and operational context.\n\n    Attributes:\n        tech_footprint (str): A summary of the organization's known technology\n            stack.\n        tech_trends (List[str]): A list of key technology trends observed within\n            the organization or its industry.\n        vendor_dependencies (List[str]): A list of key third-party vendors and\n            services the organization relies on. Defaults to an empty list.\n        operating_constraints (List[str]): A list of known constraints or\n            limitations affecting operations, such as budget, compliance, or\n            legacy systems. Defaults to an empty list.\n        recent_incident_signals (List[str]): A list of signals and learnings\n            derived from recent operational incidents or outages. Defaults to an\n            empty list.\n        source_evidence (str): A description of or link to the source material\n            from which this intelligence was derived."}."""

    tech_footprint: str
    tech_trends: List[str]
    vendor_dependencies: List[str] = Field(default_factory=list)
    operating_constraints: List[str] = Field(default_factory=list)
    recent_incident_signals: List[str] = Field(default_factory=list)
    source_evidence: str


class ClientDossier(BaseModel):
    r"""{'docstring': 'A data model for a comprehensive client intelligence dossier.\n\nThis model aggregates key business, technological, and strategic information\nabout a client organization to inform strategic engagement.\n\nAttributes:\n    client_name (str): The official name of the client organization.\n    industry (str): The primary industry sector in which the client operates.\n    financial_tier (str): A classification of the client\'s financial standing,\n        e.g., "Tier 1", "Fortune 500".\n    regulatory_frameworks (List[str]): Key regulatory and compliance\n        frameworks applicable to the client.\n    ceo_agenda (str): A summary of the stated priorities and strategic goals\n        of the client\'s Chief Executive Officer.\n    technological_drivers (List[str]): Key technological trends and drivers\n        influencing the client\'s business operations and strategy.\n    osint_footprint (str): A summary of the client\'s public digital footprint\n        derived from Open-Source Intelligence (OSINT).\n    transformation_horizon (str): The expected timeframe for the client\'s major\n        business or technological transformations, e.g., "3-5 years".\n    target_maturity_matrix (Dict[str, float]): A dictionary mapping business or\n        technical capabilities to their target maturity scores.\n    evidences (List[str]): A collection of sources, citations, or evidence\n        supporting the information contained within the dossier.'}."""

    client_name: str
    industry: str
    financial_tier: str
    regulatory_frameworks: List[str]
    ceo_agenda: str
    technological_drivers: List[str]
    osint_footprint: str
    transformation_horizon: str
    target_maturity_matrix: Dict[str, float]
    evidences: List[str]


Confidence = Literal["low", "medium", "high"]
Applicability = Literal["low", "medium", "high"]
HorizonStage = Literal["H1", "H2", "H3"]
ClaimType = Literal["fact", "inference", "assumption"]


class EvidenceRef(BaseModel):
    """Represents a structured reference to a piece of evidence.

    Attributes:
        source (str): A canonical string identifier for the evidence, e.g.,
            a URL, file path, or a database document ID.
        note (str | None): An optional, human-readable annotation regarding
            the evidence.
    """

    source: str
    note: str | None = None


class SourcedText(BaseModel):
    """Represent a text summary with its confidence score and supporting evidence sources."""

    summary: str
    confidence: Confidence = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class SourcedItem(BaseModel):
    """Encapsulates a data item with its assessed confidence and evidentiary sources.

    This data model represents a single piece of information, such as an identified
    software package or version string, and associates it with metadata. The
    metadata includes a confidence score reflecting the system's certainty about
    the information's correctness and a list of references pointing to the raw
    evidence that supports the conclusion.

    Attributes:
        name (str): The value of the information item (e.g., "openssl").
        confidence (Confidence): The confidence level in the accuracy of the item's
            name. Defaults to "medium".
        sources (List[EvidenceRef]): A list of references to the evidence supporting
            this item. Defaults to an empty list.
    """

    name: str
    confidence: Confidence = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class RegulatoryFramework(BaseModel):
    r"""{'docstring': 'Represents a single regulatory framework and its associated evidence.\n\nThis data model encapsulates the core components of a regulatory framework,\nincluding its official name, a qualitative assessment of its applicability, and\nreferences to the source documents that define it.\n\nAttributes:\n    name (str): The official name of the regulatory framework (e.g., \'GDPR\').\n    applicability (Applicability): A qualitative assessment of the framework\'s\n        scope and impact. Defaults to "medium".\n    sources (List[EvidenceRef]): A list of references to the evidence or legal\n        texts that constitute the framework. Defaults to an empty list.'}."""

    name: str
    applicability: Applicability = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class TransformationHorizon(BaseModel):
    """Represents a single proposed transformation within a larger intelligence analysis.

    This data model encapsulates all relevant information about a potential change,
    hypothesis, or confirmed finding, including its justification, confidence level,
    and supporting evidence.

    Attributes:
        stage (HorizonStage): The developmental stage of the transformation.
        label (str): A concise, human-readable name for the transformation.
        rationale (str): A detailed explanation justifying the proposed transformation.
        confidence (Confidence): The assessed confidence level in the transformation's
            validity. Defaults to "medium".
        sources (List[EvidenceRef]): A list of references to evidence supporting
            this transformation. Defaults to an empty list.
    """

    stage: HorizonStage
    label: str
    rationale: str
    confidence: Confidence = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class TowerContext(BaseModel):
    """Defines the context and constraints for a specific technology tower.

    Encapsulates business and operational drivers that guide the assessment and
    evolution of a technology tower. This model is used to tailor
    recommendations and prioritize initiatives based on strategic importance,
    external pressures, and known limitations.

    Attributes:
        target_maturity: The desired maturity level for the tower, on an inclusive
            scale from 1.0 to 5.0.
        business_criticality: The level of importance of this tower to business
            operations. Defaults to "medium".
        regulatory_pressure: The degree of regulatory requirements or scrutiny
            affecting this tower. Defaults to "medium".
        change_urgency: The urgency for implementing changes or improvements to
            the tower. Defaults to "medium".
        constraints: A list of known constraints or limitations (e.g., budget,
            technology, personnel) applicable to the tower. Defaults to an
            empty list.
    """

    target_maturity: float = Field(ge=1.0, le=5.0)
    business_criticality: Confidence = "medium"
    regulatory_pressure: Confidence = "medium"
    change_urgency: Confidence = "medium"
    constraints: List[str] = Field(default_factory=list)


class ClientProfile(BaseModel):
    """Represents a client's profile with key business attributes.

    A data model for storing and validating structured information about a client,
    including their industry, financial standing, and operational footprint.

    Attributes:
        industry (str): The primary industry sector in which the client operates.
        financial_tier (str): The financial classification or tier of the client.
        operating_model (Optional[str]): The client's business operating model,
            such as B2B or D2C. Defaults to None.
        regions (List[str]): Geographical regions where the client has a presence.
            Defaults to an empty list.
    """

    industry: str
    financial_tier: str
    operating_model: str | None = None
    regions: List[str] = Field(default_factory=list)


class BusinessContext(BaseModel):
    """A data model for the comprehensive business context of an organization.

    This model aggregates key strategic, technological, and operational information
    to inform decision-making processes.

    Attributes:
        ceo_agenda (SourcedText): The stated agenda or key priorities of the CEO,
            including source attribution.
        technological_drivers (List[SourcedItem]): A list of key technological
            trends and drivers impacting the business. Defaults to an empty list.
        osint_footprint (SourcedText): An overview of the organization's open-
            source intelligence (OSINT) footprint, with source attribution.
        transformation_horizon (TransformationHorizon): The defined timeframe and
            scope for business transformation initiatives.
        constraints (List[str]): A list of known business, technical, or
            operational constraints. Defaults to an empty list.
    """

    ceo_agenda: SourcedText
    technological_drivers: List[SourcedItem] = Field(default_factory=list)
    osint_footprint: SourcedText
    transformation_horizon: TransformationHorizon
    constraints: List[str] = Field(default_factory=list)


class EvidenceClaim(BaseModel):
    """Represents a single, atomic claim derived from evidence.

    This model structures an assertion about a subject, linking it back to
    specific pieces of evidence from which it was inferred.

    Attributes:
        claim_id (str): A unique identifier for the claim.
        claim (str): The textual statement of the assertion.
        claim_type (ClaimType): The categorical type of the claim.
        confidence (Confidence): The assessed confidence level in the claim's
            accuracy. Defaults to "medium".
        sources (List[EvidenceRef]): A list of references to the evidence that
            supports this claim. Defaults to an empty list.
    """

    claim_id: str
    claim: str
    claim_type: ClaimType
    confidence: Confidence = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class ClientDossierV2(BaseModel):
    r"""{'docstring': 'Represents a version 2.0 structured dossier for a client.\n\nThis model serves as a comprehensive data container for all relevant client\ninformation, including profile, business context, applicable regulations,\nand evidence claims. It is the primary input for various assessment and\nintelligence-gathering processes.\n\nAttributes:\n    version (Literal["2.0"]): The schema version identifier, fixed to "2.0".\n    client_name (str): The unique name or identifier for the client.\n    profile (ClientProfile): A data structure containing the client\'s profile\n        information.\n    regulatory_frameworks (List[RegulatoryFramework]): A list of regulatory\n        frameworks applicable to the client. Defaults to an empty list.\n    business_context (BusinessContext): A data structure describing the\n        client\'s business operations and environment.\n    tower_overrides (Dict[str, TowerContext]): A dictionary mapping tower names\n        to specific contexts. This allows for overrides of the general\n        business context for distinct service lines or business units.\n        Defaults to an empty dictionary.\n    evidence_register (List[EvidenceClaim]): A comprehensive list of all\n        evidence claims asserted within the dossier. Defaults to an empty\n        list.'}."""

    version: Literal["2.0"] = "2.0"
    client_name: str
    profile: ClientProfile
    regulatory_frameworks: List[RegulatoryFramework] = Field(default_factory=list)
    business_context: BusinessContext
    tower_overrides: Dict[str, TowerContext] = Field(default_factory=dict)
    evidence_register: List[EvidenceClaim] = Field(default_factory=list)


class ConfidenceAssessment(BaseModel):
    """Represents a structured assessment of confidence.

    This Pydantic model provides a standardized structure for confidence scoring,
    encapsulating a numerical score, a categorical label, and the method of
    assessment. The model includes a pre-validation hook that normalizes the
    input for the 'label' field to a canonical set of values.

    Attributes:
        score: An integer representing the confidence level on a scale from 0 to
            100, inclusive.
        label: A categorical label from the `Confidence` enum representing the
            confidence level. Common synonyms are normalized before validation.
        method: A string describing the method used to determine the confidence
            assessment. Defaults to "custom".
    """

    score: int = Field(ge=0, le=100)
    label: Confidence
    method: str = "custom"

    @field_validator("label", mode="before")
    @classmethod
    def normalize_label(cls, value: str) -> str:
        r"""{'docstring': "Normalize and standardize a string label for a Pydantic field.\n\n    A Pydantic `before` validator that sanitizes a raw string input. The\n    normalization process involves converting the string to lowercase, removing\n    leading and trailing whitespace, and replacing all hyphens and spaces with\n    underscores.\n\n    Subsequently, specific synonyms are mapped to a canonical set of labels:\n      - 'critical', 'very_high' -> 'high'\n      - 'moderate', 'mid' -> 'medium'\n      - 'very_low' -> 'low'\n\n    If the normalized input does not match a known synonym, the normalized\n    string itself is returned.\n\n    Args:\n        cls: The class on which the validator is defined.\n        value: The raw input string to be processed.\n\n    Returns:\n        The normalized and standardized label string."}."""
        normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in {"critical", "very_high"}:
            return "high"
        if normalized in {"moderate", "mid"}:
            return "medium"
        if normalized in {"very_low"}:
            return "low"
        return normalized


class TimelinessWindow(BaseModel):
    """Encapsulates metadata for assessing the timeliness and validity of information.

    This model provides a structured representation of timestamps and a staleness
    policy, used to programmatically determine if associated data is fresh,
    stale, or expired.

    Attributes:
        created_at: An optional ISO 8601 timestamp string for when the information
            was created.
        modified_at: An optional ISO 8601 timestamp string for the last time the
            information was modified.
        last_verified_at: An optional ISO 8601 timestamp string for the last time
            the information's accuracy was explicitly verified.
        valid_until: An optional ISO 8601 timestamp string indicating an absolute
            expiration time, after which the information is considered invalid.
        stale_after_days: An optional integer specifying the number of days after which
            the information should be considered stale. If provided, must be a
            positive integer (>= 1).
    """

    created_at: str | None = None
    modified_at: str | None = None
    last_verified_at: str | None = None
    valid_until: str | None = None
    stale_after_days: int | None = Field(default=None, ge=1)


class ClaimSource(BaseModel):
    """Models a source of information used to substantiate a claim.

    Attributes:
        source: The primary identifier for the information source, such as a URL,
            document ID, or publication title.
        note: Optional additional context or notes about the source. Defaults to
            None.
        source_type: The classification of the source (e.g., "public", "internal").
            Defaults to "public".
        source_reliability_score: An optional integer score from 0 to 100,
            inclusive, representing the perceived reliability of the source.
            Values outside this range will raise a `pydantic.ValidationError`.
            Defaults to None.
    """

    source: str
    note: str | None = None
    source_type: str = "public"
    source_reliability_score: int | None = Field(default=None, ge=0, le=100)


class SourcedTextV3(BaseModel):
    """Encapsulates a text summary with its confidence, sources, and evidence strength.

    This data model provides a structured representation for a generated text
    summary. It includes an assessment of the model's confidence, a list of
    sources that substantiate claims within the summary, and an optional
    classification of the overall evidence strength.

    Attributes:
        summary: The generated text summary.
        confidence: An object assessing the model's confidence in the summary.
        sources: A list of sources providing evidence for claims made in the
            summary.
        evidence_strength: An optional classification of the overall strength of
            the supporting evidence (e.g., 'STRONG', 'MODERATE').
    """

    summary: str
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)
    evidence_strength: str | None = None


class SourcedItemV3(BaseModel):
    """Represents an atomic, sourced claim with an associated confidence score.

    This data model encapsulates a single piece of extracted information (the
    claim), a structured assessment of confidence in its accuracy, a list of
    evidentiary sources, and an optional textual rationale. It serves as a
    fundamental unit for representing structured knowledge extracted from
    unstructured or semi-structured data.

    Attributes:
        name: The atomic piece of information or the claim itself.
        confidence: A structured object representing the assessed confidence level
            and its basis for the claim in `name`.
        sources: A list of `ClaimSource` objects that provide evidence or
            provenance for the claim. Defaults to an empty list.
        rationale: An optional, human-readable justification for the assigned
            confidence level.
    """

    name: str
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)
    rationale: str | None = None


class RegulatoryFrameworkV3(BaseModel):
    """Represents a single regulatory framework and its assessed characteristics.

    This Pydantic model captures structured data about a regulation, including
    its applicability, the confidence in the assessment, supporting evidence,
    and its areas of impact.

    Attributes:
        name (str): The official designation of the regulatory framework (e.g., "GDPR").
        applicability (Applicability): An enumerated assessment of the framework's
            scope. Defaults to "medium".
        confidence (ConfidenceAssessment): A structured assessment of the confidence
            in the provided data and its rationale.
        sources (List[ClaimSource]): A list of evidentiary sources supporting the
            assessment details.
        impacted_domains (List[str]): A list of business or technical domains
            affected by this regulation.
    """

    name: str
    applicability: Applicability = "medium"
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)
    impacted_domains: List[str] = Field(default_factory=list)


class TransformationHorizonV3(BaseModel):
    """Represents a single transformation horizon with its justification.

    This model captures a specific stage in a transformation process, detailing the
    reasoning, confidence level, and supporting evidence for that stage.

    Attributes:
        stage (HorizonStage): The enumerated stage of the transformation horizon.
        label (str): A human-readable label for this transformation horizon stage.
        rationale (str): A detailed justification or reasoning for the specified
            transformation stage and confidence level.
        confidence (ConfidenceAssessment): An object representing the assessed
            confidence level in the transformation claim.
        sources (List[ClaimSource]): A list of evidentiary sources supporting the
            transformation claim. Defaults to an empty list.
    """

    stage: HorizonStage
    label: str
    rationale: str
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)


class TowerContextV3(BaseModel):
    """Represents the version 3 contextual information for a capability tower.

    This Pydantic model captures various assessments and metadata that define the
    operational environment and strategic requirements for a specific capability.

    Attributes:
        target_maturity: The target maturity level for the capability, defined as an
            inclusive float between 1.0 and 5.0.
        business_criticality: A `ConfidenceAssessment` of the capability's
            importance to the business.
        regulatory_pressure: A `ConfidenceAssessment` of the influence of
            regulatory requirements on the capability.
        change_urgency: A `ConfidenceAssessment` of the urgency for the capability
            to be changed or improved.
        rationale: An optional free-text explanation for the provided contextual
            assessments. Defaults to None.
        constraints: A list of known limitations, restrictions, or dependencies
            that impact the capability. Defaults to an empty list.
        related_claim_ids: A list of identifiers for related claims or evidence
            that support the contextual assessments. Defaults to an empty list.
    """

    target_maturity: float = Field(ge=1.0, le=5.0)
    business_criticality: ConfidenceAssessment
    regulatory_pressure: ConfidenceAssessment
    change_urgency: ConfidenceAssessment
    rationale: str | None = None
    constraints: List[str] = Field(default_factory=list)
    related_claim_ids: List[str] = Field(default_factory=list)


class ClientProfileV3(BaseModel):
    r"""{'docstring': "Represents a structured profile of a client (Version 3).\n\nThis data model captures key business and operational characteristics of a client,\nsuch as industry, financial standing, and geographical presence.\n\nAttributes:\n    industry: The primary industry in which the client operates.\n    financial_tier: A classification of the client's financial standing.\n    operating_model: The client's operational model. Defaults to None.\n    regions: A list of geographical regions where the client is active.\n    priority_markets: A list of key markets targeted by the client.\n    business_lines: A list of the lines of business the client is engaged in."}."""

    industry: str
    financial_tier: str
    operating_model: str | None = None
    regions: List[str] = Field(default_factory=list)
    priority_markets: List[str] = Field(default_factory=list)
    business_lines: List[str] = Field(default_factory=list)


class BusinessContextV3(BaseModel):
    """Represents the comprehensive business context for a company, V3 model.

    Attributes:
        ceo_agenda (SourcedTextV3): The stated agenda or primary focus from the
            CEO, including its source.
        strategic_priorities (list[SourcedItemV3]): A list of key strategic
            goals for the business, each with associated source information.
        business_model_signals (list[str]): A list of indicators or signals
            related to the company's business model.
        active_transformations (list[str]): A list of major ongoing
            transformations within the business.
        transformation_horizon (TransformationHorizonV3): The timeframe and scope
            for business transformations.
        constraints (list[str]): A list of limitations, restrictions, or
            challenges faced by the business.
    """

    ceo_agenda: SourcedTextV3
    strategic_priorities: List[SourcedItemV3] = Field(default_factory=list)
    business_model_signals: List[str] = Field(default_factory=list)
    active_transformations: List[str] = Field(default_factory=list)
    transformation_horizon: TransformationHorizonV3
    constraints: List[str] = Field(default_factory=list)


class TechnologyContextV3(BaseModel):
    """Represents the technology context of a system or component.

    This model captures key aspects of a technology's operational and strategic
    context, including its footprint, driving factors, dependencies, and
    operational considerations.

    Attributes:
        footprint_summary (SourcedTextV3): A text summary, with citations,
            detailing the technology's resource and dependency footprint.
        technology_drivers (List[SourcedItemV3]): A list of sourced items
            representing key technological factors or trends influencing the
            adoption or evolution of this technology.
        vendor_dependencies (List[str]): A list of strings naming external vendors
            on which this technology has a direct dependency.
        operating_constraints (List[str]): A list of strings describing known
            operational constraints or limitations, such as performance
            bottlenecks, scaling limits, or specific environmental requirements.
        recent_incident_signals (List[str]): A list of strings summarizing key
            signals or takeaways derived from recent operational incidents involving
            this technology.
    """

    footprint_summary: SourcedTextV3
    technology_drivers: List[SourcedItemV3] = Field(default_factory=list)
    vendor_dependencies: List[str] = Field(default_factory=list)
    operating_constraints: List[str] = Field(default_factory=list)
    recent_incident_signals: List[str] = Field(default_factory=list)


class IntelligenceClaimV3(BaseModel):
    """Represents a version 3 structured intelligence claim.

    This Pydantic model encapsulates a single piece of intelligence, providing
    metadata for its type, confidence, sources, and applicability across various
    domains and intelligence verticals.

    Attributes:
        claim_id (str): A unique identifier for the intelligence claim.
        claim (str): The textual content of the intelligence assertion.
        claim_type (Literal[
            "fact", "inference", "assumption", "scenario", "alternative_hypothesis"
        ]): The classification of the claim's nature.
        confidence (ConfidenceAssessment): A structured assessment of the confidence
            level in the claim's validity.
        sources (List[ClaimSource]): A list of sources that support or are related
            to the claim. Defaults to an empty list.
        source_reliability_score (Optional[int]): An aggregated reliability score for
            the sources, ranging from 0 to 100 inclusive. Defaults to None.
        valid_for_domains (List[str]): A list of domains where this claim is
            considered applicable (e.g., 'cyber', 'geopolitical'). Defaults to
            an empty list.
        related_towers (List[str]): A list of intelligence towers or verticals
            related to this claim. Defaults to an empty list.
    """

    claim_id: str
    claim: str
    claim_type: Literal[
        "fact", "inference", "assumption", "scenario", "alternative_hypothesis"
    ]
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)
    source_reliability_score: int | None = Field(default=None, ge=0, le=100)
    valid_for_domains: List[str] = Field(default_factory=list)
    related_towers: List[str] = Field(default_factory=list)


class IntelligenceReviewV3(BaseModel):
    """Represents the state and outcome of a human review process for V3 intelligence.

    This model captures the status, approver details, timestamp, and any
    associated notes for a review.

    Attributes:
        human_review_status (Literal["pending", "reviewed", "approved", "rejected"]):
            The current status of the human review. Defaults to "pending".
        approved_by (Optional[str]): The identifier of the user who approved the
            review. Is `None` if the review has not been approved.
        approved_at (Optional[str]): The ISO 8601 timestamp of when the review was
            approved. Is `None` if the review has not been approved.
        review_notes (List[str]): A list of textual notes or comments associated
            with the review process. Defaults to an empty list.
    """

    human_review_status: Literal["pending", "reviewed", "approved", "rejected"] = (
        "pending"
    )
    approved_by: str | None = None
    approved_at: str | None = None
    review_notes: List[str] = Field(default_factory=list)


class IntelligenceMetadataV3(BaseModel):
    """Represents the V3 metadata schema for an intelligence dossier.

    Attributes:
        dossier_id (str): The unique identifier for the dossier.
        schema_version (Literal["3.0"]): The metadata schema version, fixed to '3.0'.
        created_at (str): The ISO 8601 timestamp indicating when the dossier was
            created.
        modified_at (str): The ISO 8601 timestamp of the last modification to the
            dossier.
        last_verified_at (str | None): The optional ISO 8601 timestamp of the last
            manual verification.
        lang (str): The ISO 639-1 language code for the dossier content.
            Defaults to 'es'.
        generated_by (str): Identifier for the system or process that generated
            the dossier. Defaults to 'assessment_engine'.
        prompt_version (str | None): The optional version identifier for the prompt
            used to generate the dossier.
        timeliness (TimelinessWindow | None): The optional time window for which
            the dossier's intelligence is considered relevant.
    """

    dossier_id: str
    schema_version: Literal["3.0"] = "3.0"
    created_at: str
    modified_at: str
    last_verified_at: str | None = None
    lang: str = "es"
    generated_by: str = "assessment_engine"
    prompt_version: str | None = None
    timeliness: TimelinessWindow | None = None


class ClientDossierV3(BaseModel):
    """Defines the schema for a version 3.0 client intelligence dossier.

    This Pydantic model serves as the top-level data structure for aggregating all
    structured intelligence pertaining to a client. It encapsulates information
    ranging from business and technology profiles to regulatory contexts and specific
    compliance assertions, providing a comprehensive and version-controlled view.

    Attributes:
        version (Literal["3.0"]): The schema version identifier, fixed to "3.0".
        client_name (str): The unique name or identifier for the client.
        metadata (IntelligenceMetadataV3): Dossier metadata, including authors and
            creation timestamp.
        profile (ClientProfileV3): High-level descriptive information about the client.
        regulatory_context (List[RegulatoryFrameworkV3]): A list of regulatory
            frameworks applicable to the client. Defaults to an empty list.
        business_context (BusinessContextV3): Information concerning the client's
            business operations and structure.
        technology_context (TechnologyContextV3): Details of the client's technology
            stack, platforms, and infrastructure.
        tower_overrides (Dict[str, TowerContextV3]): A dictionary mapping tower names
            (e.g., a specific business unit or technology stack) to their context
            overrides. Defaults to an empty dictionary.
        claims (List[IntelligenceClaimV3]): A list of specific, verifiable
            intelligence assertions or findings. Defaults to an empty list.
        review (IntelligenceReviewV3): Data regarding the review status, history,
            and approvers of the dossier. Defaults to a new `IntelligenceReviewV3`
            instance.
        extensions (Dict[str, Any]): A flexible key-value store for custom data not
            accommodated by the standard schema fields. Defaults to an empty
            dictionary.
    """

    version: Literal["3.0"] = "3.0"
    client_name: str
    metadata: IntelligenceMetadataV3
    profile: ClientProfileV3
    regulatory_context: List[RegulatoryFrameworkV3] = Field(default_factory=list)
    business_context: BusinessContextV3
    technology_context: TechnologyContextV3
    tower_overrides: Dict[str, TowerContextV3] = Field(default_factory=dict)
    claims: List[IntelligenceClaimV3] = Field(default_factory=list)
    review: IntelligenceReviewV3 = Field(default_factory=IntelligenceReviewV3)
    extensions: Dict[str, Any] = Field(default_factory=dict)
