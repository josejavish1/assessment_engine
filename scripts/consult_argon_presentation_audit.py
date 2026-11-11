"""Consult gemini-4-argon: Forensic adversarial analysis of Presentation & Reporting Layer Audit."""

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

# Read the external audit report text provided by the user
EXTERNAL_AUDIT_REPORT = """
Auditoría de presentación/reporting sobre 41d4c2d completada. No edité archivos.

## Veredicto
La remediación eliminó parte del cálculo duplicado, pero la capa de presentación sigue siendo un motor de negocio paralelo. El split-brain continúa activo y alcanzable desde las rutas de generación de anexos y Tomo 1.

### Evidencia cuantitativa
- payload_to_ast.py: 4.730 LOC, 11 mutaciones directas de campos de negocio, 16 imports actuariales/calibradores, 8 except Exception.
- in_memory_asis_compiler.py: 1.900 LOC, 7 mutaciones de scores, un motor actuarial alternativo.
- En los compiladores encontré al menos 18 asignaciones directas a métricas/scores, 24 capturas genéricas y más de 24 imports de cálculo/calibración actuarial.
- Confirmé más de 30 supuestos numéricos de negocio dentro de presentación, sin contar tamaños visuales, fuentes o colores.
- La supuesta prueba de “inmunidad de presentación” y la prueba que exige ALE positivo sin evidencia pasan ambas, pese a estos defectos.

## P0 — Split-brain actuarial ejecutable
### 1. derive_in_memory_fair_risks() es un segundo motor actuarial
Archivo: src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py:532-730.
Si faltan métricas canónicas, calcula: deficit = 5 - score; TEF = deficit × 0.8; LM = deficit × 1.5; ALE = TEF × LM × 1.000; P90 = ALE × 2,5; LEF con TEF × 0,09, limitado a 0,08–0,50; SLE como ALE / LEF o LM × 5.000.
Cuando no hay findings, instancia ActuarialInferenceEngine, asume ingresos de 100 M y crea cinco riesgos latentes.
Alcanzable desde asis_fair_chapter.py:591, tomo_asis_ast_compiler.py:478, tomo_asis_ast_compiler.py:1390, payload_to_ast.py:3050.

### 2. payload_to_ast.py sigue mutando resultados
- Ejecuta ActuarialDowntimeCalibrator y actualiza financial_telemetry durante compilación: líneas 1436-1451.
- Recalibra y muta scores según regex de narrativa: líneas 726-794.
- Sustituye score ausente por 2,5 y escribe score, overall_score, exact_score: 1548-1570.
- Escala cada ALE para forzar que la suma coincida con el total: 3395-3411.
- Escribe sle y lef derivados en riesgos: 3311-3324.
- Construye un nuevo FairActuarialInput en la tarjeta: 3765-3838.
- Si falta SLE canónico, lo recalcula con RTO y coste horario: 3824-3827.
- Recalcula frecuencia de toil mediante ALE / SLE o TEF × 6: 3989-3999.

### 3. tomo_asis_ast_compiler.py reconstruye el portfolio
Recalcula:
- corporate ALE desde torres o annual_revenue × 0,001: 492-497;
- P90 desde suma derivada o ALE × 2,5: 498-509;
- exposición a tres años y estrés: 511-513;
- asignación por dominio usando heatmap, pesos o reparto igual: 821-857;
- standalone ALE faltante como reparto uniforme: 1438-1446;
- una nueva asignación mediante EulerPortfolioAllocator: 1456-1463.

## P1 — Reporting fabrica métricas financieras
### 4. El informe global contiene otro modelo financiero (build_global_report_payload.py:394-616)
Mantiene defaults no gobernados: EUR, 100M revenue, 5k/h downtime, 2M fine, FinOps waste, 27h downtime, tail range 0.45-0.65 x ALE, OpEx 40%, fallback 250k, payback 6 meses, ROI 1x, valor protegido = cash waste + downtime + tail max.

### 5. asis_fair_chapter.py fabrica P90 y pérdida máxima
P90 = ALE × 2,5; MAX = P90 × 1,5; tier thresholds = media × 1,5 y × 0,5 (líneas 64-67, 405-430, 629-630, 722, 759).

### 6. Supuestos sin procedencia en payload_to_ast.py
Perimeter revenue = 100%, fuente inventada Gartner / ITIC Global Downtime Benchmark, sector impact factor = 40%, target maturity = score + 1.5, P90 = ALE x 2.2, recovery ceiling = 24h, risk tiers 15%/3%, coupling 1.5/1.2/1.0, alpha 0.70/0.40/0.20, productivity rate = 65/h, RTO fallback = LM x 0.85 o 3.5h.

### 7. El renderer global inventa madurez positiva
adapters/render_global_report_from_template.py:1751-1757 establece score = 4.0, band = "Managed", status_color = "green" para cualquier tower bottom line incompleto.

### 8. Split-brain de madurez
in_memory_asis_compiler.py recalibra madurez a partir de texto (líneas 1258-1272, 1354-1370, 1725-1728, 1874-1897).
payload_to_ast.py aplica reglas distintas: máximo 1.25/1.50 (763-772).

## P0 — Los tests protegen el comportamiento incorrecto
test_presentation_modules_do_not_calculate_financial_metrics_ast sólo prohíbe llamadas con seis nombres.
test_rfc084_zero_ale_prohibition_gate.py exige que nueve torres sin evidencia tengan ALE positivo y superior a 100.000.
"""

# Inspect relevant snippets from the presentation modules
snippets = []

p1 = REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"
if p1.is_file():
    text1 = p1.read_text(encoding="utf-8")
    lines1 = text1.splitlines()
    snippet1 = "\n".join(lines1[530:735])
    snippets.append(f"### SNIPPET 1: in_memory_asis_compiler.py:532-735 (derive_in_memory_fair_risks)\n```python\n{snippet1}\n```\n")

p2 = REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py"
if p2.is_file():
    text2 = p2.read_text(encoding="utf-8")
    lines2 = text2.splitlines()
    snippet2_1 = "\n".join(lines2[490:520])
    snippet2_2 = "\n".join(lines2[1430:1470])
    snippets.append(f"### SNIPPET 2: tomo_asis_ast_compiler.py (lines 490-520 and 1430-1470)\n```python\n{snippet2_1}\n...\n{snippet2_2}\n```\n")

p3 = REPO_ROOT / "src/assessment_engine/adapters/compilers/asis_fair_chapter.py"
if p3.is_file():
    text3 = p3.read_text(encoding="utf-8")
    lines3 = text3.splitlines()
    snippet3 = "\n".join(lines3[55:75])
    snippets.append(f"### SNIPPET 3: asis_fair_chapter.py (lines 55-75)\n```python\n{snippet3}\n```\n")

p4 = REPO_ROOT / "src/assessment_engine/application/build_global_report_payload.py"
if p4.is_file():
    text4 = p4.read_text(encoding="utf-8")
    lines4 = text4.splitlines()
    snippet4 = "\n".join(lines4[520:565])
    snippets.append(f"### SNIPPET 4: build_global_report_payload.py (lines 520-565)\n```python\n{snippet4}\n```\n")

FULL_SNIPPETS_PAYLOAD = "\n".join(snippets)

PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Fellow of the Open FAIR Institute, and Chief Actuarial Model Risk Examiner.

An external audit team has just submitted a scathing critique of our presentation and reporting layer on commit 41d4c2d:

--- BEGIN EXTERNAL AUDIT REPORT ---
{EXTERNAL_AUDIT_REPORT}
--- END EXTERNAL AUDIT REPORT ---

Here are excerpts directly from our codebase confirming the audit's cited sections:

{FULL_SNIPPETS_PAYLOAD}

YOUR MANDATE:
Perform an unflinching, mathematically rigorous, and forensic analysis of this critique.

Answer specifically:
1. Ground Truth Verification:
   - For each cited issue (P0 #1, P0 #2, P0 #3, P1 #4, P1 #5, P1 #6, P1 #7, P1 #8, P0 Tests), is the auditor telling the absolute technical truth based on the physical codebase?
   - Validate whether presentation compilers are indeed operating as a 'parallel business and actuarial engine'.
2. Root Cause Analysis:
   - Why do presentation modules contain `derive_in_memory_fair_risks()`, `ActuarialDowntimeCalibrator`, `EulerPortfolioAllocator`, and synthetic multipliers (`ALE * 2.5`)?
   - How does this violate the Separation of Concerns, Clean/Hexagonal Architecture, and SR 11-7 model governance?
3. Risks and Blast Radius of Proposed Remediation:
   - If we convert `derive_in_memory_fair_risks` to a passive mapper, make `payload_to_ast.py` and `tomo_asis_ast_compiler.py` read-only consumers, and eliminate fallback fabrication:
     * What could break in the existing 10 tower DOCX generation pipelines?
     * How should presentation DTOs (`PresentationTowerDTO`, `PresentationFindingDTO`, `PresentationPortfolioDTO`) be designed to supply all required rendering data without touching raw simulation engines?
4. Concrete Implementation Strategy:
   - Provide an exact, step-by-step architectural blueprint to completely purge all actuarial math, mutations, and synthetic fallbacks from `adapters/` and `compilers/`.
   - Specify the exact AST test rules that will permanently guard against regression.

Respond in 100% Technical English with supreme precision and zero sycophancy.
"""


def main() -> None:
    print(f"Submitting Presentation Audit Analysis to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_PRESENTATION_SPLIT_BRAIN_AUDIT_RULING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nReview written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:3000] + ("\n... [TRUNCATED]" if len(ruling) > 3000 else ""))


if __name__ == "__main__":
    main()
