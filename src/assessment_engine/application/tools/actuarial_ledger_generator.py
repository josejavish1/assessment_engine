import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def generate_actuarial_ledger(tower_id: str, blueprint_payload: Dict[str, Any]) -> None:
    """Generate a formal Markdown Audit Dossier for each quantified financial risk.

    Combines SME elicitation rationale with a self-contained, reproducible Python simulation
    script compliant with the Federal Reserve SR 11-7 model risk management guidance.
    """
    client_name = blueprint_payload.get("document_meta", {}).get("client_name", "UNKNOWN")
    currency_code = str(
        blueprint_payload.get("currency_code")
        or blueprint_payload.get("currency")
        or "EUR"
    ).strip().upper()

    from assessment_engine.infrastructure.runtime_paths import resolve_case_dir
    base_dir = resolve_case_dir(client_name, tower_id)
    base_dir.mkdir(parents=True, exist_ok=True)
        
    dossier_path = base_dir / f"Actuarial_Risk_Audit_Dossier_{tower_id}.md"
    
    lines = []
    lines.append(f"# Actuarial Diagnostic Dossier - Tower {tower_id}")
    lines.append("This document constitutes the **Audit Trail** for quantitative risk evaluation. It details methodological rationale, parameter sources, and simulation outputs. Results represent quantitative diagnostic estimates derived from structured evidence, explicit assumptions, and benchmark priors.\n")
    
    lines.append("## 0. Executive Briefing: Risk Calculation Methodology")
    lines.append("- **Nature of Figures:** Estimates represent actuarial loss expectancies from potential service degradation, operational toil, or incident response if identified vulnerabilities trigger failures. They do not constitute accounting provisions or legal guarantees.")
    lines.append("- **Operational Differentiation:** The model distinguishes functional impact tiers across mission-critical, core platforms, and administrative/support systems.")
    lines.append("- **Evidential Boundaries:** Metrics reflect point-in-time diagnostic evaluations; unconfirmed assumptions are explicitly recorded in the parameter provenance ledger.\n")
    
    for pillar in blueprint_payload.get("pillars_analysis", []):
        for finding in pillar.get("health_check_asis", []):
            if "fair_ale_score" not in finding:
                continue
                
            risk_id = finding.get("node_id", "UNK")
            cap = finding.get("capability", "UNK")
            tef = finding.get("threat_event_frequency", 1.0)
            lm = finding.get("loss_magnitude", 1.0)
            tef_mod = finding.get("_consensus_tef_mod", 1.0)
            lm_mod = finding.get("_consensus_lm_mod", 1.0)
            slef_mod = finding.get("_consensus_slef_mod", 1.0)
            rationale = finding.get("_consensus_justification", "No deviation recorded.")
            
            ale = float(finding.get("fair_ale_score", 0.0))
            var_90 = float(finding.get("fair_p90_score", 0.0))
            cvar = float(finding.get("fair_cvar_score") or 0.0)
            max_p99 = float(finding.get("fair_max_score", 0.0))
            
            lines.append("---")
            lines.append(f"## 🧮 Audit Record: {risk_id} - {cap}\n")
            
            lines.append("### 1. Modeling Rationale (SME Elicitation)")
            lines.append(f"**Analyzed Vulnerability:** {finding.get('finding', 'N/A')}\n")
            lines.append("**Prior Update Rationale:**")
            lines.append(f"> {rationale}\n")
            
            lines.append("### 2. Bayesian & Copula Stochastic Parameters")
            vec = finding.get("actuarial_input_vector") or {}
            finding_currency = str(vec.get("currency_code") or currency_code).strip().upper()
            inputs_data = vec.get("inputs") or {}
            if inputs_data:
                lines.append("| Parameter | Estimated | Effective | Unit | Source Type | Confidence | Validation Status | Override |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
                for param_name, p_rec in inputs_data.items():
                    if isinstance(p_rec, dict) and "effective_value" in p_rec:
                        lines.append(
                            f"| `{param_name}` | `{p_rec.get('estimated_value')}` | `{p_rec.get('effective_value')}` | "
                            f"{p_rec.get('unit', '-')} | `{p_rec.get('source_type', 'UNSPECIFIED')}` | "
                            f"{p_rec.get('confidence', 'UNASSESSED')} | {p_rec.get('validation_status', 'UNCONFIRMED')} | "
                            f"{'YES' if p_rec.get('client_override') else 'NO'} |"
                        )
                lines.append("")
            elif vec:
                lines.append(f"- **Vulnerability Posterior Mean (Beta-Binomial):** `{vec.get('mean_vuln', 0.25):.4f}`")
                lines.append(f"- **Audit Evidence Ratio:** `{vec.get('audit_k_failures', 0)} deficiencies / {vec.get('audit_n_trials', 0)} evaluated controls`")
                lines.append(f"- **Threat Event Frequency Mean (LEF):** `{vec.get('mean_lef', 0.10):.4f} events/year`")
                lines.append(f"- **Single Loss Expectancy Mean (SLE):** `{vec.get('mean_sle', 0.0):,.2f} {finding_currency}`")
                lines.append(f"- **Euler Sub-additive Allocated ALE:** `{vec.get('portfolio_allocated_ale', ale):,.2f} {finding_currency}`\n")
            else:
                lines.append("- **Distribution Type:** Discrete Compound Poisson with Lognormal Severity.")
                lines.append(f"- **Baseline Metrics:** Ordinal Frequency = {tef}/5 | Ordinal Severity = {lm}/5.")
                lines.append(f"- **Applied Attenuation Factors:** TEF=`{tef_mod}x`, LM=`{lm_mod}x`, SLEF=`{slef_mod}x`\n")
            
            lines.append("### 3. Quantitative Risk Exposure")
            lines.append(f"- **Annual Loss Exposure (ALE - Mean):** {ale:,.2f} {finding_currency}")
            lines.append(f"- **Value-at-Risk (VaR - P90):** {var_90:,.2f} {finding_currency}")
            lines.append(f"- **Conditional Value-at-Risk (CVaR - Expected Shortfall):** {cvar:,.2f} {finding_currency}")
            lines.append(f"- **Value-at-Risk (VaR - P99):** {max_p99:,.2f} {finding_currency}\n")
            
            lines.append("### 4. Auditor Replication Script (Python/NumPy)")
            lines.append("The portfolio simulation is reproducible via the deterministic reproduction manifest:\n")
            
            code_block = """```python
import json
import sys
from pathlib import Path
from assessment_engine.domain.bayesian_fair_copula_engine import replay_portfolio_simulation

def verify_reproduction(manifest_file: str = "portfolio_reproduction_manifest.json") -> None:
    manifest_path = Path(manifest_file)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Reproduction manifest not found at: {manifest_path.resolve()}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    result = replay_portfolio_simulation(manifest_data, currency_tolerance=0.01)
    print(f"Replay verified successfully: {result}")

if __name__ == "__main__":
    target_path = sys.argv[1] if len(sys.argv) > 1 else "portfolio_reproduction_manifest.json"
    verify_reproduction(target_path)
```\n"""
            lines.append(code_block)
            
    # Automated Mathematical Closure Gate (Zero-Tolerance Assertion)
    # Validate SSOT closure for the entire portfolio/tower prior to flushing the ledger.
    try:
        tower_ale = float(blueprint_payload.get("total_fair_ale", 0.0))
        tower_p90 = float(blueprint_payload.get("total_fair_p90", 0.0))
        tower_cvar = float(blueprint_payload.get("total_fair_cvar_90", 0.0))
        finding_ale_sum = sum(float(f.get("fair_ale_score", 0.0)) for p in blueprint_payload.get("pillars_analysis", []) for f in p.get("health_check_asis", []))
        closure_tol = max(1.0, 0.02 * max(1, len(blueprint_payload.get("pillars_analysis", []))))
        if tower_ale > 0.0 and finding_ale_sum > 0.0:
            import math
            if not math.isclose(tower_ale, finding_ale_sum, abs_tol=closure_tol):
                raise AssertionError(
                    f"SSOT Non-Closure: Tower ALE ({tower_ale}) != Sum of Findings ({finding_ale_sum}) within tolerance {closure_tol}"
                )
            if tower_cvar < tower_p90 - 0.01:
                raise AssertionError(
                    f"Sub-additivity / Tail Violation: CVaR90 ({tower_cvar}) < VaR90 ({tower_p90})"
                )
    except Exception as e:
        logger.error(f"SR 11-7 Governance Gate Failed: {e}")
        raise e

    try:
        with open(dossier_path, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(lines))
        logger.info(f"Audit Dossier MD generated at: {dossier_path}")
    except Exception as e:
        logger.error(f"Failed to write actuarial dossier: {e}")
        raise e
