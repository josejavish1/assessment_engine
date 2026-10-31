#!/usr/bin/env python3
"""Blind Reader Comparison via gemini-4-argon: What a human reader actually sees in Word."""

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

doc_base = Document(str(REPO_ROOT / "working/out/molins_baseline_pre_argon/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"))
doc_new = Document(str(REPO_ROOT / "working/out/molins/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx"))

# Extract visual defects: White on White text
white_on_white_count = 0
for t in doc_new.tables:
    for r in t.rows:
        for c in r.cells:
            tcPr = c._tc.get_or_add_tcPr()
            shd = tcPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd")
            shd_val = shd.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill") if shd is not None else None
            for p in c.paragraphs:
                for run in p.runs:
                    color = run.font.color.rgb if run.font.color else None
                    if str(color) == "FFFFFF" and (shd_val is None or shd_val in ("auto", "None", "FFFFFF")):
                        white_on_white_count += 1

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

base_text_sample = "\n".join([p.text.strip() for p in doc_base.paragraphs if p.text.strip()][:50])
new_text_sample = "\n".join([p.text.strip() for p in doc_new.paragraphs if p.text.strip()][:50])

prompt = f"""
Actúa como un Auditor de Calidad Documental y Lector Ejecutivo (CIO/Director de IT de Molins).
Analiza qué ve EXACTAMENTE un humano cuando abre estos dos archivos en Microsoft Word.

HALLAZGO TÉCNICO FORENSE DETECTADO EN EL DOCUMENTO NUEVO:
- Existen exactamente {white_on_white_count} elementos de texto formateados con color de fuente BLANCO (#FFFFFF) sobre fondo BLANCO/TRANSPARENTE (shading=None). Es decir, en pantalla ese texto es LITERALLY INVISIBLE a menos que el usuario lo seleccione con el ratón.
- En el documento nuevo, casi todo el texto se ha encajonado en 17 tablas pequeñas con bordes cortados, en lugar de párrafos continuos y elegantes de informe de consultoría.
- El documento base anterior tenía 144 párrafos y 11 tablas con una maquetación de libro/anexo técnico (100% legible, fondos contrastados, jerarquía visual limpia).

CONTENIDO DEL DOCUMENTO BASE (ANTERIOR):
```text
{base_text_sample}
```

CONTENIDO DEL DOCUMENTO NUEVO (ACTUAL):
```text
{new_text_sample}
```

Dime con total franqueza y severidad:
1. ¿Qué experiencia tiene el lector al abrir el documento nuevo en Word? Detalla TODOS los fallos visuales, de legibilidad, contraste y contenido.
2. Compara ambos documentos desde los ojos del cliente: ¿cuál transmite profesionalidad de Tier-1 y cuál parece un documento roto/defectuoso?
3. Diagnóstico de qué ha fallado en la plantilla/renderizador y qué hay que hacer para recuperar el documento perfecto que le gustaba al usuario.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print(response.text)
