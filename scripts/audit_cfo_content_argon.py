#!/usr/bin/env python3
"""Hostile CFO Content Audit via gemini-4-argon."""

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

doc_path = REPO_ROOT / "working/out/molins/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"
doc = Document(str(doc_path))

parts = []
for p in doc.paragraphs:
    if p.text.strip():
        parts.append(p.text.strip())
for t in doc.tables:
    for r in t.rows:
        row_txt = " | ".join(c.text.strip() for c in r.cells if c.text.strip())
        if row_txt:
            parts.append(row_txt)
corpus = "\n".join(parts)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

prompt = f"""
Actúa como el CFO (Director Financiero) de Molins, conocido por ser implacable, escéptico y alérgico a la "cháchara de consultores". También actúa como Auditor Principal de McKinsey.

Evalúa el corpus completo del nuevo documento AS-IS (Data Center T1) comprobando estrictamente estas 5 métricas de perfección de contenido:
1. Densidad de Valor (Zero-Fluff): ¿Cada párrafo aporta un dato técnico de planta, un activo concreto o una consecuencia de negocio? ¿Hay frases vacías de relleno?
2. Coeficiente de No-Repetición: ¿La información progresa sin clonarse? ¿Se repiten frases en el resumen y luego en las fichas de riesgos?
3. Trazabilidad Causal del Riesgo: ¿Los 14 riesgos (especialmente el RVS05 de climatización) desglosan su ALE en: Frecuencia (TEF) x Horas de Parada x Coste/hora (lucro cesante) + Daños Secundarios?
4. Palanca Presupuestaria (ROI): ¿Está clara la inversión necesaria (CAPEX) y el retorno (reducción de ALE)?
5. Test del CFO Hostil: ¿Te crees los números? ¿Puedes defenderlos ante el Comité de Dirección sin que te desmonten el caso de negocio?

CORPUS COMPLETO DEL DOCUMENTO ({len(parts)} elementos):
```text
{corpus}
```

EMITE TU INFORME:
1. Veredicto por cada una de las 5 métricas (Aprobado/Suspenso).
2. Si hay fallos, enumera exactamente qué falla y cómo solucionarlo en la próxima iteración.
3. Si el contenido ha alcanzado el 10.0 (perfecto y defendible), confirma "APROBADO PARA COMITÉ DE DIRECCIÓN".
4. Cierra con un pareado que resuma el veredicto del CFO.
"""

print(f"Auditing CFO-Grade content with {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)
print(response.text)
