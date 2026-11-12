"""Pure Domain Service: Semantic Domain Router.

Enforces root-cause jurisdiction routing across multi-framework domains.
100% Pure Domain: Zero infrastructure imports, zero filesystem I/O, zero network calls.
Written in 100% Technical English.
"""

from __future__ import annotations

import hashlib
import logging
import re
from enum import StrEnum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TowerID(StrEnum):
    """Canonical domain identifier for general infrastructure assessments."""
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


class AbsenceSemanticEvaluation(BaseModel):
    """Evaluation of whether a finding represents a total absence of a required capability."""
    model_config = {"frozen": True}

    is_absence_of_control: bool = Field(
        description="True if finding describes total absence or lack of a required control or tool."
    )
    missing_capability: Optional[str] = Field(
        default=None,
        description="Canonical capability that is missing when is_absence_of_control is True."
    )


class SemanticRoutingDecision(BaseModel):
    """Authoritative decision mapping a technical finding to its root-cause domain."""
    model_config = {"frozen": True}

    finding_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the evaluated finding."
    )
    chain_of_thought_jurisdiction: str = Field(
        description="Concise analytical reasoning explaining the root-cause jurisdiction assignment."
    )
    primary_tower: TowerID = Field(
        description="The canonical technology tower owning root-cause jurisdiction."
    )
    secondary_impacted_towers: List[TowerID] = Field(
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
        self._ontology: Dict[str, Any] = ontology if ontology is not None else self._default_ontology()
        self._cache: Dict[str, SemanticRoutingDecision] = {}

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def _default_ontology(self) -> Dict[str, List[str]]:
        """Embedded fallback dictionary to ensure 100% offline hermetic execution."""
        return {
            "T1": ["data center", "ups", "pdu", "cooling", "generator", "raised floor", "cabling", "physical security"],
            "T2": ["vsphere", "simplivity", "hypervisor", "virtual machine", "compute cluster", "kubernetes", "container"],
            "T3": ["core switch", "routing", "bgp", "ospf", "firewall", "sd-wan", "mpls", "dark fiber"],
            "T4": ["san", "nas", "storage array", "lun", "netapp", "backup", "veeam", "immutable storage"],
            "T5": ["business continuity", "drp", "disaster recovery", "failover", "runbook", "cyber vault"],
            "T6": ["active directory", "identity", "pam", "mfa", "edr", "siem", "soc", "rbac"],
            "T7": ["itsm", "servicenow", "jira", "cmdb", "change management", "incident management", "sla"],
            "T8": ["finops", "cloud economics", "reserved instances", "software licensing", "cloud billing"],
            "T9": ["digital workplace", "intune", "endpoint", "laptop", "vdi", "citrix", "m365"],
            "T10": ["scada", "mes", "plc", "industrial ot", "weighbridge", "plant floor", "truck dispatch", "prenet"],
        }

    def route_finding(self, text: str, finding_id: Optional[str] = None) -> SemanticRoutingDecision:
        """
        Routes a single technical finding to its canonical technology tower.
        Thread-safe and cached via SHA-256 signatures.
        """
        clean_text = text.strip()
        if not clean_text:
            return SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="Empty text provided.",
                primary_tower=TowerID.UNCLASSIFIED,
            )

        cache_key = self._hash_text(clean_text)
        if cache_key in self._cache:
            decision = self._cache[cache_key]
            if finding_id and not decision.finding_id:
                # Re-wrap with finding_id
                decision = SemanticRoutingDecision(
                    finding_id=finding_id,
                    chain_of_thought_jurisdiction=decision.chain_of_thought_jurisdiction,
                    primary_tower=decision.primary_tower,
                    secondary_impacted_towers=decision.secondary_impacted_towers,
                    confidence_score=decision.confidence_score,
                    absence_evaluation=decision.absence_evaluation,
                )
            return decision

        text_lower = clean_text.lower()

        # Invariant: Physical manufacturing plant operations & weighbridges belong strictly to T10
        if re.search(r"\b(hormig\w*|caseta\w*|planta\b|bascula\w*|weighbridge|prenet)\b", text_lower):
            decision = SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="Physical plant and local weighbridge operations belong strictly to T10.",
                primary_tower=TowerID.T10,
            )
            self._cache[cache_key] = decision
            return decision

        # Invariant: Disaster recovery governance & failover runbooks belong strictly to T5
        if re.search(r"\b(drp|bcp|disaster recovery|failover plan|contingency plan)\b", text_lower):
            decision = SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="Disaster recovery plans and service failover governance belong strictly to T5.",
                primary_tower=TowerID.T5,
            )
            self._cache[cache_key] = decision
            return decision

        # If an external classifier port is injected, delegate to it
        if self._classifier is not None:
            try:
                delegated = self._classifier.classify_finding(clean_text, self._ontology, finding_id=finding_id)
                self._cache[cache_key] = delegated
                return delegated
            except Exception as ex:
                logger.warning("Delegated semantic classifier error: %s", ex)

        # Deterministic boundary matching against loaded formal ontology
        matched_towers: List[TowerID] = []
        for tower_str, keywords in self._ontology.items():
            if isinstance(keywords, list):
                for kw in keywords:
                    if re.search(rf"(?<!\w){re.escape(str(kw))}(?!\w)", text_lower):
                        try:
                            tower_enum = TowerID(tower_str)
                            if tower_enum not in matched_towers:
                                matched_towers.append(tower_enum)
                        except ValueError:
                            pass
                        break

        if matched_towers:
            primary = matched_towers[0]
            secondaries = matched_towers[1:]
            decision = SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction=f"Matched canonical ontology scope for {primary.value}.",
                primary_tower=primary,
                secondary_impacted_towers=secondaries,
            )
        else:
            decision = SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="No explicit ontology matches found; unclassified.",
                primary_tower=TowerID.UNCLASSIFIED,
            )

        self._cache[cache_key] = decision
        return decision
