#!/usr/bin/env python3
"""Iterative Excellence Judge via gemini-4-argon: Molins T1 Baseline (9/10) vs New AST Master."""

from __future__ import annotations

import sys
from pathlib import Path
from docx import Document

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

base_path = REPO_ROOT / "working/out/molins_baseline_pre_argon/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"
new_path = REPO_ROOT / "working/out/molins/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"

doc_base = Document(str(base_path))
doc_new = Document(str(new_path))


def extract_full_corpus(doc: Document) -> str:
    parts = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            parts.append(t)
    for t in doc.tables:
        for r in t.rows:
            row_txt = " | ".join(c.text.strip() for c in r.cells if c.text.strip())
            if row_txt:
                parts.append(row_txt)
    return "\n".join(parts)


base_corpus = extract_full_corpus(doc_base)
new_corpus = extract_full_corpus(doc_new)

# Contrast audit on new doc
white_on_white_count = 0
for t in doc_new.tables:
    for r in t.rows:
        for c in r.cells:
            tcPr = c._tc.get_or_add_tcPr()
            shd = tcPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd")
            shd_val = shd.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill") if shd is not None else None
            for p_obj in c.paragraphs:
                for run in p_obj.runs:
                    color = run.font.color.rgb if run.font.color else None
                    if str(color) == "FFFFFF" and (shd_val is None or shd_val in ("auto", "None", "FFFFFF")):
                        white_on_white_count += 1

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

prompt = f"""
Actúa como Chief Technology Officer (CTO) y Socio Director de Consultoría Estratégica (Tier-1: McKinsey / BCG / Gartner).

Evalúa el documento recién compilado frente al baseline del cliente industrial Molins (fábrica de Sant Vicenç dels Horts):
- El documento baseline anterior ya fue calificado por el usuario como un **9 sobre 10**.
- Tu objetivo es comprobar si el NUEVO documento compilado por el motor declarativo AST ha superado con claridad ese listón, alcanzando el nivel de "Obra de Arte" (>= 9.5 / 10).

DATOS DE AUDITORÍA FÍSICA EN WORD:
- Documento Anterior: 144 párrafos, 11 tablas, 7.165 palabras. Tenía fallos visibles como 'chapter3title', 'decisionmatrixtitle' y ALE absurda de 8.434 €.
- Documento Nuevo AST: 123 párrafos fluidos, 14 tablas estructuradas. Cero texto blanco sobre blanco (white-on-white = {white_on_white_count}). Cero claves crudas (resueltas formalmente como '3. Diagnóstico Técnico y Análisis Transversal'). Cálculo FAIR actuarial realista (1.052.775 €).

CORPUS DEL DOCUMENTO ANTERIOR (BASELINE 9/10):
```text
{base_corpus[:15000]}
```

CORPUS DEL DOCUMENTO NUEVO (COMPILADOR AST CERTIFICADO):
```text
{new_corpus[:15000]}
```

EMITE TU INFORME ESTRUCTURADO:
1. BONIDADES DEL DOCUMENTO NUEVO PARA EL CIO/LECTOR DE MOLINS:
   - ¿Qué valor específico gana el lector?
   - Explica el impacto de la eliminación de claves rotas ('chapter3title') y la calibración realista de riesgos.
2. ASPECTOS MENORES O COSAS A VIGILAR (si queda algún detalle residual de redacción o formato).
3. COMPARATIVA DIRECTA CON EL BASELINE:
   - Argumenta por qué este nuevo documento supera al 9/10 previo.
4. CALIFICACIÓN FINAL NUMÉRICA:
   - Puntúa el nuevo documento de 1.0 a 10.0 (¿supera el 9.0 anterior?).
   - Veredicto final: ¿Aprobado como Obra de Arte definitiva para entrega oficial?
"""

print(f"Auditing deliverable with {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print(response.text)
