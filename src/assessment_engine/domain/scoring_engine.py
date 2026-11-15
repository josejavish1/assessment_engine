"""
100% Deterministic Scoring Engine.
Eliminates LLM stochasticity from maturity score calculation.
Enforces Master Matrix weights and rigorous CMMI scale bounding.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any

from assessment_engine.domain.governance.scale_engine import GovernanceScaleEngine

class ScoringEngine:
    @staticmethod
    def compute_pillar_score(kpi_scores: List[float]) -> Decimal:
        """Computes the unweighted maturity score for a single pillar from its constituent KPIs.
        Follows standard mean, but ignores None/missing values explicitly.
        """
        valid_scores = [Decimal(str(s)) for s in kpi_scores if s is not None and s > 0]
        if not valid_scores:
            return Decimal("0.00")
        
        avg = sum(valid_scores) / Decimal(len(valid_scores))
        return avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def compute_tower_score(pillar_scores: List[Decimal], pillar_weights: List[Decimal]) -> Decimal:
        """Computes the dot-product global tower score using exact official weights."""
        if len(pillar_scores) != len(pillar_weights):
            raise ValueError("Pillar scores and weights count must match exactly.")
        
        # Verify weights sum to 100% (or 1.0)
        total_weight = sum(pillar_weights)
        if not (Decimal("0.99") <= total_weight <= Decimal("1.01") or Decimal("99") <= total_weight <= Decimal("101")):
             raise ValueError(f"Pillar weights must sum to 1.0 or 100. Got {total_weight}")

        # Normalize weights to fractions of 1.0 if they are percentages
        if total_weight > 1.05:
            normalized_weights = [w / Decimal("100.0") for w in pillar_weights]
        else:
            normalized_weights = pillar_weights

        dot_product = sum(s * w for s, w in zip(pillar_scores, normalized_weights))
        return dot_product.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def generate_audit_trail(tower_id: str, kpi_ledger: Dict[str, float], pillar_defs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates a complete deterministic audit trail of the scoring math."""
        scale_engine = GovernanceScaleEngine()
        
        audit_trail = {
            "tower_id": tower_id,
            "pillars": [],
            "global": {}
        }

        p_scores = []
        p_weights = []

        for p_def in pillar_defs:
            p_id = p_def["pillar_id"]
            weight = Decimal(str(p_def.get("weight_pct", 20.0)))
            p_weights.append(weight)

            kpi_ids = [kpi["kpi_id"] for kpi in p_def.get("kpis", [])]
            k_scores = [kpi_ledger.get(kid) for kid in kpi_ids]
            
            # Missing data imputation policy: if no valid kpis, default to 0.00 to flag missing data.
            pillar_score = ScoringEngine.compute_pillar_score(k_scores)
            p_scores.append(pillar_score)

            band = scale_engine.resolve_maturity(float(pillar_score))

            audit_trail["pillars"].append({
                "pillar_id": p_id,
                "pillar_name": p_def.get("pillar_name"),
                "raw_kpi_scores": {kid: kpi_ledger.get(kid) for kid in kpi_ids},
                "computed_score": float(pillar_score),
                "weight_pct": float(weight),
                "maturity_band": band.label
            })

        tower_score = ScoringEngine.compute_tower_score(p_scores, p_weights)
        global_band = scale_engine.resolve_maturity(float(tower_score))

        audit_trail["global"] = {
            "computed_tower_score": float(tower_score),
            "maturity_band": global_band.label,
            "maturity_level": global_band.level
        }

        return audit_trail
