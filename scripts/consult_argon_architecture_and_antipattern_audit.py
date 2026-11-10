#!/usr/bin/env python3
"""Consult gemini-4-argon to diagnose recent antipatterns and architect an uncompromising elimination plan."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Code Quality Arbiter, and Chief Forensic Auditor for the Assessment Engine.

CRITICAL USER MANDATE & COMPLAINT:
The user has rightfully expressed outrage at severe antipatterns and regressions recently introduced into the codebase:
"se puede saber que cojones has hecho? un antipatron grave? en locales.json y lo que acabas de programar? si es así mira como solucionarlo con gemini-4-argon bajo las siguiente premisa y dejarlo solucionado:
- Antes de ponernos a programar hay que pensar bien cómo lo vamos a abordar y en cuántas fases para garantizar que queda sin errores y que vamos a ser número 1 mundial, de cualquier vertical, en cualquier idioma.
- El código debe estar 100% en inglés, nada de español ni una sola palabra.
- Aumentar la calidad de los entregables al 100%.
- CERO hardcoding: debe servir para cualquier empresa del mundo, desde mediana a top tier."

THE RECENT BLUNDERS & ANTIPATTERNS IDENTIFIED:
1. ANTIPATTERN 1: Linguistic "Frankenstein" Mixture in Deliverables:
   In Rede D'Or (Portuguese `pt`), paragraph 10 in Annex 4 generated this grotesque hybrid sentence:
   "A avaliação técnica do domínio de Data Services & Storage na Rede D'Or São Luiz (Data Services & Storage architecture, managed operational workloads, and automated control procedures) estabelece uma maturidade arquitetural estimada de 1,79 sobre 5,0 (Nível 1 - Initial). A plataforma atual sustenta com solvência as operações diárias de mission-critical customer-facing workloads, real-time transaction pipelines, and core Integrated Hospital Network & Diagnostic Centers digital services através da dedicação contínua da equipe técnica. Contudo, identificam-se oportunidades claras de modernização para reinforcing automated resiliency, eliminating single points of dependency..."
   CAUSE: A static Portuguese template in `locales.json` was populated with dynamic English tokens (`{operational_mission}`, `{primary_workloads_summary}`, `{posture_modernization_focus}`) generated in `scripts/build_client_delivery_suite.py`! This is an unacceptable linguistic bastardization.

2. ANTIPATTERN 2: Hardcoded Python Taxonomy Dictionaries:
   In `scripts/build_client_delivery_suite.py`, a helper `resolve_contextual_technology` was added with an explicit hardcoded dictionary mapping "T1", "T2", ... "T10" to lists of keywords like `["facility", "power", "cooling"]`, `["compute", "server", "vmware"]`.
   CAUSE: Bypassing the project's existing configuration infrastructure (`engine_config/tower_classification_keywords.json` or ontology taxonomies) to write quick inline Python hacks.

3. ANTIPATTERN 3: Static Prose Catalogs in `locales.json`:
   `locales.json` is still acting as a Frankenstein repository of analytical sentences with `{placeholder}` tokens, instead of being restricted purely to structural UI labels (e.g. "Table of Contents", "Page", "Executive Summary", "Financial Exposure").

YOUR MISSION:
Deliver a comprehensive, uncompromising, multi-phase master architectural plan to permanently eradicate:
- All static prose templates with token interpolation from `locales.json`.
- All hardcoded dictionary hacks from `scripts/` and `src/`.
- All linguistic cross-contamination (when a document is generated in Portuguese, French, Spanish, or German, 100% of its sentences and tokens must be in that target language, with ZERO English leaks).

The plan must define:
1. PHASE 1: Root Cause & Architecture Invariants (The non-negotiable laws that every component must obey).
2. PHASE 2: Data Contract Decoupling (How the payload must provide self-contained, 100% native language narratives so the AST compiler never interpolates English tokens into foreign templates).
3. PHASE 3: Purging `locales.json` & Configuration Centralization (Moving all classification keywords into `engine_config/` and stripping `locales.json` of all domain analytical prose).
4. PHASE 4: Verification & Automated Anti-Frankenstein Quality Gates (Deterministically testing that non-English deliverables have 0 English words in analytical paragraphs).

Constraints:
- Respond in 100% Technical English.
- Be brutally honest, rigorous, and architecturally definitive.
- Zero code implementation yet—deliver the comprehensive, step-by-step Master Plan.

Deliver your architectural judgment now.
"""

def main() -> None:
    print(f"Submitting uncompromising audit request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_ANTIPATTERN_REMEDIATION_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nArchitecture Plan generated successfully. Report written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3500])
    if len(audit_report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")

if __name__ == "__main__":
    main()
