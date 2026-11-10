#!/usr/bin/env python3
"""Consult gemini-4-argon: Is the Tribunal Post-Processor / Self-Correction Editor an anti-pattern or the 2026 state-of-the-art?"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = """You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Global Platforms.

THE USER'S DEEP INTELLECTUAL REFLECTION & PROPOSAL:
"Pero aquí me estoy dando cuenta de que es que estos informes que tú me estás pasando son realmente reales y dicen cosas que son realmente de fallos que tenemos. Lo que no sé es por qué se producen esos fallos. Porque tenemos muchos... La idea es identificar el origen de por qué ocurren y que no puedan volver a ocurrir en el futuro en ninguna empresa del mundo con ningún nivel de madurez distinto.
Es que ya estoy llegando a la conclusión, y no sé si esto es un antipatrón o no, que es:
UNA VEZ QUE TERMINEN DE GENERARSE TODOS LOS FICHEROS, QUE UN TRIBUNAL COMO ESTE QUE HACEMOS REVISE CADA UNO DE LOS FICHEROS Y RETOQUE A MANO EL FICHERO.
Ya es lo único que se me ocurre. Pero eso huele casi a un antipatrón gigante, pero es que mira, a lo mejor no lo es."

YOUR MANDATE:
Deliver a profound, definitive architectural verdict:
1. **WHY DO THESE FLAWS ACTUALLY OCCUR IN OUR SYSTEM?**
   - Explain the root cause of the "Split-Brain" generation:
     * Component 1 (Interview parser / transcript) extracts qualitative facts.
     * Component 2 (Questionnaire scoring) computes CMMI scores.
     * Component 3 (Actuarial calculator) computes ALE/P90.
     * Component 4 (Static templates / locales) injects pre-written boilerplate paragraphs.
   - Because these 4 components run independently without a shared Epistemic Graph, they introduce discrepancies:
     * The transcript says NetApp MetroCluster, while the survey says no off-site backups.
     * The survey says PAM=4.5, while the transcript says shared root passwords.
     * The template injects "puntos de venta digitales" because it was written for a generic commercial sector.
2. **IS AN "ADVERSARIAL TRIBUNAL EDITOR / ACTOR-CRITIC AGENT" AN ANTIPATTERN?**
   - Answer: Analyze both perspectives:
     * *Why it COULD be an anti-pattern if done naively:* If an unconstrained LLM "retouches" documents randomly, it can hallucinate new contradictions, break Word XML formatting, or introduce endless non-deterministic drift.
     * *Why it is the CUTTING-EDGE STATE OF THE ART (SOTA) IN 2026 if designed properly:*
       - The **Actor-Critic / Generator-Verifier (Self-Correction) Architecture** (RLVR, Constitutional AI, Reflexion).
       - How OpenAI, Anthropic, and DeepMind use Verifier Models (Critic) to audit the Actor's output and execute deterministic, constrained remediation before user delivery.
3. **THE CONCRETE ARCHITECTURAL IMPLEMENTATION OF THE CRITIC LOOP:**
   - How should this "Tribunal Editor" work in production?
     * Step 1 (Generation): Document is compiled.
     * Step 2 (Adversarial Audit): The 10-point Tribunal Auditor inspects the document (checks for cross-sector tokens like e-commerce in factories, checks CMMI-vs-findings, checks arithmetic).
     * Step 3 (Constrained Remediation): If the auditor detects a defect, it triggers a deterministic patch targeting ONLY the defective AST node, re-verifies, and signs off.
4. **EXECUTIVE SYNTHESIS & REASSURANCE:**
   Deliver a clear, definitive message to the Founder: explain why their intuition is spot-on, and how to implement this cleanly without it becoming messy.

Respond in 100% Technical English with supreme executive authority and clarity.
"""

def main() -> None:
    print(f"Submitting Actor-Critic Tribunal Architecture deliberation to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "architecture" / "ARGON_ACTOR_CRITIC_TRIBUNAL_ARCHITECTURE.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nActor-Critic Architecture written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
