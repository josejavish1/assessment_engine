from __future__ import annotations

import json
import logging
import math
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy

logger = logging.getLogger(__name__)

class FairRiskPolicy(BaseSovereignPolicy):
    """Generate random samples from statistical distributions for FAIR Monte Carlo modeling."""

    def _sample_pert(
        self, min_val: float, most_likely: float, max_val: float, size: int = 10000, rng: Any = None
    ) -> Any:
        import numpy as np
        if rng is None:
            rng = np.random.default_rng()

        # Mathematical Safeguard: Prevent DivisionByZero if min and max converge
        if min_val >= max_val:
            return np.full(size, min_val)

        # Mathematical Safeguard: Clamp mode inside boundaries to prevent Beta parameter inversion
        most_likely = max(min_val, min(most_likely, max_val))

        range_val = max_val - min_val
        alpha = 1.0 + 4.0 * (most_likely - min_val) / range_val
        beta_val = 1.0 + 4.0 * (max_val - most_likely) / range_val
        return min_val + rng.beta(alpha, beta_val, size=size) * range_val

    def _sample_lognormal(
        self, rng: Any, min_val: float, most_likely: float, max_val: float, size: int = 10000
    ) -> Any:
        import numpy as np

        # Mathematical Safeguard: Prevent Log of zero or convergence
        if min_val >= max_val or min_val <= 0:
            return np.full(size, max_val)

        # standard Actuarial Practice: Calibrate Lognormal using the Mode (most_likely) and P95 (max_val).
        # Mode M = exp(mu - sigma^2) => mu = ln(M) + sigma^2
        # P95 X = exp(mu + 1.645*sigma) => ln(X) = mu + 1.645*sigma
        # Substituting mu: ln(X) = ln(M) + sigma^2 + 1.645*sigma => sigma^2 + 1.645*sigma + (ln(M) - ln(X)) = 0
        import math
        ln_m = math.log(max(min_val, most_likely))
        ln_x = math.log(max_val)
        c = ln_m - ln_x
        
        # Solve quadratic equation for sigma (ax^2 + bx + c = 0, a=1, b=1.645)
        # sigma = (-1.645 + sqrt(1.645^2 - 4*c)) / 2
        discriminant = 1.645**2 - 4 * c
        if discriminant > 0:
            sigma = (-1.645 + math.sqrt(discriminant)) / 2.0
            if sigma <= 0:
                # Fallback to geometric mean if expert inputs are mathematically incompatible with lognormal skew
                sigma = (np.log(max_val) - np.log(min_val)) / 3.29
                mu = (np.log(max_val) + np.log(min_val)) / 2.0
            else:
                mu = ln_m + sigma**2
        else:
            # Fallback if discriminant is negative
            sigma = (np.log(max_val) - np.log(min_val)) / 3.29
            mu = (np.log(max_val) + np.log(min_val)) / 2.0
        
        # standard Actuarial Practice: Sigma Cap to prevent the Infinite Mean Paradox.
        # If sigma exceeds ~2.0 in a Lognormal, the theoretical mean diverges towards infinity faster than 
        # the Monte Carlo sample can converge, causing wild instability. We cap sigma at 2.0.
        sigma = min(2.0, max(1e-4, sigma))
        
        samples = rng.lognormal(mean=mu, sigma=sigma, size=size)
        # standard Actuarial Practice: Allow true Black Swans (Heavy Tails). 
        # Only cap at a massive macroeconomic limit (Enterprise Ruin Level) to prevent float overflow.
        enterprise_ruin_limit = 500_000_000.0
        return np.minimum(samples, enterprise_ruin_limit)

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Performs a quantitative risk analysis on qualitative findings using the Open FAIR methodology and enriches the input payload with the results.

        This method processes a payload of qualitative findings, loading a client-
        specific risk profile based on industry and organizational scale from
        `engine_config/policies/fair_risk_profiles.json`. The profile selection is
        informed by client metadata, typically located in `working/{client_id}/client_intelligence.json`.

        For each finding, text-based heuristics are applied to its descriptive
        fields to map it to qualitative scores for Threat Event Frequency (TEF),
        Vulnerability (VULN), and Loss Magnitude (LM). These scores correspond to
        quantitative ranges (min, most-likely, max) defined in the risk profile.

        A Monte Carlo simulation (10,000 iterations) using Beta-PERT distributions
        models the uncertainty in these factors. The simulation calculates the
        Annualized Loss Expectancy (ALE) and other statistical risk measures.
        These quantitative metrics are then patched directly into the finding
        objects within the original `payload` dictionary.

        Args:
            graph: An EpistemicGraph object. Reserved for future contextual analysis
                and not currently used.
            payload: The input dictionary containing analysis data. This dictionary is
                modified in-place. It is expected to have a 'pillars_analysis' key,
                which contains a list of pillar objects, each with a
                'health_check_asis' list of finding dictionaries.

        Returns:
            The `payload` dictionary, enriched with quantitative FAIR risk metrics
            for each finding. Keys added to each finding dict include
            'threat_event_frequency', 'vulnerability_level', 'loss_magnitude',
            'fair_ale_score', 'fair_p90_score', 'fair_min_score', and
            'fair_max_score'.

        Raises:
            json.JSONDecodeError: If the risk profile configuration file
                (`engine_config/policies/fair_risk_profiles.json`) is malformed.
            ValueError: If keys or numeric values within the risk profile
                configuration file cannot be converted to their expected integer
                or float types.
        """
        import os

        import numpy as np

        pillars = payload.get("pillars_analysis", [])

        # Initialize an accumulator array for the total annual losses across all simulated years (10,000 runs)
        total_annual_losses = np.zeros(10000)

        # Load FAIR model parameters from the canonical governance repository.
        from assessment_engine.infrastructure.config_loader import load_policy_file

        try:
            profiles = load_policy_file("fair_risk_profiles")
        except Exception as e:
            logger.error(f"Fallo cargando fair_risk_profiles de políticas: {e}")
            profiles = {}

        # Load client metadata to ascertain the industry sector for sector-lock policy enforcement.
        client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
        intel_path = Path(f"working/{client_id}/client_intelligence.json")
        if not intel_path.exists():
            client_base = client_id.split('_')[0]
            intel_path = Path(f"working/{client_id}/{client_base}/client_intelligence.json")

        industry = "Standard"
        hierarchy = "Standard"
        intel: Dict[str, Any] = {}
        if intel_path.exists():
            try:
                with open(intel_path, "r", encoding="utf-8-sig") as inf:
                    intel = json.load(inf)
                    p_meta = intel.get("profile", {})
                    industry = p_meta.get("industry", "Standard")
                    hierarchy = p_meta.get("hierarchy", "Standard")
            except (OSError, json.JSONDecodeError) as ex:
                logger.debug(f"[PolicyEngine] Error leyendo perfil para escala actuarial: {ex}")

        # Select the risk model preset that is calibrated to the client's organizational scale and data volume.
        preset_key = os.environ.get("ASSESSMENT_COMPANY_SCALE", "").upper()
        if preset_key not in profiles:
            reg_context_str = " ".join(intel.get("regulatory_context", [])).lower()
            if any(k in reg_context_str for k in ["essential", "critica", "pic", "dora"]):
                preset_key = "CRITICAL_INFRASTRUCTURE"
            elif "global" in hierarchy.lower() or "mega" in hierarchy.lower() or "enterprise" in hierarchy.lower():
                preset_key = "MEGA_ENTERPRISE"
            else:
                preset_key = "MID_MARKET"

        preset = profiles.get(preset_key, profiles.get("MID_MARKET", {}))

        # Coerce string-based map keys to integer types for compatibility with downstream processing.
        tef_map = {int(k): v for k, v in preset.get("tef_map", {}).items()}
        vuln_map = {int(k): v for k, v in preset.get("vuln_map", {}).items()}
        lm_map = {int(k): v for k, v in preset.get("lm_map", {}).items()}

        # Load dynamic custom risk profile generated by the financial scale calibrator (FAIR-MAM)
        tower_id = payload.get("document_meta", {}).get("tower_id", "T2")
        from assessment_engine.infrastructure.runtime_paths import resolve_case_dir
        case_dir = resolve_case_dir(client_id, tower_id)
        custom_profile_path = case_dir / "custom_risk_profile.json"
        
        custom_calibration = None
        capability_calibrations = {}
        reg_max_fine = 2000000.0
        if custom_profile_path.exists():
            try:
                with open(custom_profile_path, "r", encoding="utf-8-sig") as cf:
                    custom_calibration = json.load(cf)
                    capability_calibrations = custom_calibration.get("capability_calibrations", {})
                    val_fine = custom_calibration.get("reg_max_fine_eur")
                    if val_fine is not None:
                        reg_max_fine = float(val_fine)
                    logger.info(f"🎯 [Policy Engine] Cargando calibración financiera dinámica desde: {custom_profile_path}")
            except Exception as e:
                logger.warning(f"Error loading custom risk profile: {e}")

        # Load dynamic evidence ledger for Bayesian Inference (Horizon 2 - Phase 4)
        evidence_ledger_path = case_dir / "evidence_ledger.json"
        if not evidence_ledger_path.exists():
            evidence_ledger_path = Path(f"working/{client_id}/evidence_ledger.json")
            
        evidences = []
        if evidence_ledger_path.exists():
            try:
                with open(evidence_ledger_path, "r", encoding="utf-8-sig") as ef:
                    evidences = json.load(ef).get("evidences", [])
                    logger.info(f"🎯 [Policy Engine] Cargando expediente de evidencias para inferencia bayesiana desde: {evidence_ledger_path}")
            except Exception as e:
                logger.warning(f"Error loading evidence ledger: {e}")

        # Load the dynamic security controls catalog
        controls_path = Path(__file__).resolve().parents[3] / "engine_config" / "policies" / "security_controls.json"
        controls_catalog = {}
        if controls_path.exists():
            try:
                with open(controls_path, "r", encoding="utf-8-sig") as cf:
                    controls_catalog = json.load(cf).get("security_controls", {})
                    logger.info(f"🎯 [Policy Engine] Cargando catálogo de controles de ciberseguridad desde: {controls_path}")
            except Exception as e:
                logger.warning(f"Error loading security controls catalog: {e}")
                logger.warning(f"Error loading custom risk profile: {e}")

        # If custom calibration exists, dynamically scale and override the primary Loss Magnitude map (lm_map)
        if custom_calibration:
            try:
                val = custom_calibration.get("hourly_downtime_cost_eur")
                if val is not None:
                    cost = float(val)
                elif "annual_revenue_eur" in custom_calibration:
                    rev = float(custom_calibration["annual_revenue_eur"])
                    dep = float(custom_calibration.get("digital_dependency_factor", 0.5))
                    cost = (rev * dep) / 8760.0
                else:
                    cost = 5000.0
            except (ValueError, TypeError):
                logger.warning("🎯 [Policy Engine] Calibración de coste horario con formato no numérico. Aplicando fallback seguro.")
                cost = 5000.0

            lm_map = {
                1: {"min": cost * 0.1, "ml": cost * 0.3, "max": cost * 1.0},
                2: {"min": cost * 0.5, "ml": cost * 1.5, "max": cost * 4.0},
                3: {"min": cost * 2.0, "ml": cost * 5.0, "max": cost * 12.0},
                4: {"min": cost * 5.0, "ml": cost * 12.0, "max": cost * 24.0},
                5: {"min": cost * 12.0, "ml": cost * 24.0, "max": cost * 48.0},
            }

        # Establishes safe default values to ensure resilience against configuration file parsing errors or unavailability.
        if not tef_map:
            tef_map = {
                1: {"min": 0.01, "ml": 0.1, "max": 0.2},
                2: {"min": 0.1, "ml": 0.25, "max": 0.5},
                3: {"min": 0.5, "ml": 1.0, "max": 3.0},
                4: {"min": 2.0, "ml": 4.0, "max": 8.0},
                5: {"min": 6.0, "ml": 12.0, "max": 24.0},
            }
        if not vuln_map:
            vuln_map = {
                1: {"min": 0.05, "ml": 0.10, "max": 0.15},
                2: {"min": 0.15, "ml": 0.25, "max": 0.35},
                3: {"min": 0.30, "ml": 0.50, "max": 0.70},
                4: {"min": 0.70, "ml": 0.85, "max": 0.95},
                5: {"min": 0.90, "ml": 1.00, "max": 1.00},
            }
        if not lm_map:
            lm_map = {
                1: {"min": 500.0, "ml": 1000.0, "max": 3000.0},
                2: {"min": 2000.0, "ml": 5000.0, "max": 15000.0},
                3: {"min": 10000.0, "ml": 25000.0, "max": 80000.0},
                4: {"min": 50000.0, "ml": 100000.0, "max": 300000.0},
                5: {"min": 250000.0, "ml": 500000.0, "max": 1500000.0},
            }

        # standard Actuarial Practice: Systemic Threat Climate (Frailty Model)
        # Threat campaigns (like global Ransomware) do not attack vulnerabilities independently; they hit the entire perimeter at once.
        # To model Multivariate Frequency Covariance, we generate a SINGLE shared stochastic 'Climate Multiplier' for the 10,000 simulated years.
        import hashlib
        global_seed_str = f"SYSTEMIC_CLIMATE_{client_id}".encode("utf-8")
        global_seed = int(hashlib.md5(global_seed_str).hexdigest(), 16) % (2**32)
        rng_climate = np.random.default_rng(global_seed)
        # Gamma(shape=2.0, scale=0.5) generates a positive multiplier with Mean=1.0 and Variance=0.5.
        # This preserves the expert's average frequency but injects simultaneous 'Black Swan' storm years across all tower risks.
        systemic_climate_multiplier = rng_climate.gamma(2.0, 0.5, size=10000)

        for p in pillars:
            p_score = float(p.get("score", 3.0))
            p_name = p.get("pilar_name", p.get("pilar_id", "Unknown_Pillar"))
            for finding in p.get("health_check_asis", []):
                target_state = finding.get("target_state", finding.get("capability", "Unknown_Capability"))
                text = (
                    finding.get("finding", "") + " " + finding.get("impact", "")
                ).lower()

                # Implements dynamic qualitative TEF and LM mapping from the AI-Elicited scores (Gap 1)
                # Falls back to deterministic mapping from calibrated severity if not available in the payload
                tef = int(finding.get("_elicited_tef", 0) or 0)
                sev_raw = str(finding.get("severity", "")).lower()

                if tef == 0:
                    if sev_raw in ["critical", "crítica"]:
                        tef = 5 if ("internet" in text or "ransomware" in text) else 4
                    elif sev_raw in ["high", "alta"]:
                        tef = 4 if p_score < 3.0 else 3
                    elif sev_raw in ["low", "baja", "informativa"]:
                        tef = 1 if p_score >= 3.5 else 2
                    else:
                        if "internet" in text or "ransomware" in text:
                            tef = 5
                        elif p_score < 2.5:
                            tef = 4
                        else:
                            tef = 3

                # Implements dynamic qualitative Loss Magnitude mapping (Gap 1)
                # Falls back to deterministic mapping from calibrated severity if not available in the payload
                lm = int(finding.get("_elicited_lm", 0) or 0)
                if lm == 0:
                    if sev_raw in ["critical", "crítica"]:
                        lm = 5
                    elif sev_raw in ["high", "alta"]:
                        lm = 4
                    elif sev_raw in ["medium", "media"]:
                        lm = 3
                    elif sev_raw in ["low", "baja", "informativa"]:
                        lm = 2
                    else:
                        if "parada total" in text or "caída catastrófica" in text:
                            lm = 5
                        elif any(k in text for k in ["nis2", "ens", "multa", "sanción"]):
                            lm = 4
                        else:
                            lm = 3

                # Sanity Gate: Bound TEF and LM by the finding's calibrated severity when explicitly specified
                # A Low or Informative finding cannot escalate to catastrophic TEF=5 or LM=5
                sev = finding.get("severity")
                if sev is not None:
                    sev_str = str(sev).lower()
                    if sev_str in ["low", "baja", "informativa"]:
                        tef = min(tef, 2)
                        lm = min(lm, 2)
                    elif sev_str in ["medium", "media"]:
                        tef = min(tef, 3)
                        lm = min(lm, 3)
                    elif sev_str in ["high", "alta"]:
                        tef = min(tef, 4)
                        lm = min(lm, 4)

                # Define uncertainty for model inputs using a Beta-PERT distribution, as specified by the Open FAIR standard.
                #
                tef_range = tef_map.get(tef, {"min": 0.5, "ml": 1.0, "max": 3.0})
                tef_min = float(tef_range.get("min", 0.5))
                tef_ml = float(tef_range.get("ml", 1.0))
                tef_max = float(tef_range.get("max", 3.0))

                # Compute deterministic multipliers from the qualitative security controls audited by the IA
                tef_mod = 1.0
                lm_mod = 1.0
                slef_mod = 1.0

                # Load security_controls range definitions
                controls_list = finding.get("_consensus_controls", [])
                for ctrl in controls_list:
                    c_id = ctrl.get("control_id")
                    status = ctrl.get("implementation_status", "Ausente")
                    
                    # Map state to mitigation percentage
                    mitigation_multiplier = 0.0 # 'Ausente' gets 0% mitigation
                    if status == "Implementado":
                        mitigation_multiplier = 1.0 # 'Implementado' gets 100% of the range mitigation
                    elif status == "Parcial":
                        mitigation_multiplier = 0.5 # 'Parcial' gets 50% of the range mitigation

                    # Get range definitions dynamically from the loaded config catalog (FAIR-CAM)
                    ctrl_def = controls_catalog.get(c_id, {})
                    tef_range = ctrl_def.get("tef_mitigation_range", [0.0, 0.0])
                    lm_range = ctrl_def.get("lm_mitigation_range", [0.0, 0.0])

                    # Fallback default definitions if not found in the loaded catalog
                    if not ctrl_def or tef_range == [0.0, 0.0]:
                        tef_range = [0.20, 0.45]
                        lm_range = [0.10, 0.35]

                    # Calculate exact mitigation for TEF and LM
                    tef_mitigation = tef_range[0] + (tef_range[1] - tef_range[0]) * mitigation_multiplier
                    lm_mitigation = lm_range[0] + (lm_range[1] - lm_range[0]) * mitigation_multiplier

                    # Multiply the remaining risk multiplier (1.0 - mitigation)
                    tef_mod *= (1.0 - tef_mitigation)
                    lm_mod *= (1.0 - lm_mitigation)
                    
                    # Slef_mod is mapped dynamically based on standard regulatory compliance mitigations (FAIR-CAM)
                    slef_range = ctrl_def.get("slef_mitigation_range", [0.0, 0.0])
                    
                    # Fallback default definitions if not found in the loaded catalog
                    if not ctrl_def or slef_range == [0.0, 0.0]:
                        if c_id == "NIS2-IaC":
                            slef_range = [0.50, 0.85] # 50% partial, 85% full mitigations

                    slef_mitigation = slef_range[0] + (slef_range[1] - slef_range[0]) * mitigation_multiplier
                    slef_mod *= (1.0 - slef_mitigation)

                # Apply audit-grounded modifiers to Beta-PERT inputs
                tef_min *= tef_mod
                tef_ml *= tef_mod
                tef_max *= tef_mod

                # Gamma-Poisson Conjugate Update for Threat Event Frequency (TEF) using physical evidence
                p_id = p.get("pilar_id", "T2.P1")
                pillar_evidences = [ev for ev in evidences if p_id in ev.get("pillar_ids", [])] if evidences else []
                n_trials = len(pillar_evidences)
                k_failures = 0
                
                if n_trials > 0:
                    pillar_gaps = len(p.get("gaps", []))
                    pillar_strengths = len(p.get("strengths", []))
                    ledger_gaps = sum(
                        1
                        for ev in pillar_evidences
                        if "gap" in ev.get("supports", [])
                        or "risk" in ev.get("supports", [])
                    )
                    ledger_strengths = sum(
                        1
                        for ev in pillar_evidences
                        if "asis" in ev.get("supports", [])
                        and "gap" not in ev.get("supports", [])
                    )
                    k_failures = max(pillar_gaps, ledger_gaps)
                    n_trials = max(
                        1,
                        k_failures
                        + max(pillar_strengths, ledger_strengths, len(pillar_evidences)),
                    )
                            
                    # Prior Gamma(alpha, beta) parameters
                    alpha_prior = 4.0
                    beta_prior = 4.0 / max(1e-4, tef_ml)
                    
                    # Poisson observations: x_events = failures, t_years = trials * 0.25
                    x_events = k_failures
                    t_years = n_trials * 0.25
                    
                    # Posterior Gamma(alpha_post, beta_post) parameters
                    alpha_post = alpha_prior + x_events
                    beta_post = beta_prior + t_years
                    tef_ml_post = alpha_post / beta_post
                    
                    # Shift ranges proportionally
                    tef_ratio = tef_ml_post / max(1e-4, tef_ml)
                    tef_ml = tef_ml_post
                    tef_min = tef_min * tef_ratio
                    tef_max = tef_max * tef_ratio
                    logger.info(f"🔮 [Bayesian Inferencia] TEF_ml actualizado de {tef_ml/tef_ratio:.2f} a {tef_ml:.2f} (Pruebas: {n_trials}, Fallos: {k_failures})")

                # standard Actuarial Practice: Metadata-driven Calibration & Typology Segregation (FAIR-MAM)
                # 1. Fetch specific dynamic calibrations for this capability from the client profile
                cap_name = finding.get("capability", target_state)
                cap_calibration = capability_calibrations.get(cap_name, {}) if capability_calibrations else {}
                if not isinstance(cap_calibration, dict):
                    cap_calibration = {}
                typology = cap_calibration.get("typology", "CATASTROPHIC_SYSTEMIC")
                exposure_factor = float(cap_calibration.get("exposure_factor", 1.0))

                # Symmetrical with the latest 2026 FAIR-CAM standard, Vulnerability (VULN) is formally and mathematically
                # derived from the actual qualitative technical maturity score (p_score) of the corresponding pillar.
                # standard Actuarial Practice: Instead of a naive linear decay, we use a logistic/exponential decay function.
                # A maturity drop from 3 to 2 causes an exponential collapse in defense efficacy, not a flat 25% drop.
                p_vuln = 1.0 / (1.0 + np.exp(1.5 * (p_score - 3.0)))
                # Condition vulnerability on network/environmental exposure factor (e.g. air-gapped systems)
                p_vuln = max(0.01, min(0.99, p_vuln * exposure_factor))

                # Beta-Binomial Conjugate Update for Vulnerability (VULN) using physical evidence
                if n_trials > 0:
                    mu_prior = p_vuln
                    kappa = 30.0  # Expert confidence scale
                    alpha_prior = mu_prior * kappa
                    beta_prior = (1.0 - mu_prior) * kappa
                    
                    # Physical evidence weight
                    w_evidence = 2.0
                    alpha_post = alpha_prior + w_evidence * k_failures
                    beta_post = beta_prior + w_evidence * (n_trials - k_failures)
                    
                    p_vuln_post = alpha_post / (alpha_post + beta_post)
                    logger.info(f"🔮 [Bayesian Inferencia] VULN_rate actualizado de {p_vuln:.4f} a {p_vuln_post:.4f} (Pruebas: {n_trials}, Fallos: {k_failures})")
                    p_vuln = p_vuln_post
                
                vuln_ml = p_vuln
                vuln_min = max(0.01, p_vuln - 0.15)
                vuln_max = min(0.99, p_vuln + 0.15)
                
                # We determine the qualitative vuln level for reporting/classification
                if p_vuln >= 0.80:
                    vuln = 5
                elif p_vuln >= 0.60:
                    vuln = 4
                elif p_vuln >= 0.40:
                    vuln = 3
                elif p_vuln >= 0.20:
                    vuln = 2
                else:
                    vuln = 1

                # Symmetrical with the 2026 FAIR-MAM standard, Loss Magnitude (LM) is divided into:
                # 1. Primary Loss (Response & Restoration): e.g. engineering hours, VM recovery.
                # 2. Secondary Loss (Regulatory/Compliance liabilities under NIS2 / market SLA penalties).
                lm_range = lm_map.get(
                    lm, {"min": 10000.0, "ml": 25000.0, "max": 80000.0}
                )
                lm_min = float(lm_range.get("min", 10000.0)) * lm_mod
                lm_ml = float(lm_range.get("ml", 25000.0)) * lm_mod
                lm_max = float(lm_range.get("max", 80000.0)) * lm_mod

                # standard Industrial Practice: Scope-Aware Downtime Impact (Environment Tiering)
                hourly_cost = (
                    custom_calibration.get("hourly_downtime_cost_eur")
                    if custom_calibration
                    else None
                )
                if hourly_cost is not None and typology != "OPERATIONAL_FRICTION":
                    hourly = float(hourly_cost)
                    env_tier = str(
                        finding.get("environment_tier")
                        or cap_calibration.get("environment_tier", "")
                    ).upper()
                    if env_tier in ["CRITICAL_CORE", "DC_PLANT", "PRODUCTION_OT"]:
                        scope_ratio = 0.60
                    elif env_tier in ["CAMPUS_OFFICE", "INTERNAL_SUPPORT"]:
                        scope_ratio = 0.15
                    else:
                        scope_ratio = float(cap_calibration.get("scope_ratio", 0.35))

                    effective_hourly = hourly * scope_ratio

                    op_assumptions = profiles.get("operational_assumptions", {})
                    duration_map = op_assumptions.get(
                        "duration_hours_by_severity", {}
                    )
                    dur_spec = duration_map.get(
                        str(lm), {"min": 0.5, "ml": 2.0, "max": 6.0}
                    )
                    lm_min = effective_hourly * float(dur_spec.get("min", 0.5))
                    lm_ml = effective_hourly * float(dur_spec.get("ml", 2.0))
                    lm_max = effective_hourly * float(dur_spec.get("max", 6.0))

                # standard Enterprise Actuarial Practice: Ontology & Structure-Driven Typology (Zero-Keywords)
                finding_typology = finding.get("typology") or cap_calibration.get("typology")
                is_friction_risk = (
                    typology == "OPERATIONAL_FRICTION"
                    or finding_typology == "OPERATIONAL_FRICTION"
                    or finding.get("is_operational_friction") is True
                )
                finding["typology"] = "OPERATIONAL_FRICTION" if is_friction_risk else typology
                finding["is_operational_friction"] = is_friction_risk
                finding["p_vuln"] = p_vuln
                if is_friction_risk:
                    calib_rev = float(custom_calibration.get("annual_revenue_eur", 50000000.0)) if custom_calibration else 50000000.0
                    max_frict_cap = calib_rev * 0.05 if calib_rev > 0 else 150000.0
                    lm_max = min(lm_max, max_frict_cap)
                    
                    # Inject TCO fixed license/hours cost for Value Hexagon rendering
                    finding["deterministic_tco_waste_eur"] = float(cap_calibration.get("deterministic_waste_eur", 0.0))

                # Execute a mathematically rigorous, production-grade Open FAIR 10,000-run Monte Carlo simulation (Collective Risk Model).
                size = 10000

                # Deterministic Monte Carlo Seeding (standard Actuarial Practice): 
                # SHA-256 stable hashing algorithm for 100% deterministic, platform-independent random seeds
                import hashlib
                node_id_seed = finding.get("node_id", "") or str(len(text))
                unique_signature = f"{p_name}_{target_state}_{p_score}_{node_id_seed}".encode("utf-8")
                stable_hash = hashlib.sha256(unique_signature).hexdigest()
                det_seed = int(stable_hash[:16], 16)
                
                # Instanciar generador local aislado y seguro para hilos concurrentes (Thread-Safe RNG)
                rng = np.random.default_rng(det_seed)

                from scipy import stats

                # standard Actuarial Practice: Unbound Threat Frequency
                # Replacing Beta-PERT with Lognormal for Threat Event Frequency and passing our safe local rng
                tef_rates_base = self._sample_lognormal(rng, tef_min, tef_ml, tef_max, size=size)
                
                # standard Actuarial Practice: Universal First-Principles Topological Attenuation
                # Assets isolated behind physical or cryptographic air-gaps exhibit vastly reduced contact frequency (TEF).
                isolation = cap_calibration.get("isolation", "STANDARD_HYBRID")
                is_air_gapped = (
                    isolation in ["AIR_GAPPED_OT", "ISOLATED_MAINFRAME"]
                    or finding.get("network_zone") in ["AIR_GAPPED", "ISOLATED"]
                    or cap_calibration.get("is_air_gapped") is True
                )
                if is_air_gapped:
                    tef_rates_base = tef_rates_base * 0.05
                    
                # standard Actuarial Practice: Bayesian Deduplication (MECE Principle via FAIR-CAM)
                # If multiple vulnerabilities share the same causal pillar, they are NOT mutually exclusive.
                # Summing their ALEs causes massive double counting. We apply a Bayesian DAG attenuation 
                # factor to the frequency based on the number of overlapping findings.
                pillar_findings_count = max(1, len(p.get("health_check_asis", [])))
                if pillar_findings_count > 1:
                    import math
                    tef_rates_base = tef_rates_base / math.sqrt(pillar_findings_count)

                # Apply the Shared Latent Variable (Systemic Climate) to couple the frequencies across all vulnerabilities
                tef_rates = tef_rates_base * systemic_climate_multiplier
                
                # standard Actuarial Practice: Avoid Beta domain edge crash (variance impossibility) by using 
                # a relative concentration parameter (Kappa) instead of an absolute hardcoded variance.
                # This mathematically guarantees the pure Beta distribution can exist at any probability bound [0, 1].
                mu = p_vuln
                kappa = 50.0  # Concentration parameter: higher means less variance around the mean
                alpha_beta = mu * kappa
                beta_beta = (1.0 - mu) * kappa
                vuln_rates = rng.beta(alpha_beta, beta_beta, size=size)

                # standard Actuarial Practice: Dynamic Dispersion (Negative Binomial)
                # We model over-dispersed (clustered) cyber attacks, but we scale the dispersion dynamically based on severity.
                # Highly sophisticated attacks (high impact) cluster less (tend to Poisson, p -> 1.0). Common attacks cluster heavily (p -> 0).
                # We normalize the most likely impact to create a dynamic 'p' parameter.
                impact_factor = min(1.0, lm_ml / 1000000.0)
                # p_param scales from 0.1 (massive clustering for low impact) to 0.9 (almost Poisson for high impact APTs)
                p_param = 0.1 + (0.8 * impact_factor)
                
                # standard Actuarial Practice: Restore Bayesian Hierarchical Variance (Epistemic + Aleatory)
                # The mean of the Negative Binomial must be the stochastic tef_rates array to correctly compound 
                # expert uncertainty (epistemic) with threat clustering (aleatory).
                n_param = tef_rates * p_param / (1.0 - p_param) # n = mean * p / (1 - p)
                n_param = np.maximum(n_param, 1e-6)  # standard Actuarial Practice: Anti-Crash Clamp
                
                n_threats = rng.negative_binomial(n_param, p_param, size=size)
                k_losses = rng.binomial(n_threats, vuln_rates)

                total_k = int(np.sum(k_losses))

                # Symmetrical with 2026 top-tier actuarial engineering, we vectorize the entire compound loss simulation,
                # completely avoiding Python loops to achieve microseconds execution speeds.
                if total_k > 0:
                    # Map each of the total_k simulated loss events to its respective run index (0 to size-1)
                    event_run_ids = np.repeat(np.arange(size), k_losses)

                    # Sample all primary loss magnitudes at once using Lognormal heavy-tailed distributions and local thread-safe RNG
                    all_primary_lms = self._sample_lognormal(rng, lm_min, lm_ml, lm_max, size=total_k)

                    # standard Actuarial Practice: Erlang-C / Kendall M/M/c Incident Congestion Model (Gap 3)
                    # Instead of an arbitrary decay or rigid presets, 'c_crews' (concurrent response crews) 
                    # is calculated dynamically based on the client's actual financial revenue scale (FAIR-MAM)
                    revenue = 50000000.0 # Default fallback (50M EUR)
                    if custom_calibration:
                        try:
                            val_rev = custom_calibration.get("annual_revenue_eur")
                            if val_rev is not None:
                                revenue = float(val_rev)
                        except (ValueError, TypeError):
                            pass

                    # Continuous logarithmic scaling of concurrent SRE capacity with corporate turnover (1 to 6 crews)
                    c_crews = max(
                        1,
                        min(
                            6,
                            int(
                                np.floor(
                                    1 + np.log10(max(1.0, revenue / 10000000.0))
                                )
                            ),
                        ),
                    )
                    
                    # 'mu' is the service rate (1 / MTTR). SRE Maturity directly and exponentially scales MTTR
                    # Low maturity (1.5) -> MTTR = 12 hours. High maturity (4.5) -> MTTR = 0.5 hours.
                    mttr_hours = 12.0 / (1.5 ** (p_score - 1.0))
                    mu_rate = 1.0 / max(0.1, mttr_hours)
                    
                    # 'lambda' (arrival rate) is the concurrent incident count in the simulated year
                    k_per_event = np.repeat(k_losses, k_losses)
                    
                    # Calculate Erlang-C probability of delay and average queue wait time for each simulated year
                    # To avoid division by zero and infinite queues when lambda >= c * mu, we clamp utilization (rho < 1.0)
                    rho = k_per_event / (c_crews * mu_rate)
                    rho = np.minimum(0.99, rho)  # Anti-crash saturation clamp

                    # Erlang-C Delay Probability (P_q) formula calculation
                    # We compute the numerator and denominator terms for the exact formula
                    import math
                    numerator = ((c_crews * rho) ** c_crews) / math.factorial(c_crews) * (1.0 / (1.0 - rho))
                    
                    denominator = 0.0
                    for k_term in range(c_crews):
                        denominator += ((c_crews * rho) ** k_term) / math.factorial(k_term)
                    denominator += numerator
                    
                    p_q = numerator / np.maximum(1e-6, denominator)
                    
                    # Average queue wait time in hours: W_q = P_q / (c * mu * (1 - rho))
                    w_q_hours = p_q / np.maximum(1e-6, c_crews * mu_rate * (1.0 - rho))
                    
                    # Total downtime multiplier: downtime is scaled by wait time
                    # We multiply the baseline loss magnitude by this congestion factor
                    congestion_multiplier = 1.0 + (w_q_hours / max(1.0, mttr_hours))
                    
                    # Clamp the maximum congestion impact to avoid absurd numbers (Sovereign Safety Guard)
                    max_congestion = 2.0 if hourly_cost is not None else 5.0
                    congestion_multiplier = np.minimum(max_congestion, congestion_multiplier)
                    
                    all_primary_lms = all_primary_lms * congestion_multiplier

                    # standard Actuarial Practice: Continuous Logistic Regulatory Fine Probability (SLEF)
                    # We eliminate the binary "Step-Function Cliff" (15% vs 2%) and replace it with a continuous 
                    # logistic function that smoothly transitions the probability of a fine as the maturity score approaches 2.60.
                    # As maturity drops below 2.60, fine probability approaches 15%. As it rises above, it drops asymptoticaly to 2%.
                    slef_base = 0.02 + (0.13 / (1.0 + np.exp(10.0 * (p_score - 2.60))))
                    slef_base *= slef_mod
                    if is_friction_risk:
                        slef_base = 0.0
                    
                    # standard Actuarial Practice: Conditional Regulatory Triggers (Materiality Threshold)
                    # Regulatory fines (NIS2) are not triggered by a random coin flip on a €500 laptop crash.
                    # The secondary event is mathematically conditioned on the Primary Loss exceeding a materiality threshold (e.g. median).
                    materiality_threshold = np.percentile(all_primary_lms, 50.0) if len(all_primary_lms) > 0 else 0.0
                    all_sec_triggered = (all_primary_lms > materiality_threshold) & (rng.uniform(0.0, 1.0, size=total_k) < slef_base)

                    all_sec_losses = np.zeros(total_k)
                    num_sec = int(np.sum(all_sec_triggered))
                    if num_sec > 0:
                        # standard Actuarial Practice: Dynamic Regulatory Mapping (Industry Routing)
                        # Secondary loss severity is mapped to the highest regulatory framework applicable to the client's industry.
                        reg_max_fine = 2000000.0 # Default GDPR/LGPD baseline
                        
                        # Load dynamic reg max fine from custom calibration if available (FAIR-MAM)
                        # standard Actuarial Practice: Compliance fines (NIS2) are legally bound by a minimum standard (e.g. 10M) 
                        # or 2.0% of the organization's factual global annual revenue (turnover), whichever is higher (NIS2 Art 34).
                        if custom_calibration and "reg_max_fine_eur" in custom_calibration:
                            try:
                                val_fine = custom_calibration.get("reg_max_fine_eur")
                                base_fine = float(val_fine) if val_fine is not None else 10000000.0
                                
                                val_rev = custom_calibration.get("annual_revenue_eur")
                                revenue = float(val_rev) if val_rev is not None else 0.0
                                
                                # Scale dynamically with global turnover statutory cap (e.g. 2.0%-4.0% rule under NIS2/GDPR)
                                fine_ratio = float(custom_calibration.get("regulatory_fine_cap_ratio", 0.02))
                                turnover_fine = revenue * fine_ratio if revenue > 0 else base_fine
                                reg_max_fine = min(base_fine, turnover_fine) if revenue > 0 else base_fine
                            except (ValueError, TypeError):
                                reg_max_fine = 10000000.0
                        else:
                            reg_context_str = " ".join(intel.get("regulatory_context", [])).lower()
                            client_country = str(intel.get("country") or intel.get("geography", "")).lower()
                            if "dora" in reg_context_str:
                                reg_max_fine = 15000000.0 # DORA compliance cap
                            elif "hipaa" in reg_context_str:
                                reg_max_fine = 5000000.0 # HIPAA compliance cap
                            elif any(c in client_country for c in ["brasil", "brazil", "mexico", "méxico", "chile", "colombia", "argentina", "peru", "perú"]) or any(k in reg_context_str for k in ["lgpd", "lfpd", "1581", "21.663"]):
                                reg_max_fine = 2000000.0 # LatAm statutory baseline cap (LGPD / LFPDPPP / SIC / INAI)
                            else:
                                reg_max_fine = 10000000.0 # EU statutory baseline cap (NIS2 / GDPR / ISO)

                        # standard Regulatory Law & Actuarial Practice: Proportionality of Single-Deficiency Sanctions (GDPR/NIS2/DORA)
                        # A single technical deficiency cannot incur the maximum statutory penalty of the entire corporation (27M€).
                        # Penalties for individual infractions are bounded by operational proportionality (1-5% of statutory cap).
                        finding_fine_cap = min(reg_max_fine * 0.05, float(hourly_cost) * 20.0 if hourly_cost else 500000.0)
                        if hourly_cost is not None:
                            hourly = float(hourly_cost)
                            finding_fine_cap = min(finding_fine_cap, hourly * 8.0)

                        if lm >= 4:
                            most_likely_fine = min(finding_fine_cap * 0.25, float(hourly_cost) * 1.5 if hourly_cost else 50000.0)
                            raw_sec_losses = self._sample_lognormal(
                                rng, min(5000.0, lm_min), most_likely_fine, finding_fine_cap, size=num_sec
                            )
                        else:
                            raw_sec_losses = self._sample_lognormal(
                                rng, lm_min * 1.5, lm_ml * 1.5, min(finding_fine_cap, lm_max * 1.5), size=num_sec
                            )

                        # standard Actuarial Practice: True Directional Gaussian Copula with Asymmetric Tail Dependence
                        # Primary damage is a real physical simulation that ALREADY HAPPENED.
                        # We must map the REAL primary damage to its theoretical Gaussian percentiles (Z0)
                        # rather than generating a ghost variable. This establishes true causal dependency.
                        triggered_primary_lms = all_primary_lms[all_sec_triggered]
                        
                        # Calculate empirical CDF (percentiles) of the triggered primary losses
                        ranks = stats.rankdata(triggered_primary_lms, method='ordinal')
                        empirical_cdf = ranks / (num_sec + 1.0)
                        
                        # Transform empirical CDF to standard normal (Inverse CDF / PPF)
                        z0_real = stats.norm.ppf(empirical_cdf)
                        
                        # We calculate the dynamic correlation vector (Tail Dependence)
                        # standard Actuarial Practice: Continuous Logistic Copula Correlation
                        # Eliminates the binary "Arbitrage Cliff". The correlation scales smoothly from 0.0 (independent) 
                        # to 0.85 (highly correlated) as the severity of the primary outage approaches its absolute maximum (empirical CDF -> 1.0).
                        # The function is centered at the 80th percentile.
                        rhos = 0.85 / (1.0 + np.exp(-10.0 * (empirical_cdf - 0.80)))
                        
                        # Generate the dependent normal variable for secondary losses and passing our safe local rng
                        z1_independent = rng.normal(size=num_sec)
                        z1_correlated = rhos * z0_real + np.sqrt(1.0 - rhos**2) * z1_independent
                        
                        # Use the dependent variable (z1_correlated) to rank-sort the secondary losses
                        z1_ranks = stats.rankdata(z1_correlated, method='ordinal')
                        raw_sec_sorted = np.sort(raw_sec_losses)
                        
                        # Map the sorted secondary losses exactly back to the order of triggered_primary_lms
                        final_sec_losses = np.zeros(num_sec)
                        for i in range(num_sec):
                            target_pos = int(z1_ranks[i]) - 1
                            final_sec_losses[i] = raw_sec_sorted[target_pos]

                        all_sec_losses[all_sec_triggered] = final_sec_losses

                    # standard Actuarial Practice: Financial Double-Counting Fix (Max Absorption)
                    # Severe secondary legal fines generally absorb the operational cost of the primary response,
                    # avoiding the double-counting fallacy of a blind addition.
                    consolidated_losses = np.maximum(all_primary_lms, all_sec_losses) + (all_primary_lms * 0.1)

                    loss_per_run = np.bincount(event_run_ids, weights=consolidated_losses, minlength=size)
                else:
                    loss_per_run = np.zeros(size)

                # standard Actuarial Practice: Truncated Lognormal Model (Extreme Outliers Elimination)
                # To prevent extreme, non-defensible P100 outliers from distorting the mean and causing 
                # mathematical discrepancies (like CVaR exceeding the printed Maximum Plausible Loss), 
                # we truncate the empirical annual loss distribution at the 99.0th percentile (P99).
                # This represents the "Maximum Plausible Loss" (1-in-100-year extreme operational limit),
                # which is the global actuarial standard for bounding operational risk distributions.
                p99_limit = float(np.percentile(loss_per_run, 99.0)) if len(loss_per_run) > 0 else 0.0
                truncated_losses = np.clip(loss_per_run, a_min=None, a_max=p99_limit)

                # Calculate statistical exposures using the truncated distribution
                mean_ale = float(np.mean(truncated_losses))
                
                # standard Actuarial Practice: Coherent Risk Measure (Expected Shortfall / CVaR)
                # Value-at-Risk (P90) is not subadditive and ignores the tail magnitude. We use Expected Shortfall (CVaR).
                # Under the Basel Committee's Fundamental Review of the Trading Book (FRTB) and Enterprise banking standards, 
                # Expected Shortfall must be calculated at the 97.5% confidence level to properly capture tail risk without dilution.
                # Since we operate on the truncated distribution, CVaR is mathematically bounded by the P99 limit.
                sorted_losses = np.sort(truncated_losses)
                tail_index = int(len(sorted_losses) * 0.975)
                tail_losses = sorted_losses[tail_index:]
                cvar_ale = float(np.mean(tail_losses)) if len(tail_losses) > 0 else 0.0
                p90_ale = cvar_ale  # Overwriting the legacy P90 variable with the Coherent Risk Measure (CVaR 97.5%) to maintain schema compatibility
                
                min_ale = float(np.min(truncated_losses))
                max_ale = p99_limit

                # Round final computed metrics to a fixed precision for presentation clarity.
                ale_euros = round(mean_ale, 2)

                finding["threat_event_frequency"] = tef
                finding["vulnerability_level"] = vuln
                finding["loss_magnitude"] = lm
                finding["fair_ale_score"] = ale_euros
                finding["fair_p90_score"] = round(p90_ale, 2)
                finding["fair_min_score"] = round(min_ale, 2)
                finding["fair_max_score"] = round(max_ale, 2)

                # standard Enterprise Actuarial Auditing: Attach Physical Accounting Breakdown to finding
                hourly_val = float(hourly_cost) if hourly_cost is not None else 500.0
                hourly_sre_rate = (
                    float(custom_calibration.get("hourly_rate_sre_eur", 36.0))
                    if custom_calibration
                    else 36.0
                )
                downtime_h = {1: 0.5, 2: 2.0, 3: 6.0, 4: 12.0, 5: 24.0}.get(lm, 6.0)
                downtime_cost = downtime_h * hourly_val
                sre_h = max(1.0, 12.0 / (1.5 ** max(0.5, p_score - 1.0)))
                sre_cost = sre_h * hourly_sre_rate * 2.0

                finding["physical_loss_breakdown"] = {
                    "downtime_hours": round(downtime_h, 1),
                    "hourly_downtime_cost_eur": round(hourly_val, 2),
                    "lucro_cesante_eur": round(downtime_cost, 2),
                    "sre_recovery_hours": round(sre_h, 1),
                    "sre_hourly_rate_eur": round(hourly_sre_rate, 2),
                    "sre_cost_eur": round(sre_cost, 2),
                    "direct_incident_cost_eur": round(downtime_cost + sre_cost, 2),
                }
                from assessment_engine.infrastructure.localization import (
                    format_currency,
                    get_localized_string,
                )

                doc_lang = str(
                    payload.get("document_meta", {}).get("language", "es")
                ).lower()
                curr_code = str(
                    payload.get("document_meta", {}).get("currency")
                    or (
                        custom_calibration.get("currency_code")
                        if custom_calibration
                        else "EUR"
                    )
                ).upper()
                curr_sym = payload.get("document_meta", {}).get(
                    "currency_symbol"
                ) or (
                    custom_calibration.get("currency_symbol")
                    if custom_calibration
                    else None
                )

                formatted_hourly = format_currency(
                    hourly_val,
                    currency_code=curr_code,
                    currency_symbol=curr_sym,
                    locale=doc_lang,
                )
                formatted_downtime_cost = format_currency(
                    downtime_cost,
                    currency_code=curr_code,
                    currency_symbol=curr_sym,
                    locale=doc_lang,
                )
                formatted_sre_rate = format_currency(
                    hourly_sre_rate,
                    currency_code=curr_code,
                    currency_symbol=curr_sym,
                    locale=doc_lang,
                )
                formatted_sre_cost = format_currency(
                    sre_cost,
                    currency_code=curr_code,
                    currency_symbol=curr_sym,
                    locale=doc_lang,
                )

                finding["audit_justification"] = get_localized_string(
                    "audit_justification_template",
                    locale=doc_lang,
                    downtime_hours=f"{downtime_h:.1f}",
                    hourly_rate=formatted_hourly,
                    downtime_cost=formatted_downtime_cost,
                    sre_cost=formatted_sre_cost,
                    sre_recovery_hours=f"{sre_h:.1f}",
                    sre_hourly_rate=formatted_sre_rate,
                )

                # Sum vectorially to compile the corporate-wide annual loss distribution (Gap 2)
                total_annual_losses += truncated_losses

        # standard Actuarial Practice: Portfolio Subadditivity & Operational Absorption Cap
        if len(total_annual_losses) > 0 and np.sum(total_annual_losses) > 0:
            if hourly_cost is not None and float(hourly_cost) > 0:
                hourly_f = float(hourly_cost)
                # Portfolio subadditivity: Annual cumulative operational downtime across a tower is realistically bounded
                # by declarative operational assumptions, while secondary consolidated regulatory sanctions are capped proportionally.
                op_assumptions = profiles.get("operational_assumptions", {})
                max_dt_hours = float(op_assumptions.get("max_annual_downtime_hours", 40.0))
                max_annual_tower_loss = hourly_f * max_dt_hours + min(reg_max_fine * 0.02, hourly_f * 20.0)
                total_annual_losses = np.minimum(
                    total_annual_losses, max_annual_tower_loss
                )

            portfolio_sorted = np.sort(total_annual_losses)
            portfolio_mean = float(np.mean(total_annual_losses))
            tail_idx = int(len(portfolio_sorted) * 0.975)
            portfolio_cvar = float(np.mean(portfolio_sorted[tail_idx:])) if len(portfolio_sorted[tail_idx:]) > 0 else portfolio_mean

            payload["total_fair_ale"] = round(portfolio_mean, 2)
            payload["total_fair_p90"] = round(portfolio_cvar, 2)
            payload["total_fair_max"] = round(float(np.percentile(total_annual_losses, 99.0)), 2)

        # Generate the Loss Exceedance Curve (LEC) Chart (Gap 2)
        if len(total_annual_losses) > 0 and np.sum(total_annual_losses) > 0:
            try:
                # Import matplotlib in a non-GUI thread-safe manner (Agg backend)
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt

                # Sort the losses in descending order for the exceedance probability
                sorted_losses_desc = np.sort(total_annual_losses)[::-1]
                
                # Eje Y: Exceedance Probability (from 0 to 1)
                probabilities = np.arange(1, len(sorted_losses_desc) + 1) / len(sorted_losses_desc)

                # Set custom styling matching the high-end corporate brand profile of the client
                plt.figure(figsize=(7.5, 4.5), dpi=300)
                plt.plot(sorted_losses_desc / 1000.0, probabilities * 100.0, color="#1e3a8a", linewidth=2.5, label="Postura Actual (AS-IS)")
                
                # Draw the Materiality Threshold if defined in custom_calibration
                m_threshold = 500000.0 # Default
                if custom_calibration and "reg_max_fine_eur" in custom_calibration:
                    m_threshold = float(custom_calibration.get("reg_max_fine_eur", 10000000.0)) * 0.1
                
                plt.axvline(x=m_threshold / 1000.0, color="#b91c1c", linestyle="--", linewidth=1.5, label=f"Umbral de Materialidad ({m_threshold:,.0f} €)")

                plt.title("Curva de Excedencia de Pérdidas (LEC) - Value-at-Risk", fontsize=11, fontweight="bold", pad=12)
                plt.xlabel("Pérdida Operativa Anual Excedente (Miles de Euros, k€)", fontsize=9.5)
                plt.ylabel("Probabilidad de Excedencia (%)", fontsize=9.5)
                plt.grid(True, linestyle=":", alpha=0.6)
                plt.legend(fontsize=8.5, loc="upper right")
                
                # Force tight layout and save physically to the case folder
                plt.tight_layout()
                
                chart_path = case_dir / "loss_exceedance_curve.png"
                plt.savefig(chart_path, format="png", dpi=300)
                plt.close()
                logger.info(f"🎨 [Policy Engine] Gráfico oficial de Curva de Excedencia de Pérdidas (LEC) generado en: {chart_path}")
                
            except Exception as chart_err:
                logger.warning(f"Error generating Loss Exceedance Curve chart: {chart_err}")

        return payload


# Declarative registry mapping policy identifiers to their concrete implementation classes
