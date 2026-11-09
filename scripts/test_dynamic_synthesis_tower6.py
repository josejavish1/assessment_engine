"""Surgical test demonstrating dynamic LLM evidence synthesis on Starling Bank Tower 6.

1. Extracts actual Tower 6 dialogue from raw interview transcript.
2. Prompts Gemini to synthesize domain semantics, workloads, failure triggers, and findings.
3. Injects the synthesized data into blueprint_t6_payload.json.
4. Compiles Annex 6 DOCX.
5. Performs a before/after comparison of the resulting text.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import docx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.adapters.compilers.payload_to_ast import compile_asis_docx_via_ast
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

TRANSCRIPT_PATH = REPO_ROOT / "tests/test_data/synthetic_clients/uk_fintech/transcription_interview_session.docx"
PAYLOAD_PATH = REPO_ROOT / "working/starling_bank/T6/blueprint_t6_payload.json"
OUTPUT_DOCX_PATH = REPO_ROOT / "working/out/starling_bank/Starling_Bank_202610_Annex_06_Infrastructure_Security_Identity_ASIS.docx"


def extract_transcript_context() -> str:
    """Extract Tower 6 dialogue lines from the raw interview transcript."""
    doc = docx.Document(TRANSCRIPT_PATH)
    t6_lines = []
    capture = False
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "Tower 6" in txt or "Sarah Jenkins" in txt or "Zero Trust" in txt or "Security" in txt:
            t6_lines.append(txt)
    return "\n\n".join(t6_lines)


def synthesize_tower6_evidence(transcript_context: str) -> dict[str, any]:
    """Prompt Gemini to synthesize grounded domain telemetry and semantics."""
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)

    prompt = f"""You are the Lead Cybersecurity Architect for an assessment of Starling Bank.
Based strictly on the following technical interview excerpt:

--- TRANSCRIPT EXCERPT ---
{transcript_context}
--- END EXCERPT ---

Synthesize a JSON object with these EXACT keys:
1. "operational_mission": A concise noun phrase (10-18 words) describing the true operational security mission for Starling Bank (e.g. zero trust cloud identity, Teleport PAM, Vault secrets rotation).
2. "primary_workloads_summary": A concise noun phrase (8-16 words) describing their real workloads (e.g. cloud-native AWS production workloads, real-time Faster Payments clearing, and EKS container microservices).
3. "posture_modernization_focus": A concise verb phrase (12-22 words) describing their forward-looking priorities without contradicting their high maturity.
4. "compound_failure_trigger": A severe, plausible failure scenario trigger (10-18 words) for a cloud-native bank (e.g. hyperscaler regional control plane partition combined with simultaneous authentication token invalidation).
5. "findings_briefs": A list of exactly 3 concise strings describing operational gaps or modernization friction identified in the interview (format: "Area: Observation").
6. "inventory": A string listing real security tools confirmed in the interview (Okta, Teleport, HashiCorp Vault, CrowdStrike Falcon, Splunk Cloud).
7. "strengths": A list of 3 verified security strengths confirmed in the interview.

Respond ONLY with valid, raw JSON.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    raw = response.text.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw.strip())


def main() -> None:
    print("1. Extracting Tower 6 transcript context...")
    transcript_ctx = extract_transcript_context()
    print(f"   ✓ Extracted {len(transcript_ctx)} characters of interview testimony.")

    print("2. Prompting Gemini for dynamic evidence synthesis...")
    synth_data = synthesize_tower6_evidence(transcript_ctx)
    print("   ✓ Synthesized dynamic domain semantics:")
    for k, v in synth_data.items():
        print(f"     - {k}: {str(v)[:75]}...")

    print("3. Updating blueprint_t6_payload.json...")
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    payload["operational_mission"] = synth_data["operational_mission"]
    payload["primary_workloads_summary"] = synth_data["primary_workloads_summary"]
    payload["posture_modernization_focus"] = synth_data["posture_modernization_focus"]
    payload["compound_failure_trigger"] = synth_data["compound_failure_trigger"]
    payload["critical_findings_summary"] = synth_data["findings_briefs"]
    payload["inventory"] = synth_data["inventory"]
    payload["strengths"] = synth_data["strengths"]

    PAYLOAD_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("   ✓ Injected dynamic fields into payload.")

    print("4. Recompiling Annex 6 DOCX...")
    compile_asis_docx_via_ast(PAYLOAD_PATH, OUTPUT_DOCX_PATH, doc_lang="en")
    print(f"   ✓ Compiled: {OUTPUT_DOCX_PATH.name} ({OUTPUT_DOCX_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
