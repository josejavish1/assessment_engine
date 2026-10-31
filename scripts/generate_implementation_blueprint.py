import os
import time
from pathlib import Path
from assessment_engine.infrastructure.genai_client import get_model, ModelTier, create_genai_client

client = create_genai_client()
model = get_model(ModelTier.REASONING)

roadmap_text = Path("docs/architecture/MASTER_ENTERPRISE_REMEDIATION_ROADMAP.md").read_text(encoding="utf-8")

clusters = [
    "CLUSTER 1: Container Resilience & Process Control",
    "CLUSTER 2: Epistemic Integrity & Fail-Closed State",
    "CLUSTER 3: Multi-Dimensional Sovereignty & Graph",
    "CLUSTER 4: Domain Purity, Type Safety & i18n"
]

out_path = Path("docs/architecture/MASTER_IMPLEMENTATION_BLUEPRINT.md")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text("# LOW-LEVEL IMPLEMENTATION BLUEPRINT: MASTER REMEDIATION ROADMAP\n\n", encoding="utf-8")

for cluster in clusters:
    prompt = f"""Role: Principal Systems Architect & Chief Software Engineer (Google Tier-1 / Anthropic Infrastructure).
Language Mandate: All engineering analysis, schemas, code blueprints, and test strategies MUST be in 100% formal Technical English. Zero Spanish allowed.

Task: Formulate the definitive, Low-Level Implementation Blueprint (LLD) for the tasks in {cluster} defined in the MASTER ENTERPRISE REMEDIATION ROADMAP.

Context Roadmap:
{roadmap_text}

Strict Constraints:
1. Enterprise Universality: Must serve any enterprise globally, in any vertical, in any human language.
2. Zero Hardcoding: No hardcoded languages, vendors, locales, or consultant names. Complete decoupling.
3. Bug & Anti-Pattern Free: Must architecturally guarantee zero hallucinations, mathematical purity (IEEE-754 / FAIR), and structural integrity (Fail-Fast).
4. Code Level Specifications: For the tasks in {cluster}, provide exact class signatures, crucial code snippets, and specific `pytest` strategy guaranteeing 100% test coverage.

Structure the output as a formal Markdown section for this specific cluster. Do not include conversational filler.
"""
    print(f"Generating for {cluster}...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            with out_path.open("a", encoding="utf-8") as f:
                f.write(resp.text + "\n\n---\n\n")
            print(f"Done for {cluster}")
            break
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {cluster}: {type(e).__name__} - {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                print(f"Skipping {cluster} after {max_retries} attempts.")
