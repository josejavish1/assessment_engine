"""Actuarial Parameter Correction and Recalculation Service (SR 11-7).

Applies validated client parameter corrections to assessment payloads,
preserving original estimates, updating effective values, tagging provenance,
and executing deterministic portfolio recalculation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from assessment_engine.application.services.canonical_risk_orchestrator import (
    CanonicalRiskOrchestrator,
)
from assessment_engine.domain.bayesian_fair_copula_engine import (
    PortfolioReproductionManifest,
)
from assessment_engine.domain.models.parameter_lineage import (
    ActuarialParameterCorrection,
)

logger = logging.getLogger(__name__)


class ActuarialCorrectionService:
    """Production service for applying client corrections and triggering recalculation."""

    @classmethod
    def apply_parameter_correction(
        cls,
        payloads_by_tower: Dict[str, Dict[str, Any]],
        correction: ActuarialParameterCorrection,
        target_finding_id: str,
        global_context: Optional[Dict[str, Any]] = None,
        client_id: Optional[str] = None,
        persist_to_disk: bool = False,
    ) -> Tuple[Dict[str, Dict[str, Any]], Optional[PortfolioReproductionManifest]]:
        """Applies correction to finding's raw input & lineage, then recalculates the portfolio."""
        param_name = correction.parameter_name
        corr_val = correction.corrected_effective_value

        finding_found = False
        target_tower_code = None

        for t_code, payload in payloads_by_tower.items():
            for pillar in payload.get("pillars_analysis", []):
                for hc in pillar.get("health_check_asis", []):
                    if str(hc.get("node_id")) == target_finding_id:
                        finding_found = True
                        target_tower_code = t_code

                        # Update raw field in finding
                        if param_name == "cmmi_maturity":
                            hc["cmmi_maturity"] = float(corr_val)
                        elif param_name == "hourly_burn_rate":
                            hc["hourly_burn_rate"] = float(corr_val)
                        elif param_name == "secondary_loss_mean":
                            hc["secondary_loss_mean"] = float(corr_val)
                        elif param_name == "direct_replacement_cost":
                            hc["direct_replacement_cost"] = float(corr_val)
                        elif param_name == "blast_radius_alpha":
                            hc["blast_radius_alpha"] = float(corr_val)
                        elif param_name == "is_spof":
                            hc["is_spof"] = bool(corr_val)
                        elif param_name == "rto_hours_mode":
                            hc["rto_hours_mode"] = float(corr_val)
                            hc["recovery_time_hours"] = float(corr_val)
                        elif param_name == "tef_pert_mode":
                            hc["tef_pert_mode"] = float(corr_val)
                            hc["threat_event_frequency"] = float(corr_val)
                        elif param_name.startswith("tef_pert_"):
                            hc[param_name] = float(corr_val)
                        elif param_name.startswith("rto_hours_"):
                            hc[param_name] = float(corr_val)

                        # Record explicit audit trail metadata
                        hc["last_correction_audit"] = {
                            "parameter_name": param_name,
                            "original_estimated_value": correction.original_estimated_value,
                            "corrected_effective_value": corr_val,
                            "source": correction.user_provided_source,
                            "review_identifier": correction.review_identifier,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        break
                if finding_found:
                    break
            if finding_found:
                break

        if not finding_found:
            raise KeyError(
                f"Actuarial Correction Error: Target finding '{target_finding_id}' not found in provided payloads."
            )

        logger.info(
            "Applied correction on parameter '%s' for finding '%s' in tower '%s'. Recalculating portfolio...",
            param_name,
            target_finding_id,
            target_tower_code,
        )

        # Trigger canonical portfolio recalculation with verified inputs
        recalculated_payloads, manifest = CanonicalRiskOrchestrator.quantify_payloads(
            payloads_by_tower=payloads_by_tower,
            global_context=global_context,
            persist_to_disk=persist_to_disk,
            client_id=client_id,
        )

        return recalculated_payloads, manifest
