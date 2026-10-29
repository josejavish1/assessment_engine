import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
from pydantic import BaseModel, Field
import os
from google import genai

logger = logging.getLogger(__name__)

class ControlEfficacyAssessment(BaseModel):
    """Encapsulates the qualitative technical audit of a specific security control."""
    control_id: str = Field(
        description="The exact ID of the security control evaluated, e.g., 'NIS2-IaC', 'ISO27001-Observabilidad', or 'CIS-Automatizacion'."
    )
    implementation_status: str = Field(
        description="The factual status of the control based on client evidence. Strict options: 'Implementado' (full mitigation), 'Parcial' (partial mitigation), or 'Ausente' (zero mitigation)."
    )
    evidence_grounding: str = Field(
        description="SME Elicitation Rationale (SR 11-7 compliant) justifying this specific status based on the raw client evidence, files, or interview answers."
    )

class ConsensusAdjustment(BaseModel):
    """The structured result of the adversarial consensus debate, mapping audit to security controls."""
    controls_assessed: List[ControlEfficacyAssessment] = Field(
        default_factory=list,
        description="List of security controls assessed during the adversarial consensus debate."
    )
    justification: str = Field(
        description="Unified technical validation justification (SME Rationale) explaining the cumulative risk mitigation under SR 11-7 standard."
    )

class AdversarialConsensusEngine:
    """
    Asynchronous engine that orchestrates debates between an ultra-skeptical CFO 
    and a Tier-1 Actuary to factually audit the implementation status of 
    cibersecurity controls based on client evidence, compliant with the 2026 FAIR-CAM standard.
    """
    def __init__(self, ai_client=None, env=None):
        from assessment_engine.infrastructure.genai_client import (
            ModelTier,
            get_model,
        )

        self.client = genai.Client()
        self.model_name = get_model(ModelTier.REASONING)
        self.env = env
        self.max_iterations = 4  # 4 structured rounds of debate

        # Load the dynamic security controls catalog
        policies_dir = Path(__file__).resolve().parents[4] / "engine_config" / "policies"
        controls_path = policies_dir / "security_controls.json"
        self.controls_catalog = {}
        if controls_path.exists():
            try:
                with open(controls_path, "r", encoding="utf-8-sig") as cf:
                    self.controls_catalog = json.load(cf).get("security_controls", {})
            except Exception as e:
                logger.warning(f"Error loading security controls catalog: {cf}: {e}")

    async def _generate_text_with_retry(self, prompt: str):
        """Executes LLM API calls with exponential backoff to robustly prevent rate limits (429)."""
        retries = 5
        base_delay = 5.0
        import random
        for attempt in range(retries):
            try:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.client.models.generate_content(model=self.model_name, contents=prompt).text
                )
                return response
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                logger.warning(f"Adversarial API error: {e}. Retrying in {delay:.2f}s... ({attempt+1}/{retries})")
                await asyncio.sleep(delay)

    async def _generate_pydantic_with_retry(self, prompt: str, schema):
        retries = 5
        base_delay = 5.0
        import random
        for attempt in range(retries):
            try:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.model_name, 
                        contents=prompt,
                        config=genai.types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=schema,
                            temperature=0.1
                        )
                    ).text
                )
                return schema.model_validate_json(response)
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                logger.warning(f"Adversarial Pydantic API error: {e}. Retrying in {delay:.2f}s... ({attempt+1}/{retries})")
                await asyncio.sleep(delay)

    async def process_payload(self, tower_id: str, findings_payload: Dict[str, Any], client_name: Optional[str] = None) -> Dict[str, Any]:
        """Iterates through all critical findings and subjects them to adversarial consensus."""
        if not client_name:
            client_name = findings_payload.get("document_meta", {}).get("client_name")
        if not client_name:
            client_name = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")

        from assessment_engine.infrastructure.runtime_paths import resolve_case_dir
        case_dir = resolve_case_dir(client_name, tower_id)
        case_dir.mkdir(parents=True, exist_ok=True)
        transcript_file = case_dir / "adversarial_consensus_transcript.log"
        
        # Open in write mode to clear previous runs
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(f"=== TRANSCRITO DE CONSENSO ADVERSARIAL GROUNDED (TORRE {tower_id}) ===\n\n")

        # Load the raw findings.json to extract the qualitative elicited FAIR scores (Gap 1)
        findings_path = case_dir / "findings.json"
        elicited_scores_map = {}
        if findings_path.exists():
            try:
                with open(findings_path, "r", encoding="utf-8-sig") as ff:
                    raw_f = json.load(ff)
                    for pf in raw_f.get("pillar_findings", []):
                        p_id = pf.get("pillar_id")
                        # Find the first risk's elicited scores
                        for r in pf.get("risks", []):
                            elicited_scores_map[p_id] = {
                                "tef": r.get("_elicited_tef", 3),
                                "lm": r.get("_elicited_lm", 3)
                            }
                            break
            except Exception as e:
                logger.warning(f"Error loading elicited scores from findings: {e}")

        pillars = findings_payload.get("pillars_analysis", [])
        
        # Collect async tasks
        tasks = []
        for p_idx, pillar in enumerate(pillars):
            p_id = pillar.get("pilar_id")
            for h_idx, finding in enumerate(pillar.get("health_check_asis", [])):
                # Inject the dynamic elicited scores in the health_check_asis object in-place (Gap 1)
                scores = elicited_scores_map.get(p_id, {"tef": 3, "lm": 3})
                finding["_elicited_tef"] = scores["tef"]
                finding["_elicited_lm"] = scores["lm"]
                
                tasks.append(self._debate_finding(tower_id, finding, transcript_file, p_idx, h_idx))
                    
        # Execute debates concurrently
        if tasks:
            logger.info(f"🥊 Launching {len(tasks)} parallel adversarial control debates for {tower_id}...")
            results = await asyncio.gather(*tasks)
            
            # Map the evaluated controls back to the payload
            for result in results:
                if result:
                    p_idx, h_idx, adjustment = result
                    finding = pillars[p_idx]["health_check_asis"][h_idx]
                    
                    controls_list = []
                    for ctrl in adjustment.controls_assessed:
                        controls_list.append({
                            "control_id": ctrl.control_id,
                            "implementation_status": ctrl.implementation_status,
                            "evidence_grounding": ctrl.evidence_grounding
                        })
                    finding["_consensus_controls"] = controls_list
                    finding["_consensus_justification"] = adjustment.justification

        return findings_payload

    async def _debate_finding(self, tower_id: str, finding: Dict[str, Any], transcript_file: Path, p_idx: int, h_idx: int) -> tuple:
        finding_text = finding.get("finding", "")
        cap = finding.get("capability", "")
        
        if not finding_text:
            return None
            
        context_str = f"Capability: {cap}\nIdentified Vulnerability / Technical Debt: {finding_text}\nBaseline FAIR Severity: {finding.get('loss_magnitude')} / 5"
        
        # Build controls catalog string to inject as context
        catalog_str = "AVAILABLE CYBERSECURITY AND RESILIENCE CONTROLS CATALOG:\n"
        for c_id, c_data in self.controls_catalog.items():
            catalog_str += f"- {c_id}: {c_data['name']}. {c_data['description']}\n  Mitigation Ranges: Frequency (TEF) {c_data['tef_mitigation_range']}, Severity (LM) {c_data['lm_mitigation_range']}\n"

        history = f"AUDIT CONTEXT:\n{context_str}\n\n{catalog_str}\n\n"
        
        cfo_prompt_base = f"""
        Act as the Chief Financial Officer (CFO) and Chief Risk Officer of an enterprise critical infrastructure organization.
        You are debating whether technical vulnerabilities are mitigated by compensating controls within the catalog.
        Your objective is to skeptically challenge risk severity, establishing that operational runbooks, tactical automation,
        virtualization guardrails, or existing compensating controls measurably compress threat frequency and loss magnitude.
        Advocate for qualifying mitigations as 'Implemented' or 'Partial' based strictly on empirical evidence.
        Be rigorous, pragmatic, and direct in a single analytical paragraph.
        """
        
        actuary_prompt_base = f"""
        Act as a Principal Quantitative Risk Actuary specializing in Open FAIR-CAM and Basel III stress testing.
        You are debating a skeptical enterprise CFO. Your mandate is defending actuarial rigor, admitting mitigation credit
        only when conclusively substantiated by verifiable telemetry and operational evidence. If controls are nascent,
        uncoordinated, or absent, firmly qualify them as 'Absent' or 'Partial' to protect tail risk (CVaR/P99).
        Be mathematically rigorous, sober, and concise in a single analytical paragraph.
        """
        
        try:
            # Iteration 1: CFO adversarial critique
            history += "--- ROUND 1: CFO CHALLENGE ---\n"
            cfo_prompt = cfo_prompt_base + "\n" + history + "\nFormulate your initial challenge:"
            cfo_resp1 = await self._generate_text_with_retry(cfo_prompt)
            history += f"👔 CFO: {cfo_resp1}\n\n"
            
            # Iteration 2: Actuary statistical defense
            history += "--- ROUND 2: ACTUARY DEFENSE ---\n"
            act_prompt = actuary_prompt_base + "\n" + history + "\nState your defense based on the absence of robust operational controls:"
            act_resp1 = await self._generate_text_with_retry(act_prompt)
            history += f"🧮 ACTUARY: {act_resp1}\n\n"
            
            # Iteration 3: CFO fiscal counter-attack
            history += "--- ROUND 3: CFO COUNTER-ARGUMENT ---\n"
            cfo_prompt2 = cfo_prompt_base + "\n" + history + "\nRespond to the Actuary, defending local compensating controls and operational workarounds:"
            cfo_resp2 = await self._generate_text_with_retry(cfo_prompt2)
            history += f"👔 CFO: {cfo_resp2}\n\n"
            
            # Iteration 4: Actuary consensus synthesis
            history += "--- ROUND 4: FINAL ACTUARY SYNTHESIS ---\n"
            act_prompt2 = actuary_prompt_base + "\n" + history + "\nRespond to the CFO, converging on the empirical state of the control (Implemented/Partial/Absent):"
            act_resp2 = await self._generate_text_with_retry(act_prompt2)
            history += f"🧮 ACTUARY: {act_resp2}\n\n"
            
            # Iteration 5: Consensus extraction to Pydantic
            history += "--- ROUND 5: SR 11-7 RATIONALE EXTRACTION (FAIR-CAM GROUNDING) ---\n"
            final_prompt = f"""
            Based on the 4-round adversarial debate, classify the implementation maturity of each relevant control from the catalog for this vulnerability, substantiated under model risk governance standard SR 11-7.
            
            CRITICAL EXTRACTION MANDATES:
            1. Only evaluate controls strictly present in the provided catalog.
            2. The 'implementation_status' field only accepts three exact string options: 'Implemented', 'Partial', or 'Absent'.
            3. In the justification rationale ('evidence_grounding' and 'justification'), it is strictly forbidden to mention terms like 'AI', 'debate', 'agents', 'CFO', or 'Actuary'. Draft exclusively as formal Subject Matter Expert Elicitation (SME Elicitation).
            
            PRIOR DEBATE TRANSCRIPT:
            {history}
            
            Extract the assessed controls into the structured ConsensusAdjustment schema.
            """
            
            adjustment = await self._generate_pydantic_with_retry(
                final_prompt,
                schema=ConsensusAdjustment
            )
            
            with open(transcript_file, "a", encoding="utf-8") as f:
                f.write(f"\n======================================================\n")
                f.write(f"--- COMPLETE DEBATE FOR CAPABILITY: {cap} ---\n")
                f.write(history)
                f.write(f"\n⚙️ ADVERSARIAL CONTROLS CONSENSUS EXTRACTED:\n")
                for c in adjustment.controls_assessed:
                    f.write(f"- Control: {c.control_id} | Status: {c.implementation_status}\n  Justification: {c.evidence_grounding}\n")
                f.write(f"- General Rationale: {adjustment.justification}\n")
                f.write("======================================================\n")
                
            return (p_idx, h_idx, adjustment)
            
        except Exception as e:
            logger.warning(f"Adversarial control debate failed for {cap}: {e}")
            return None
