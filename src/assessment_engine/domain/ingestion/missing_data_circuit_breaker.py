"""
Missing Data Circuit Breaker.

Enforces non-silent missing/invalid data detection for assessment survey answers.
Disallows silent imputation of default values, explicitly marking absent or corrupt
KPI responses as MISSING_OR_INVALID to preserve mathematical and epistemic integrity.
"""

from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class MissingDataCircuitBreaker:
    """Detects and isolates missing, corrupt, or unparsed KPI responses."""

    @staticmethod
    def inspect_and_filter_kpi_responses(
        tower_id: str,
        expected_kpis: List[Dict[str, Any]],
        parsed_scores: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Validates all expected KPIs from the tower definition against parsed responses.

        If a KPI was not answered, has an empty value, or has an invalid/corrupt string
        (such as a stray comma or non-numeric token), it explicitly tags it as
        MISSING_OR_INVALID with value=None, prohibiting downstream silent imputation.
        """
        inspected_answers = []
        for kpi in expected_kpis:
            qid = f"{kpi['kpi_id']}.PR1"
            raw_val = parsed_scores.get(qid)

            if raw_val is not None and isinstance(raw_val, (int, float)) and 1.0 <= float(raw_val) <= 5.0:
                val = float(raw_val)
                evidence_status = "VALIDATED"
                validation_state = "Exploratoria"
            else:
                val = None
                evidence_status = "MISSING_OR_INVALID"
                validation_state = "NO_EVIDENCIADO"
                logger.warning(
                    "[MissingDataCircuitBreaker] KPI %s (%s) has no valid 1-5 score in responses for tower %s. "
                    "Explicitly logging MISSING_OR_INVALID without silent imputation.",
                    qid,
                    kpi.get("kpi_name", ""),
                    tower_id,
                )

            inspected_answers.append(
                {
                    "question_id": qid,
                    "pillar_id": kpi["pillar_id"],
                    "pillar_name": kpi.get("pillar_name", ""),
                    "kpi_id": kpi["kpi_id"],
                    "kpi_name": kpi.get("kpi_name", ""),
                    "value": val,
                    "evidence_status": evidence_status,
                    "validation_state": validation_state,
                }
            )

        return inspected_answers
