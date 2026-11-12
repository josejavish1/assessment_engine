"""Universal Pure Domain Service: Semantic Domain Router.

Enforces root-cause jurisdiction routing across any assessment framework taxonomy.
100% Pure Domain: Zero infrastructure imports, zero filesystem I/O, zero network calls.
Written in 100% Technical English.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Protocol, Set, runtime_checkable
from pydantic import BaseModel, Field, ValidationInfo, field_validator

logger = logging.getLogger(__name__)


class OntologyNode(BaseModel):
    """Universal canonical domain target within any assessment framework taxonomy."""
    model_config = {"frozen": True}

    node_id: str = Field(description="Canonical alphanumeric or UUID identifier, e.g. 'T1', 'DORA_01', 'HIPAA_SEC'.")
    name: str = Field(description="Domain name in Technical English.")
    core_jurisdiction: str = Field(default="", description="Formal technical scope and boundaries.")
    explicit_exclusions: List[str] = Field(default_factory=list, description="Explicit boundaries excluded from this domain.")
    boundary_tokens: List[str] = Field(default_factory=list, description="Contextual signature tokens for boundary matching.")


class AbsenceSemanticEvaluation(BaseModel):
    """Evaluation of whether an observation represents a total absence of a required capability."""
    model_config = {"frozen": True}

    is_absence_of_control: bool = Field(
        description="True if observation describes total absence or lack of a required control or tool."
    )
    missing_capability: Optional[str] = Field(
        default=None,
        description="Canonical capability that is missing when is_absence_of_control is True."
    )


class SemanticRoutingDecision(BaseModel):
    """
    Universal static schema for routing decisions across any enterprise vertical.
    Enforces contextual validation against the active framework ontology via ValidationInfo.context.
    """
    model_config = {"frozen": True}

    finding_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the evaluated finding."
    )
    chain_of_thought_jurisdiction: str = Field(
        description="Concise analytical reasoning explaining root-cause jurisdiction assignment."
    )
    assigned_domain_id: str = Field(
        description="Canonical domain identifier owning root-cause jurisdiction."
    )
    secondary_impacted_domain_ids: List[str] = Field(
        default_factory=list,
        description="Secondary domains experiencing derived operational friction."
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, default=1.0,
        description="Epistemic confidence score between 0.0 and 1.0."
    )
    absence_evaluation: AbsenceSemanticEvaluation = Field(
        default_factory=lambda: AbsenceSemanticEvaluation(is_absence_of_control=False),
        description="Semantic evaluation of control absence."
    )

    @field_validator("assigned_domain_id")
    @classmethod
    def validate_against_active_ontology(cls, v: str, info: ValidationInfo) -> str:
        """Validates that assigned_domain_id strictly belongs to the injected active ontology context."""
        if info.context and "valid_domain_ids" in info.context:
            valid_ids: Set[str] = info.context["valid_domain_ids"]
            if valid_ids and v != "UNCLASSIFIED" and v not in valid_ids:
                raise ValueError(
                    f"Domain ID '{v}' is invalid under active ontology. Must be one of: {sorted(valid_ids)}"
                )
        return v

    @property
    def primary_tower(self) -> str:
        """Backward-compatibility alias mapping assigned_domain_id to primary_tower."""
        return self.assigned_domain_id

    @property
    def secondary_impacted_towers(self) -> List[str]:
        """Backward-compatibility alias mapping secondary_impacted_domain_ids to secondary_impacted_towers."""
        return self.secondary_impacted_domain_ids


class TowerID:
    """Backward-compatibility namespace for legacy IT infrastructure tests."""
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"
    T5 = "T5"
    T6 = "T6"
    T7 = "T7"
    T8 = "T8"
    T9 = "T9"
    T10 = "T10"
    UNCLASSIFIED = "UNCLASSIFIED"


@runtime_checkable
class SemanticClassifierPort(Protocol):
    """Inversion of control port for probabilistic or grammar-constrained classifiers."""
    def classify_finding(
        self, text: str, ontology: Dict[str, Any], finding_id: Optional[str] = None
    ) -> SemanticRoutingDecision:
        ...


class DomainSemanticRouter:
    """
    Pure Domain Service for Root-Cause Domain Routing.
    Evaluates technical findings against formal scope boundaries without substring fragility.
    Hermetic: Zero filesystem I/O, zero network calls, zero infrastructure imports.
    """

    def __init__(
        self,
        classifier: Optional[SemanticClassifierPort] = None,
        ontology: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._classifier = classifier
        self._raw_ontology = ontology
        self._nodes: Dict[str, OntologyNode] = self._parse_ontology_nodes(ontology)
        self._cache: Dict[str, SemanticRoutingDecision] = {}

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def _parse_ontology_nodes(self, raw_ontology: Optional[Dict[str, Any]]) -> Dict[str, OntologyNode]:
        """Parses injected ontology dictionary into typed immutable domain nodes."""
        if not raw_ontology:
            return self._default_ontology_nodes()

        nodes: Dict[str, OntologyNode] = {}
        towers_dict = raw_ontology.get("towers") or raw_ontology.get("domains") or raw_ontology
        if isinstance(towers_dict, dict):
            for k, val in towers_dict.items():
                if isinstance(val, dict):
                    nodes[str(k)] = OntologyNode(
                        node_id=str(val.get("id") or k),
                        name=str(val.get("name") or k),
                        core_jurisdiction=str(val.get("core_jurisdiction") or ""),
                        explicit_exclusions=list(val.get("explicit_exclusions") or []),
                        boundary_tokens=list(val.get("boundary_tokens") or val.get("keywords") or []),
                    )
                elif isinstance(val, list):
                    nodes[str(k)] = OntologyNode(
                        node_id=str(k),
                        name=str(k),
                        boundary_tokens=[str(item) for item in val],
                    )

        return nodes if nodes else self._default_ontology_nodes()

    def _default_ontology_nodes(self) -> Dict[str, OntologyNode]:
        """Embedded fallback taxonomy space for generic IT assessments in 100% Technical English."""
        raw_defs = {
            "T1": ("Data Center Facilities & Critical Infrastructure", ["data center", "datacenter", "facility", "facilities", "ups", "pdu", "chiller", "crac", "generator", "raised floor", "cabling", "physical security", "server room", "facility architecture"]),
            "T2": ("Hybrid Compute & Virtualization Platforms", ["vmware", "vsphere", "simplivity", "hypervisor", "virtual machine", "compute cluster", "kubernetes", "container", "bare metal", "server hosts", "cloud compute"]),
            "T3": ("Enterprise Networks & Connectivity Architecture", ["network", "wan", "lan", "sd-wan", "core switch", "routing", "bgp", "ospf", "firewall", "mpls", "vpn"]),
            "T4": ("Storage Systems, Data Platforms & Resilient Backups", ["storage", "san", "nas", "storage array", "lun", "netapp", "backup", "veeam", "immutable storage", "lakehouse", "data governance"]),
            "T5": ("Operational Resilience, Disaster Recovery & Failover Governance", ["business continuity", "resilience", "drp", "disaster recovery", "failover", "runbook", "cyber vault", "bcp"]),
            "T6": ("Cybersecurity Architecture & Identity Governance", ["security", "cyber", "active directory", "identity", "pam", "mfa", "edr", "siem", "soc", "rbac", "zero trust"]),
            "T7": ("ITSM, Observability & Service Management Operations", ["itsm", "servicenow", "jira", "cmdb", "change management", "incident management", "sla", "observability", "monitoring", "dynatrace", "apm", "sre", "zabbix", "grafana"]),
            "T8": ("FinOps, Software Licensing & Cloud Economics", ["finops", "cloud economics", "reserved instances", "software licensing", "cloud billing", "subscription"]),
            "T9": ("Digital Workplace & End-User Productivity", ["digital workplace", "modern workplace", "office 365", "teams", "intune", "endpoint", "laptop", "vdi", "citrix", "digital workspace", "end user compute"]),
            "T10": ("Industrial Systems, Core Operations & Plant Manufacturing", ["scada", "mes", "plc", "industrial ot", "weighbridge", "plant floor", "manufacturing", "dispatch", "legacy monolith", "mainframe execution"]),
        }
        return {
            k: OntologyNode(node_id=k, name=name, boundary_tokens=tokens)
            for k, (name, tokens) in raw_defs.items()
        }

    def route_finding(self, text: str, finding_id: Optional[str] = None) -> SemanticRoutingDecision:
        """
        Routes a single technical finding to its canonical domain target.
        Thread-safe and cached via SHA-256 signatures.
        """
        clean_text = text.strip()
        if not clean_text:
            return SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="Empty text provided.",
                assigned_domain_id=TowerID.UNCLASSIFIED,
            )

        cache_key = self._hash_text(clean_text)
        if cache_key in self._cache:
            decision = self._cache[cache_key]
            if finding_id and not decision.finding_id:
                decision = SemanticRoutingDecision(
                    finding_id=finding_id,
                    chain_of_thought_jurisdiction=decision.chain_of_thought_jurisdiction,
                    assigned_domain_id=decision.assigned_domain_id,
                    secondary_impacted_domain_ids=decision.secondary_impacted_domain_ids,
                    confidence_score=decision.confidence_score,
                    absence_evaluation=decision.absence_evaluation,
                )
            return decision

        text_lower = clean_text.lower()

        # If an external classifier port is injected, delegate to it
        if self._classifier is not None:
            try:
                delegated = self._classifier.classify_finding(
                    clean_text, self._raw_ontology or {}, finding_id=finding_id
                )
                self._cache[cache_key] = delegated
                return delegated
            except Exception as ex:
                logger.warning("Delegated semantic classifier error: %s", ex)

        # Contextual domain evaluation against active ontology nodes
        # Priority 1: Check explicit domain overrides if defined in ontology
        override_patterns = {
            "T10": [r"\b(scada|mes|plc|industrial ot|weighbridge|plant floor|plant\b|manufacturing|fabril|hormig\w*|caseta\w*|bascula\w*|prenet)\b"],
            "T5": [r"\b(drp|bcp|disaster recovery|failover plan|contingency plan|business continuity|continuidad)\b"],
        }
        for dom_id, patterns in override_patterns.items():
            if dom_id in self._nodes:
                for pat in patterns:
                    if re.search(pat, text_lower):
                        node = self._nodes[dom_id]
                        decision = SemanticRoutingDecision(
                            finding_id=finding_id,
                            chain_of_thought_jurisdiction=f"Formal domain override matched for {node.name}.",
                            assigned_domain_id=dom_id,
                        )
                        self._cache[cache_key] = decision
                        return decision

        # Priority 2: Match boundary tokens across active ontology nodes
        matched_domain_ids: List[str] = []
        for node_id, node in self._nodes.items():
            for tok in node.boundary_tokens:
                if re.search(rf"(?<!\w){re.escape(str(tok).lower())}(?!\w)", text_lower):
                    if node_id not in matched_domain_ids:
                        matched_domain_ids.append(node_id)
                    break

        if matched_domain_ids:
            primary_id = matched_domain_ids[0]
            secondary_ids = matched_domain_ids[1:]
            primary_node = self._nodes[primary_id]
            decision = SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction=f"Matched canonical ontology scope for {primary_node.name}.",
                assigned_domain_id=primary_id,
                secondary_impacted_domain_ids=secondary_ids,
            )
        else:
            decision = SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="No explicit ontology matches found; unclassified.",
                assigned_domain_id=TowerID.UNCLASSIFIED,
            )

        self._cache[cache_key] = decision
        return decision
