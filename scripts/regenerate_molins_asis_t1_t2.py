#!/usr/bin/env python3
"""Regenerate Molins Tower 1 and Tower 2 AS-IS Technical Deliverables (DOCX, PDF, and Portal page previews)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.adapters.compilers.payload_to_ast import compile_asis_docx_via_ast


def compile_and_export_tower(
    tower_code: str,
    payload_rel_path: str,
    output_docx_name: str,
) -> None:
    print(f"\n=======================================================")
    print(f"Compiling AS-IS Deliverables for Tower {tower_code}")
    print(f"=======================================================")

    payload_path = REPO_ROOT / payload_rel_path
    if not payload_path.exists():
        raise FileNotFoundError(f"Payload not found: {payload_path}")

    # Primary target directory
    out_dir = REPO_ROOT / f"working/out/molins/{tower_code}"
    out_dir.mkdir(parents=True, exist_ok=True)
    primary_docx = out_dir / output_docx_name

    # 1. Compile DOCX via Declarative AST Engine
    print(f"1. Compiling DOCX via AST Compiler Bridge -> {primary_docx.name}")
    compile_asis_docx_via_ast(payload_path, primary_docx, doc_lang="es")
    print(f"   ✓ DOCX generated: {primary_docx.stat().st_size:,} bytes")

    # 2. Replicate to official package mirrors and legacy working paths
    mirrors = [
        REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/02_ANEXOS_TECNICOS_ESPECIALISTAS",
        REPO_ROOT / "working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS",
        REPO_ROOT / "working/out/Molins_Entrega_Piramide_Tier1/02_ANEXOS_TECNICOS_POR_DOMINIO",
    ]
    for mirror_dir in mirrors:
        if mirror_dir.exists():
            dest = mirror_dir / output_docx_name
            shutil.copy2(primary_docx, dest)
            print(f"   ✓ Mirrored DOCX to: {mirror_dir.name}/{output_docx_name}")

    # Mirror to local working/molins directory and November 202611 variants to prevent stale file reads
    legacy_dir = REPO_ROOT / f"working/molins/{tower_code}"
    if legacy_dir.exists():
        for alt_name in [
            output_docx_name,
            output_docx_name.replace("202610", "202611"),
            f"AS-IS_Anexo_Tecnico_{tower_code}.docx",
            f"Diagnostico_ASIS_{tower_code}_molins.docx",
        ]:
            alt_dest = legacy_dir / alt_name
            shutil.copy2(primary_docx, alt_dest)
        # Also mirror 202611 to out_dir
        shutil.copy2(primary_docx, out_dir / output_docx_name.replace("202610", "202611"))

    # 3. Convert DOCX to PDF via LibreOffice headless
    print(f"2. Converting DOCX to PDF via LibreOffice headless...")
    pdf_cmd = [
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        str(primary_docx),
        "--outdir",
        str(out_dir),
    ]
    subprocess.run(pdf_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pdf_name = output_docx_name.replace(".docx", ".pdf")
    primary_pdf = out_dir / pdf_name
    if not primary_pdf.exists():
        raise RuntimeError(f"PDF generation failed: {primary_pdf}")
    print(f"   ✓ PDF generated: {primary_pdf.stat().st_size:,} bytes")

    # Mirror PDF to official package if directory exists
    for mirror_dir in mirrors:
        if mirror_dir.exists():
            dest_pdf = mirror_dir / pdf_name
            shutil.copy2(primary_pdf, dest_pdf)
            print(f"   ✓ Mirrored PDF to: {mirror_dir.name}/{pdf_name}")

    if legacy_dir.exists():
        shutil.copy2(primary_pdf, legacy_dir / pdf_name)
        shutil.copy2(primary_pdf, legacy_dir / pdf_name.replace("202610", "202611"))
    shutil.copy2(primary_pdf, out_dir / pdf_name.replace("202610", "202611"))

    # 4. Generate Portal PNG page previews via pdftoppm
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    # Remove existing PNG pages
    for old_png in pages_dir.glob("page-*.png"):
        old_png.unlink()

    print(f"3. Rendering 150 DPI PNG page previews for web portal...")
    prefix = str(pages_dir / "page")
    ppm_cmd = [
        "pdftoppm",
        "-png",
        "-r",
        "150",
        str(primary_pdf),
        prefix,
    ]
    subprocess.run(ppm_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    generated_pages = sorted(pages_dir.glob("page-*.png"))
    print(f"   ✓ Generated {len(generated_pages)} portal preview images in {pages_dir.name}/")


def main() -> None:
    # Tower 1: Data Center Facilities & Energy
    compile_and_export_tower(
        tower_code="T1",
        payload_rel_path="working/molins/T1/blueprint_t1_payload.json",
        output_docx_name="Molins_202610_Anexo_01_Data_Center_ASIS.docx",
    )

    # Tower 2: Hybrid Compute & Infrastructure
    compile_and_export_tower(
        tower_code="T2",
        payload_rel_path="working/molins/T2/blueprint_t2_payload.json",
        output_docx_name="Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx",
    )

    print("\n" + "=" * 60)
    print("ALL MOLINS AS-IS DELIVERABLES REGENERATED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
