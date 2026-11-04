#!/usr/bin/env python3
"""Consult gemini-4-argon on eradicating the T1/T2 vs T3-T10 split-brain across the delivery suite."""

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
Role: Principal Enterprise Systems Architect, Lead Diligence Director at Gartner / McKinsey, and Global Multi-Tenant Framework Ontologist.

EMERGENCY PROBLEM STATEMENT:
The user has discovered a severe, unacceptable architectural split-brain in the deliverables suite:
"He detectado algo gravísimo: las torres 1 y 2 son totalmente diferentes al resto de torres. Hay un split brain gigante. Las torres 3 a 10 son el modelo que se supone que estaba erradicado, ¿qué ha pasado?"

FORENSIC AUDIT OF WHAT HAPPENED:
1. In `working/out/Molins_Entrega_Oficial_Piramide_Tier1/02_ANEXOS_TECNICOS_ESPECIALISTAS/`:
   - Towers 1 and 2 (`Anexo_01_Data_Center_ASIS.docx` and `Anexo_02_Computo_Hibrido_ASIS.docx`) were compiled using the new Declarative AST Engine (`compile_asis_docx_via_ast`) and have file sizes of ~115 KB (modern, FNMT CERES typography, CMMI maturity scales, clean AST architecture).
   - Towers 3 to 10 (`Anexo_03` through `Anexo_10`) are legacy artifacts dated OCTOBER 30 with file sizes of ~300 KB (old template injection / markdown compiler that was supposed to be completely eradicated!).
2. In `scripts/build_full_client_delivery_suite.py`:
   - Only Towers 1 and 2 were invoked:
     `compile_and_export_tower(tower_code="T1", ...)`
     `compile_and_export_tower(tower_code="T2", ...)`
   - Towers 3 to 10 were NEVER invoked because their raw blueprint payloads in `working/out/molins_baseline_pre_rebuild/T3..T10` lacked `financial_telemetry` / `annual_revenue`, causing `TelemetryResolutionError` in `downtime_calibrator.py`.
3. In Tomo 1 (Consolidated AS-IS Diagnostic):
   - `build_full_client_delivery_suite.py` passed only `tower_payloads = {"T1": t1_payload, "T2": t2_payload}`!
   - Consequently, in Chapter 4, T1 and T2 had live blueprint telemetry while T3 to T10 fell back to static localized catalog stubs.

NON-NEGOTIABLE REQUIREMENTS FOR RFC 071:
- 100% Declarative AST Engine Across All 10 Towers: Every single technical annex (Anexos 01 to 10) must be compiled using `compile_asis_docx_via_ast`, completely purging the October 30 legacy artifacts.
- Universal Multi-Tenant Telemetry Hydration: Create a clean domain/application pipeline that ensures all N tower payloads (T1 to T10) automatically inherit tenant-level financial telemetry (`annual_revenue`, `downtime_rate`, `currency`, `client_name`) from `global_payload` so `downtime_calibrator.py` never fails on any tower for any client worldwide.
- Full Tomo 1 Homogeneity: Tomo 1 must load all 10 tower payloads into `tower_payloads = {f"T{i}": ... for i in 1..10}`, ensuring 100% symmetry across all 10 diagnostic sections in Chapter 4.
- 100% Technical English Codebase: Zero Spanish in Python code, docstrings, or variables.
- CLI Modularity: Ensure `scripts/build_full_client_delivery_suite.py` supports:
  * `--only tomo1` (compiles strictly Tomo 1 in <4s)
  * `--only annexes` (compiles all 10 AST annexes in parallel)
  * `--all` (compiles full delivery suite end-to-end)

DELIVERABLES IN RFC 071:
1. Root Cause Analysis of the Split-Brain.
2. Architecture of the Universal Payload Hydrator & All-10-Tower AST Compiler.
3. Step-by-Step Implementation and Verification Plan.
"""

    print(f"Consulting {model_name} on RFC 071 split-brain eradication...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_071_ALL_10_TOWERS_AST_UNIFICATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated RFC 071 specification: {out_file}")


if __name__ == "__main__":
    main()
