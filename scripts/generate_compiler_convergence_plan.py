#!/usr/bin/env python3
"""Generates the formal RFC-026 AST Compiler Convergence Plan via gemini-4-argon."""

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


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    prompt = """
Actúa como Principal Systems Architect y Staff Software Engineer (Google Tier-1 / Palantir Infrastructure).

OBJETIVO:
Diseña el plan formal de arquitectura y desarrollo para la eliminación definitiva del Split-Brain #1 en el Assessment Engine:
"RFC-026: AST Compiler Convergence & Zero-Entropy Document Synthesis".

CONTEXTO Y PROBLEMA ACTUAL:
1. Coexisten dos motores incompatibles para compilar anexos de torres:
   - Motor A (Obsoleto / Roto): `render_tower_annex_from_template.py`, que manipula una plantilla binaria .docx buscando etiquetas {{TAG}}, encajonando texto en 17 micro-tablas y produciendo el bug de texto blanco sobre blanco (#FFFFFF sin sombreado).
   - Motor B (Moderno / AST Declarativo): `payload_to_ast.py` -> `DocxCompiler`, que implementa un árbol de sintaxis abstracta (AST) de 5 capítulos, generando el libro técnico completo de 144 párrafos y 11 tablas con diseño de consultoría de élite.
2. `mcp_server.py` seguía apuntando al Motor A, lo que provocaba que llamadas automáticas generaran el documento roto.
3. Faltan registrar en `engine_config/locales.json` tres claves de títulos (`chapter_3_diagnosis_cross_cutting`, `diagnosis_performance_matrix_title`, `decision_matrix_title`), causando que aparezcan cadenas como `chapter3title`.
4. El nuevo motor CEGAR genera contenido técnico extraordinario (HPE SimpliVity, NetApp, CRAH, canteras, 1,05M € de ALE), pero necesita inyectarse en el libro AST completo para que el lector humano (el CIO de Molins) tenga la historia, la prosa fluida y la explicación de cada cifra.

ESTRUCTURA OBLIGATORIA DEL PLAN RFC-026:
1. Executive Summary & Problem Formalization (con justificación teórica y referencias a LLVM Multi-Pass Compilers y GoF Visitor Pattern).
2. The 4 Non-Negotiable Architectural Invariants (Zero Split-Brain, Contrast Guarantee, Declarative i18n, Pure Clean Architecture).
3. Detailed 4-Step Surgical Implementation Roadmap:
   - PR-1: Declarative i18n Resolution (Locales registration for all missing keys).
   - PR-2: DocxCompiler AST Invariant Hardening (Physical rule prohibiting white text on non-dark background).
   - PR-3: Single Source of Truth Cutover in MCP Server & Facade (Deprecate imperative template rendering).
   - PR-4: Architectural Fitness Gate (`test_no_binary_template_split_brain.py`) & Molins Golden Master Verification.
4. Exact Class & Function Signatures for all modifications.
5. Definition of Done & Success Metrics.

El documento debe estar escrito en 100% Technical English, con formato markdown exhaustivo, riguroso y listo para producción.
"""

    print(f"Generating RFC-026 Architectural Plan via {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_path = REPO_ROOT / "docs" / "architecture" / "RFC_026_AST_COMPILER_CONVERGENCE_PLAN.md"
    out_path.write_text(response.text, encoding="utf-8")
    print(f"Plan formal generado con éxito en: {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
