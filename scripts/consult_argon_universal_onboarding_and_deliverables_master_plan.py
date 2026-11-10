#!/usr/bin/env python3
"""Consult Gemini-4-Argon for a comprehensive, multi-tenant Master Plan for universal onboarding, regulatory resolution, and deliverable quality elevation."""

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

ARGON_PROMPT = """You are 'gemini-4-argon', Supreme Cognitive Arbiter, Chief Enterprise Architect, and Master of Multi-Tenant IT Infrastructure Governance.

# CONTEXT & FORENSIC PROBLEM STATEMENT

Our platform is a self-service, world-class IT Infrastructure Assessment and Strategic Transformation Engine.
It translates technical operational debt into quantified financial risk (FAIR actuarial model) and generates board-ready native Word (.docx) deliverables (Tome 1 AS-IS & TO-BE Roadmap + up to 10 Specialized Technical Annexes).

In our latest live deployment test, we simulated logging in as the CTO of **Cementos Molins** (a major Spanish multinational industrial manufacturer of cement and heavy construction materials, ~6,500 employees, ~1,250M € revenue).

The resulting screen displayed severe technical, linguistic, and UX anti-patterns:
1. **Gross Regulatory Incongruence (DORA on a Cement Company):**
   - The screen displayed `DORA / NIS2 / RGPD` for Cementos Molins!
   - DORA (Digital Operational Resilience Act, Regulation (EU) 2022/2554) is STRICTLY binding on financial entities (banks, investment firms, insurers) and their critical ICT third-party providers. Assigning DORA to a heavy process manufacturing/cement firm is an embarrassing hallucination that instantly destroys technical credibility before a real CTO.
   - For an industrial manufacturer in the EU/Spain, the actual binding frameworks are: **NIS2 (Essential/Important Entities - Manufacturing of chemicals/critical products), IEC 62443 (Security for Industrial Automation and Control Systems / OT / SCADA), ISO 27001 / ISO 22237, ENS (Esquema Nacional de Seguridad if supplying public sector), and GDPR/RGPD**.
2. **Linguistic Corruption & Spanglish:**
   - Raw untranslated backend catalog strings leaked into the Spanish UI: `Spain` instead of `España`, `Heavy Process Manufacturing & Construction Materials` in English within a Spanish interface, `~1250M EUR` instead of localized format `1.250 M€`.
3. **Severe Recurrence of "Containeritis" & Bureaucratic Robot-Speak:**
   - Instead of the clean, editorial, left-aligned Apple/Linear canvas achieved in Tab 1, Tab 2 collapsed into a dull stack of 4 gray-bordered nested boxes (`bg-white border border-[#e5e5ea] p-6`) with boxes inside boxes for radio buttons.
   - The copy sounded like an AI pretending to be a tax bureaucrat: *"Expediente Pre-Configurado · Resolución Autónoma"*, *"Perfil Operativo Identificado"*, *"Decisión de Alcance Estratégico"*, *"Confirmar Perímetro y Ver Disciplinas Técnicas"*.
4. **Premature Assumptions & Broken Progressive Disclosure:**
   - In Tab 1 and the header, premature labels like `Progreso: 0 / 10` or hardcoded `10 Torres` assumed every client must audit all 10 towers before knowing their scope!
   - A client may only be responsible for Cloud, or only evaluate 3 domains, or want to audit a specific manufacturing plant (e.g. Planta Martorell) rather than the entire global holding.

# CORE MANDATES & IMMUTABLE REQUIREMENTS

1. **100% Technical English Codebase:**
   - Absolute ban on Spanish in Python files, TSX components, variable names, functions, docstrings, comments, schemas, and logs. Spanish is strictly an i18n data payload in `engine_config/locales_ui.json` and client deliverable `.docx` output.
2. **Zero Hardcoding & Epistemic Purity:**
   - NO hardcoded regulatory strings (like `DORA / NIS2 / RGPD`) in JSX or Python logic!
   - Regulatory frameworks must be resolved dynamically through a declarative, extensible Single Source of Truth (SSOT) catalog in `engine_config/` based on `(country_code, industry_vertical)`.
3. **Universal Global Multi-Tenant Support (Mid-Market to Mega-Enterprise):**
   The architecture must flawlessly handle any enterprise in the world without touching a single line of code:
   - **Case A: Cementos Molins** (Spain, Heavy Process Manufacturing / Building Materials, EUR, NIS2 / IEC 62443 / ISO 27001).
   - **Case B: Starling Bank / Revolut** (UK, Digital-Native Cloud FinTech, GBP, FCA/PRA Operational Resilience, DORA EU cross-border, ISO 27001, AWS serverless).
   - **Case C: Rede D'Or São Luiz** (Brazil, Large Private Hospital Network, BRL, Portuguese, ANPD / LGPD, CFM, RDC 330, PACS clinical telemetry, hybrid infrastructure).
   - **Case D: Geodis / CMA CGM** (France, Logistics & Freight Forwarding, EUR, French, NIS2 transport/logistics, EDI customs, distributed warehouses).
   - **Case E: Mid-Sized Enterprise** (50M revenue, 250 employees, single jurisdiction) to **Mega-Holding** (50,000M revenue, 120,000 employees, multi-region).
4. **Progressive Disclosure UX (Apple / Linear Tier 1 Standard):**
   - Clean, left-aligned, editorial typography. Zero nested gray cages.
   - Step 1 (Welcome & Scope Narrative) -> Step 2 (Autonomous Profile & Perimeter Decision: Group vs. Subsidiary) -> Step 3 (Modular Domain Selection & Discovery) -> Step 4 (Results & Deliverables).
   - Linear step locking: future steps cannot be jumped into until prior milestones are unlocked.
5. **Supreme Deliverable Quality (100% Actuarially & Forensically Defensible):**
   - Tome 1 (.docx) with executive summary, holistic maturity radar, FAIR VaR loss model, technical debt gaps, and TO-BE modernization roadmap.
   - 10 Specialized Technical Annexes (.docx).

# YOUR MISSION

Design a comprehensive, phased, zero-defect Master Architecture & Implementation Plan:

1. **Phase 1: Declarative Regulatory & Compliance Ontology (SSOT Architecture)**
   - Design the schema and catalog for `engine_config/regulatory_frameworks.json`.
   - Define the matrix mapping `(country_code, industry_id)` to authentic, authoritative regulatory standards:
     - Financial Services (EU: DORA, NIS2, GDPR, EBA; UK: FCA/PRA, UK GDPR; US: SEC Cyber, NYDFS; Brazil: BACEN, LGPD).
     - Heavy Manufacturing & Energy (EU: NIS2 Essential, IEC 62443 OT, ISO 27001, ENS; US: NERC CIP, CMMC; Global: ISO 22237).
     - Healthcare & Life Sciences (EU: NIS2, MDR, GDPR; US: HIPAA, HITECH; Brazil: ANPD, CFM, LGPD).
     - Retail & Logistics (PCI-DSS, NIS2, GDPR).
   - Detail how the backend resolves and returns localized regulatory tags dynamically.

2. **Phase 2: Autonomous Context Pre-Hydration & Dynamic Locale Decoupling**
   - Specify how authenticated user credentials (`user.email`) trigger autonomous enrichment without bureaucrat speak.
   - Eliminate all Spanglish: ensure industry names, countries, currencies, and regulatory tags are 100% localized via `engine_config/locales_ui.json` and `engine_config/locales.json`.

3. **Phase 3: Editorial Tab 2 Architecture (The Strategic Perimeter & Profile Confirmation)**
   - Design the layout for Tab 2 that completely eliminates containeritis while providing:
     - Clear executive profile readout (Entity, Jurisdiction, Currency, Sector, Scale).
     - Inline calibration drawer (only shown on explicit edit).
     - The single executive choice: Scope Perimeter (Consolidated Corporate Group vs. Specific Operating Division/Subsidiary/Plant).
     - Dynamic scaling of revenue and headcount when a subsidiary is selected.

4. **Phase 4: Modular Domain Selection & Discovery Pipeline (Tab 3 Pre-Flight)**
   - Where and how does the client select their scoped domains?
   - How does the platform recommend domain scope based on the operating model (e.g., recommend on-premise vs. cloud vs. OT)?

5. **Phase 5: Automated Playwright Cross-Tenant Verification Matrix**
   - Define exact automated visual regression test specifications for 3 diverse global tenants:
     1. `cto@molins.com` (Spain, Manufacturing, EUR, Spanish).
     2. `head.infrastructure@starlingbank.co.uk` (UK, FinTech, GBP, English).
     3. `diretor.ti@rededor.com.br` (Brazil, Healthcare, BRL, Portuguese).
   - Specify verification criteria: Zero scrollbar on 1080p, exact localized strings, zero Spanglish, accurate regulatory tags (no DORA on Molins!).

Deliver the Master Plan in 100% Technical English with supreme rigor, actionable specifications, and zero fluff.
"""

def main() -> None:
    print(f"Submitting Universal Master Plan Consultation to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=ARGON_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_UNIVERSAL_ONBOARDING_AND_DELIVERABLES_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print("\n--- EXECUTIVE SUMMARY OF ARGON PLAN ---")
    print("\n".join(report.splitlines()[:50]))

if __name__ == "__main__":
    main()
