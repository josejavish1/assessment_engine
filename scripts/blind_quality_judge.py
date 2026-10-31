#!/usr/bin/env python3
"""Blind Quality Judge via gemini-4-argon: Molins T1 Baseline vs New CEGAR."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from docx import Document

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

base_doc = Document("working/out/molins_baseline_pre_argon/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx")
new_doc = Document("working/out/molins_post_argon/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx")

base_text = "\n".join([p.text.strip() for p in base_doc.paragraphs if p.text.strip()])[:6000]
new_text = "\n".join([p.text.strip() for p in new_doc.paragraphs if p.text.strip()])[:6000]

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

prompt = f"""
Actúa como Chief Technology Officer y Auditor de Infraestructura Tier-1.
Compara a ciegas estos dos extractos del Anexo Técnico AS-IS de la Torre 1 (Data Center) para el cliente industrial Molins.

DOCUMENTO A (Versión Anterior):
```text
{base_text}
```

DOCUMENTO B (Nueva Versión Post-Remediación / CEGAR):
```text
{new_text}
```

Responde con un análisis técnico conciso evaluando:
1. Densidad y precisión técnica (¿cuál tiene más rigor de ingeniería y menos relleno conversacional?).
2. Estructura y legibilidad ejecutiva (tablas vs párrafos).
3. Veredicto Final: ¿Ha MEJORADO, SE HA MANTENIDO o HA EMPEORADO? Justifica tu respuesta en 3 puntos clave.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print(response.text)
