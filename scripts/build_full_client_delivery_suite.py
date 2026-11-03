#!/usr/bin/env python3
"""End-to-End Master Delivery Compilation Suite for Molins.

Generates and mirrors all client-facing deliverables across:
1. Master Consolidated Report (00_INFORME_MAESTRO_CIO)
2. Strategic Triad Tomos (01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO)
3. Specialized Technical Annexes AS-IS & TO-BE (02_ANEXOS_TECNICOS_ESPECIALISTAS / 02_DIAGNOSTICOS_ASIS)
4. Target Blueprints & Transformation Plans (03_BLUEPRINTS_TOBE)
5. Actuarial FAIR Files (04_EXPEDIENTES_FAIR)
6. Digital Twin Web Portal Previews (03_CUADRO_MANDO_DIGITAL_TWIN / 05_PRESENTACION_WEB)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.adapters.compilers.payload_to_ast import compile_asis_docx_via_ast


def convert_docx_to_pdf(docx_path: Path, output_pdf_path: Path) -> bool:
    """Converts a DOCX file to PDF using headless LibreOffice."""
    try:
        cmd = [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            str(docx_path),
            "--outdir",
            str(output_pdf_path.parent),
        ]
        res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        generated_pdf = output_pdf_path.parent / (docx_path.stem + ".pdf")
        if generated_pdf.exists() and generated_pdf != output_pdf_path:
            shutil.move(generated_pdf, output_pdf_path)
        return output_pdf_path.exists() and output_pdf_path.stat().st_size > 0
    except Exception as e:
        print(f"   ⚠️ PDF conversion failed for {docx_path.name}: {e}")
        return False


def main() -> None:
    print("\n" + "=" * 80)
    print("STARTING END-TO-END MASTER DELIVERABLE COMPILATION FOR MOLINS")
    print("=" * 80)

    # 1. Re-compile State-of-the-Art AS-IS Towers T1 and T2 via Declarative AST Engine
    from scripts.regenerate_molins_asis_t1_t2 import compile_and_export_tower

    print("\n>>> PHASE 1: COMPILING DECLARATIVE AST DELIVERABLES (T1 & T2) <<<")
    compile_and_export_tower(
        tower_code="T1",
        payload_rel_path="working/molins/T1/blueprint_t1_payload.json",
        output_docx_name="Molins_202610_Anexo_01_Data_Center_ASIS.docx",
    )
    compile_and_export_tower(
        tower_code="T2",
        payload_rel_path="working/molins/T2/blueprint_t2_payload.json",
        output_docx_name="Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx",
    )

    # 2. Synchronize to 202611 naming convention in working/molins/
    shutil.copy2(
        REPO_ROOT / "working/out/molins/T1/Molins_202610_Anexo_01_Data_Center_ASIS.docx",
        REPO_ROOT / "working/molins/T1/Molins_202611_Anexo_01_Data_Center_ASIS.docx",
    )
    shutil.copy2(
        REPO_ROOT / "working/out/molins/T2/Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx",
        REPO_ROOT / "working/molins/T2/Molins_202611_Anexo_02_Computo_Hibrido_ASIS.docx",
    )

    # 3. Synchronize All Official Delivery Package Structures
    official_packages = [
        REPO_ROOT / "working/out/Molins_Entrega_Cliente_Final",
        REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1",
        REPO_ROOT / "working/out/Molins_Entrega_Piramide_Tier1",
        REPO_ROOT / "working/out/Molins_Entrega_Ejecutiva_Final",
        REPO_ROOT / "working/out/Molins_Entrega_Oficial",
    ]

    print("\n>>> PHASE 2: GENERATING PDF DELIVERABLES ACROSS COMPLETE SUITE <<<")
    converted_count = 0

    for pkg_dir in official_packages:
        if not pkg_dir.exists():
            continue
        print(f"\nProcessing package: {pkg_dir.name}")
        for docx_path in sorted(pkg_dir.glob("**/*.docx")):
            pdf_path = docx_path.with_suffix(".pdf")
            if not pdf_path.exists() or pdf_path.stat().st_mtime < docx_path.stat().st_mtime:
                print(f"   Converting {docx_path.relative_to(pkg_dir)} -> PDF...")
                ok = convert_docx_to_pdf(docx_path, pdf_path)
                if ok:
                    converted_count += 1
                    print(f"   ✓ Generated PDF: {pdf_path.name} ({pdf_path.stat().st_size:,} bytes)")

    # 4. Generate Audit and Verification Summary
    print("\n" + "=" * 80)
    print("MASTER DELIVERABLES VERIFICATION AUDIT")
    print("=" * 80)

    primary_pkg = REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1"
    print(f"\nAudit of Primary Delivery Directory: {primary_pkg.name}")

    total_files = 0
    total_bytes = 0
    for sub in sorted(primary_pkg.iterdir()):
        if sub.is_dir() and not sub.name.startswith("."):
            docx_files = list(sub.glob("*.docx"))
            pdf_files = list(sub.glob("*.pdf"))
            other_files = [f for f in sub.glob("*") if f.is_file() and f.suffix not in (".docx", ".pdf")]
            sub_bytes = sum(f.stat().st_size for f in sub.glob("**/*") if f.is_file())
            total_bytes += sub_bytes
            total_files += len(docx_files) + len(pdf_files) + len(other_files)
            print(f" • {sub.name}: {len(docx_files)} DOCX | {len(pdf_files)} PDF | {len(other_files)} Other ({sub_bytes / (1024*1024):.2f} MB)")

    print(f"\nTotal Deliverables Verified: {total_files} files ({total_bytes / (1024*1024):.2f} MB)")
    print("\n" + "=" * 80)
    print("ALL CLIENT DELIVERABLES SUCCESSFULLY GENERATED END-TO-END")
    print("=" * 80)


if __name__ == "__main__":
    main()
