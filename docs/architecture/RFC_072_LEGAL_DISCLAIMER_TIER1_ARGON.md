# RFC 072: Tier-1 Legal Disclaimer Universal Architecture

**Document ID:** ARCH-RFC-072  
**Classification:** Tier-1 Legal-Tech Compliance & Architecture Specification (Confidential)  
**Target Subsystems:** Per-Tower AST Compilers, Consolidated Volume 1 AST Compiler, Localization Catalogs (`locales.json`, `locales_asis_annex.json`, `locales_dynamic/`)  
**Author:** Staff AI Architect & Legal-Tech Compliance Engineer  
**Status:** Approved for Implementation  

---

## 1. Architectural Objective

The Assessment Engine delivers mission-critical technical diagnoses, cyber-resilience postures, and actuarial loss simulations across multinational enterprise clients. Previously, the liability disclaimer rendered in generated deliverables suffered from four architectural defects:
1. **Truncation and Incompleteness:** The disclaimer historically rendered 3 to 4 paragraphs in Volume 1 and certain appendices, omitting explicit waivers of consequential damages and indirect loss.
2. **Asymmetric Locales & Empty Keys:** Keys such as `disclaimer_text_5` were initialized as empty strings (`""`) in primary catalogs or absent in dynamically synthesized locales (`locales_dynamic/*.json`).
3. **Loop Bounds & Iteration Drift:** Compilers exhibited split-brain iteration logic (e.g., `tomo_asis_ast_compiler.py` hardcoding `("disclaimer_text_1", ..., "disclaimer_text_4")` while `ast_appendices_builder.py` looped `range(1, 6)`).
4. **Hardcoded Tenancy Leakage:** Legacy paragraphs contained partial brand tokens or lacked dynamic parameterization for `{client_name}` and `{company_name}`.

### Core Objectives:
- **Deploy a 5-Pillar Tier-1 Legal Disclaimer:** Enforce institutional-grade liability protection matching top-tier international advisory standards across:
  1. *Declarative Nature & Exoneration* (non-intrusive assessment, client-provided telemetry, no field audit warranty).
  2. *Actuarial & Stochastic Risk Modeling* (Open FAIR™ / Monte Carlo ALE estimations, non-accounting balance sheet guarantees).
  3. *Non-Legal & Non-Regulatory Advice* (technical hygiene only, client officers retain non-transferable compliance liability).
  4. *Confidentiality, Third-Party Indemnity & Hold Harmless* (strict distribution prohibition, client indemnification).
  5. *Waiver of Consequential & Indirect Damages* (total waiver of loss of profits, downtime, reputational damages).
- **Universal Multi-Tenant Parametric Decoupling:** Complete parameterization via `{client_name}` and `{company_name}`. Zero tenant or consulting firm hardcoding.
- **Fail-Safe Compiler Traversal:** Robust normalization and fallback resolution preventing `KeyError`, empty paragraph rendering, or unrendered strings across all 20 tower annexes and Volume 1 deliverables.

---

## 2. Universal Legal Disclaimer Localization Catalogs (ES & EN)

The canonical texts must be synchronized across `engine_config/locales.json` and `engine_config/locales_asis_annex.json`.

### 2.1 Spanish Locale (`es`) — Institutional Tier-1 Wording

```json
{
  "disclaimer_text_1": "1. Naturaleza Declarativa y Exoneración de Auditoría de Campo: El presente informe de diagnóstico técnico (el \"Documento\") constituye un ejercicio de evaluación rápida (Fast Assessment) elaborado por {company_name} exclusivamente para el uso interno y confidencial de {client_name}. El cliente reconoce y acepta que el diagnóstico se fundamenta única y exclusivamente en la información documental, telemetrías lógicas, narrativas de arquitectura y autoevaluaciones proporcionadas de buena fe por el personal técnico de {client_name}, sin que {company_name} haya efectuado inspecciones físicas sobre el terreno, auditorías de código fuente en profundidad, pruebas de penetración intrusivas ni verificación forense independiente de los activos. En consecuencia, {company_name} no asume obligación de verificar la exactitud o completitud de los datos suministrados y queda exonerada de toda responsabilidad derivada de omisiones, inconsistencias o inexactitudes en la información de origen.",
  "disclaimer_text_2": "2. Modelos Actuariales, Proyecciones Estocásticas y O-FAIR: Las cuantificaciones económicas de riesgo, pérdidas por interrupción operativa y los valores de Expectativa de Pérdida Anualizada (ALE / P90 / CVaR) calculados mediante la metodología Open FAIR™ y simulaciones de Monte Carlo son estimaciones estadísticas de probabilidad basadas en distribuciones de incertidumbre matemática. Dichas cifras constituyen exclusivamente herramientas analíticas de priorización presupuestaria de inversiones técnicas (CAPEX/OPEX) y justificación del coste de inacción (Business Case). Bajo ninguna circunstancia constituyen auditorías contables de balance, compromisos de cobertura aseguradora ni pasivos legalmente exigibles frente a terceros o reguladores.",
  "disclaimer_text_3": "3. Carácter Exclusivamente Técnico y Ausencia de Asesoramiento Legal: Las referencias a marcos de cumplimiento normativo (incluyendo NIS2, DORA, ISO/IEC 27001, RGPD o normativas sectoriales de infraestructuras críticas) se exponen con fines estrictamente informativos y de buenas prácticas de ingeniería de seguridad tecnológica. El Documento no constituye en ningún caso asesoramiento legal, regulatorio, fiscal o procesal formal. La interpretación e implantación de las exigencias normativas es responsabilidad exclusiva, personal e intransferible de los administradores, directores y asesores jurídicos de {client_name}.",
  "disclaimer_text_4": "4. Confidencialidad, Restricción de Distribución e Indemnización (Hold Harmless): Este Documento contiene información estratégica altamente sensible relativa a la postura de ciberresiliencia y vulnerabilidades de {client_name}. Queda expresamente prohibida su copia, distribución, comunicación pública o cesión a terceros ajenos a la organización sin la previa autorización expresa y por escrito de {company_name}. {company_name} no asume responsabilidad alguna frente a terceros que accedan a este informe. {client_name} se compromete a mantener indemne a {company_name}, sus socios, consultores y subcontratistas frente a cualquier reclamación, sanción, daño o coste legal originado por la divulgación, uso ilegítimo o cesión indebida del Documento a terceros.",
  "disclaimer_text_5": "5. Renuncia Expresa a Daños Consecuenciales y Lucro Cesante: En la máxima medida permitida por la legislación aplicable, {company_name} no será responsable en ningún caso, contractual o extracontractualmente, por daños indirectos, incidentales, punitivos o consecuenciales, incluyendo de manera enunciativa pero no limitativa, lucro cesante, pérdida de ingresos, paradas de planta, interrupción del negocio, pérdidas de datos o daños reputacionales derivados del uso o la imposibilidad de uso de las recomendaciones o valoraciones contenidas en este Documento."
}
```

### 2.2 English Locale (`en`) — Institutional Tier-1 Wording

```json
{
  "disclaimer_text_1": "1. Declarative Nature & Field Audit Exoneration: This technical diagnostic report (the \"Document\") represents an expedited assessment (Fast Assessment) prepared by {company_name} solely for the confidential, internal use of {client_name}. The client acknowledges and agrees that the evaluation is strictly based upon documentary evidence, logical telemetry, architectural narratives, and self-assessment disclosures provided in good faith by technical personnel of {client_name}, without {company_name} having conducted physical field audits, in-depth source code analysis, intrusive penetration testing, or independent evidentiary verification. Consequently, {company_name} undertakes no obligation to verify the accuracy or completeness of the underlying information and is fully exonerated from any liability arising from errors, omissions, or inaccuracies in the client-furnished data.",
  "disclaimer_text_2": "2. Actuarial Risk Modeling & Open FAIR™ Estimates: Quantitative financial risk exposures, business interruption forecasts, and Annual Loss Exposure figures (ALE / P90 / CVaR) calculated via the Open FAIR™ standard and Monte Carlo stochastic algorithms are mathematical probability estimates grounded in industry uncertainty modeling. These figures serve solely as executive analytical tools for capital investment prioritization (CAPEX/OPEX) and cost-of-inaction justification (Business Case). Under no circumstances do they constitute formal balance-sheet accounting audits, asset appraisal guarantees, or legally enforceable liabilities.",
  "disclaimer_text_3": "3. Purely Technical Scope & Non-Legal Advice: References to regulatory frameworks (including NIS2, DORA, ISO/IEC 27001, GDPR, or critical infrastructure mandates) are presented exclusively for technical benchmarking and cybersecurity hygiene purposes. This Document does not constitute formal legal, regulatory, or tax advice. Legal interpretation and final compliance governance remain the strict, non-transferable obligation of the corporate officers, board of directors, and legal counsel of {client_name}.",
  "disclaimer_text_4": "4. Confidentiality, Distribution Restrictions & Third-Party Indemnification: This Document contains proprietary, highly sensitive intelligence regarding the architectural posture and vulnerabilities of {client_name}. Any unauthorized disclosure, distribution, duplication, or dissemination, in whole or in part, to third parties without prior express written authorization from {company_name} is strictly prohibited. {company_name} assumes zero liability toward any third party accessing or relying upon this report. {client_name} agrees to indemnify and hold harmless {company_name}, its affiliates, employees, and subcontractors against any third-party claims, liabilities, damages, or defense expenses arising out of the unauthorized release or misuse of this Document.",
  "disclaimer_text_5": "5. Waiver of Consequential, Indirect, and Punitive Damages: To the maximum extent permitted by applicable law, {company_name} shall not be liable, whether in contract, tort (including negligence), or otherwise, for any indirect, incidental, consequential, special, or punitive damages, including but not limited to loss of profits, loss of operational revenue, business interruption, factory downtime, data loss, or reputational impairment arising out of or in connection with the recommendations or analytical conclusions set forth in this Document."
}
```

---

## 3. Codebase Modification Plan

### 3.1 `src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py`
* **Target Location:** Method `_build_unified_appendix(self, ...)` (around lines 2025–2032).
* **Current Defect:** Hardcodes 4 paragraphs and does not filter out empty strings:
  ```python
  for disc_k in ("disclaimer_text_1", "disclaimer_text_2", "disclaimer_text_3", "disclaimer_text_4"):
      disc_text = t(disc_k, locale=doc_lang, client_name=client_name, company=client_name)
      nodes.append(ParagraphNode(text=disc_text, font_size=9.0, space_after=6))
  ```
* **Required Implementation:**
  ```python
  company_name = str(self.brand_data.get("company_name") or "Consulting Advisory Partner")
  for i in range(1, 6):
      disc_k = f"disclaimer_text_{i}"
      disc_text = t(
          disc_k,
          locale=doc_lang,
          default="",
          client_name=client_name,
          company_name=company_name,
          company=company_name,
      )
      if disc_text and disc_text != disc_k:
          nodes.append(ParagraphNode(text=disc_text, font_size=9.0, space_after=6))
  ```

### 3.2 `src/assessment_engine/adapters/compilers/ast_appendices_builder.py`
* **Target Location:** Function `build_appendix_c_glossary_and_disclaimer(...)` (around lines 411–420).
* **Current Defect:** Loops `range(1, 6)` but only formats `{client_name}`, missing `{company_name}` substitution.
* **Required Implementation:**
  ```python
  client_name = str(ctx.get("client_name") or "CLIENT").upper()
  company_name = str(brand_data.get("company_name") or ctx.get("company_name") or "Consulting Advisory Partner")
  for i in range(1, 6):
      disc_text = vocab.get(f"disclaimer_text_{i}", "")
      if disc_text:
          interpolated = (
              disc_text.replace("{client_name}", client_name)
              .replace("{company_name}", company_name)
              .replace("{company}", company_name)
          )
          nodes.append(ParagraphNode(text=interpolated))
          nodes.append(SpacerNode(points=8))
  ```

### 3.3 `src/assessment_engine/adapters/compilers/asis_appendices_chapter.py`
* **Target Location:** Legacy fallback loop in `appendices_chapter` (around lines 350–358).
* **Current Defect:** Directly appends unformatted `vocab.get(k, "")` without placeholder replacement.
* **Required Implementation:**
  Ensure `{company_name}` and `{client_name}` substitution is applied to each paragraph `k` in `["disclaimer_text_1", ..., "disclaimer_text_5"]` prior to calling `add_body_paragraph`.

---

## 4. Fallback Strategy for Minor and Dynamic Locales

When compiling deliverables for languages managed via `engine_config/locales_dynamic/*.json` (e.g., `sv.json`, `it.json`, `pl.json`):
1. **Default String Sentinel:** Always pass `default=""` to `t()`. The internationalization helper `get_localized_string` falls back to the key string itself if undefined and no default is provided. By asserting `disc_text != disc_k and disc_text.strip() != ""`, compilers avoid emitting literal key strings.
2. **JIT Locale Backfill:** The script `scripts/remediate_locales_rfc071.py` or a dedicated synchronization task must scan all files in `engine_config/locales_dynamic/` and inject English text for `disclaimer_text_5` if absent, ensuring translation completeness without build breakage.
3. **Graceful Degradation:** If `disclaimer_text_5` is missing in a minor locale and unresolvable via fallback, paragraphs 1–4 continue to render without runtime exceptions, preserving pipeline determinism.