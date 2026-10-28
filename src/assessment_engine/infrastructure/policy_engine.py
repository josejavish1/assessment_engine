from __future__ import annotations

import logging
from typing import Any, Dict, List

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies import (
    ArchiMateDeliverablesPolicy,
    BaseSovereignPolicy,
    BusinessCaseGroundingPolicy,
    ClientSanitizationPolicy,
    DeduplicationPolicy,
    FairRiskPolicy,
    OTPerimeterPolicy,
    ReverseTraceabilityPolicy,
    SequencingPolicy,
    _sanitize_risk_tree,
    _sanitize_text_placeholders,
)
from assessment_engine.infrastructure.text_utils import deep_unescape

logger = logging.getLogger(__name__)

POLICY_REGISTRY: Dict[str, Any] = {
    "client_sanitization": ClientSanitizationPolicy,
    "fair_risk": FairRiskPolicy,
    "deduplication": DeduplicationPolicy,
    "sequencing": SequencingPolicy,
    "ot_perimeter": OTPerimeterPolicy,
    "archimate_deliverables": ArchiMateDeliverablesPolicy,
    "business_case_grounding": BusinessCaseGroundingPolicy,
    "reverse_traceability": ReverseTraceabilityPolicy,
}


class SovereignPolicyEngine:
    """Orchestrates the sequential execution of a predefined sovereign policy chain."""

    def __init__(self, graph: EpistemicGraph):
        self.graph = graph
        self.policies: List[BaseSovereignPolicy] = []

        # Load declarative policy chain from the runtime manifest if configured
        try:
            from assessment_engine.infrastructure.config_loader import load_runtime_manifest
            manifest = load_runtime_manifest()
            policy_names = manifest.get("policies", {}).get("sovereign_chain")
        except (OSError, ValueError, KeyError, AttributeError):
            policy_names = None

        if not policy_names:
            policy_names = [
                "client_sanitization",
                "fair_risk",
                "deduplication",
                "sequencing",
                "ot_perimeter",
                "archimate_deliverables",
                "business_case_grounding",
                "reverse_traceability",
            ]

        for name in policy_names:
            policy_cls = POLICY_REGISTRY.get(name)
            if policy_cls:
                self.policies.append(policy_cls())
            else:
                logger.warning(f"Política no registrada en POLICY_REGISTRY: '{name}'")

    def compile(self, blueprint_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Applies the full policy chain sequentially to a configuration payload."""
        payload = deep_unescape(blueprint_payload)

        for policy in self.policies:
            try:
                payload = policy.evaluate_and_patch(self.graph, payload)
            except Exception as e:
                logger.error(f"Error evaluando política {policy.__class__.__name__}: {e}")
                raise e

        return payload


__all__ = [
    "BaseSovereignPolicy",
    "ClientSanitizationPolicy",
    "DeduplicationPolicy",
    "SequencingPolicy",
    "OTPerimeterPolicy",
    "ArchiMateDeliverablesPolicy",
    "BusinessCaseGroundingPolicy",
    "ReverseTraceabilityPolicy",
    "FairRiskPolicy",
    "POLICY_REGISTRY",
    "SovereignPolicyEngine",
    "_sanitize_text_placeholders",
    "_sanitize_risk_tree",
]
