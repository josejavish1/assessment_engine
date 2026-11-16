"""
Claim Evidence Validator & Semantic Entailment Engine.

Enforces that narrative claims generated for an operational capability
are semantically entailed by the accredited evidence corpus.

Specifically prevents generating specific physical hardware assertions
(e.g., CCTV coverage, NVR configurations, retention periods) when the
evidence consists exclusively of a quantitative survey score.
"""

from typing import List
import json
from pathlib import Path


def validate_claim_entailment(claim_text: str, evidence_text: str) -> bool:
    """Verifies that the claim does not assert ungrounded physical hardware defects

    when the evidence is restricted to survey scores without empirical transcripts.
    """
    if not claim_text:
        return True

    claim_lower = claim_text.lower()
    evidence_lower = evidence_text.lower() if evidence_text else ""

    cfg_path = (
        Path(__file__).resolve().parents[4]
        / "engine_config"
        / "policies"
        / "epistemic_dependencies.json"
    )
    
    survey_tokens: List[str] = ["score", "survey", "self-assessment", "declared"]
    transcript_tokens: List[str] = ["transcript", "interview", "telemetry", "qualitative evidence"]
    hardware_tokens: List[str] = ["cctv", "nvr", "blind spots", "retention period"]

    if cfg_path.exists():
        try:
            cfg_data = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
            for t_list in cfg_data.get("survey_indicator_tokens", {}).values():
                survey_tokens.extend(t_list)
            for t_list in cfg_data.get("transcript_indicator_tokens", {}).values():
                transcript_tokens.extend(t_list)
            for t_list in cfg_data.get("ungrounded_hardware_claim_tokens", {}).values():
                hardware_tokens.extend(t_list)
        except Exception:
            pass

    # Check if evidence indicates survey-only without qualitative transcript backing
    has_survey = not evidence_lower or any(st in evidence_lower for st in survey_tokens)
    has_transcript = any(tt in evidence_lower for tt in transcript_tokens)
    is_survey_only = has_survey and not has_transcript

    if is_survey_only:
        for token in hardware_tokens:
            if token and token in claim_lower and token not in evidence_lower:
                return False

    return True
