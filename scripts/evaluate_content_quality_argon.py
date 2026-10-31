#!/usr/bin/env python3
"""Blind Content Quality Audit via gemini-4-argon: Baseline vs. New Generation."""

from __future__ import annotations

import sys
from pathlib import Path
from docx import Document

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

base_path = REPO_ROOT / "working/out/molins_baseline_pre_argon/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"
new_path = REPO_ROOT / "working/out/molins_post_argon/T1/Molins_202610_Anexo_01_Data_Center_ASIS_ES.docx"

doc_base = Document(str(base_path))
doc_new = Document(str(new_path))


def extract_all_text(doc: Document) -> str:
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for t in doc.tables:
        for r in t.rows:
            row_texts = [c.text.strip() for c in r.cells if c.text.strip()]
            if row_texts:
                paragraphs.append(" | ".join(row_texts))
    return "\n".join(paragraphs)


base_text = extract_all_text(doc_base)
new_text = extract_all_text(doc_new)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

prompt = f"""
Actúa como Chief Technology Officer (CTO) y Editor Técnico Principal de una consultora estratégica global (McKinsey / Gartner / Tier-1).
Tu objetivo es evaluar y comparar EXCLUSIVAMENTE EL CONTENIDO Y LA CALIDAD DEL TEXTO de dos versiones del Anexo Técnico AS-IS de la Torre 1 (Data Center) para la empresa industrial Molins (fábrica de cemento de Sant Vicenç dels Horts).

IGNORA los fallos visuales o de formato Word (como tablas o colores). Concéntrate 100% en el TEXTO, la ARGUMENTACIÓN, la INGENIERÍA y el VALOR ESTRATÉGICO para el lector (el CIO y el Comité de Dirección de Molins).

================================================================================
TEXTO A (Versión Original / Baseline del 30 de Octubre):
================================================================================
{base_text[:14000]}

================================================================================
TEXTO B (Nueva Versión Generada):
================================================================================
{new_text[:14000]}

================================================================================
INSTRUCCIONES DE EVALUACIÓN OBJETIVA:
Evalúa ambos textos en las siguientes dimensiones críticas:

1. PROFUNDIDAD TÉCNICA E IDENTIFICACIÓN DEL CONTEXTO REAL:
   - ¿Cuál de los dos textos describe mejor la realidad específica de Molins (nodos HPE SimpliVity, NetApp, Huawei, básculas de expedición, fibra de 500m entre salas gemelas, CRAH, desequilibrios de fase)?
   - ¿Cuál demuestra mayor competencia técnica de ingeniería?

2. NARRATIVA Y ELOICUENCIA ESTRATÉGICA:
   - ¿Cuál tiene un tono consultivo de mayor nivel?
   - ¿Cuál se lee de forma más persuasiva, articulada y profesional?
   - ¿Detectas repeticiones, frases genéricas o lenguaje robótico en alguno de ellos?

3. CREDIBILIDAD DEL ANÁLISIS DE RIESGOS Y PROYECTOS:
   - Compara las cifras de riesgo (8.434 € vs ~1.000.000 €). ¿Cuál de las dos narrativas explica mejor la justificación económica de las iniciativas?
   - ¿Son los proyectos propuestos creíbles y accionables para el negocio?

4. VEREDICTO FINAL CLARO Y SIN FILTROS:
   - Como CIO de Molins, ¿con qué TEXTO te quedarías para presentar a tu Consejo de Administración?
   - ¿Es el Texto B mejor que el Texto A, o el Texto A tenía una calidad de redacción superior? Responde con total franqueza técnica.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print(response.text)
