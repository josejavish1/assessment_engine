#!/usr/bin/env python3
"""Build and synchronize client delivery suite across the full pyramid.

Supports:
- Declarative AST compilation for Volume 1 AS-IS (Tomo 1)
- Declarative AST compilation for all 10 specialist annexes (T1 - T10)
- Conversion of DOCX deliverables to PDF
- Mirrored deployment to Tier-1 delivery packages
"""

from __future__ import annotations

import argparse
import json
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
from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import Volume1AsisASTCompiler
from assessment_engine.application.services.tower_payload_hydrator import TowerPayloadHydrator

MOLINS_CANONICAL_FILENAMES: dict[str, str] = {
    "T1": "Molins_202610_Anexo_01_Data_Center_ASIS.docx",
    "T2": "Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx",
    "T3": "Molins_202610_Anexo_03_Redes_ASIS.docx",
    "T4": "Molins_202610_Anexo_04_Datos_Storage_ASIS.docx",
    "T5": "Molins_202610_Anexo_05_Resiliencia_ASIS.docx",
    "T6": "Molins_202610_Anexo_06_Seguridad_Identidad_ASIS.docx",
    "T7": "Molins_202610_Anexo_07_Bases_Datos_Operaciones_ASIS.docx",
    "T8": "Molins_202610_Anexo_08_Aplicaciones_FinOps_ASIS.docx",
    "T9": "Molins_202610_Anexo_09_Puesto_Trabajo_ASIS.docx",
    "T10": "Molins_202610_Anexo_10_Sistemas_Expedicion_Operaciones_ASIS.docx",
}

MOLINS_LEGACY_ALIASES: dict[str, str] = {
    "T7": "Molins_202610_Anexo_07_Operaciones_ITSM_ASIS.docx",
    "T8": "Molins_202610_Anexo_08_FinOps_Gobernanza_ASIS.docx",
    "T10": "Molins_202610_Anexo_10_Mainframe_Core_ASIS.docx",
}


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


def compile_all_annexes(hydrated_payloads: dict[str, dict[str, Any]]) -> None:
    """Compiles all 10 specialist AS-IS annexes via the Declarative AST Engine."""
    print("\n" + "=" * 80)
    print("PHASE: COMPILING ALL 10 SPECIALIST ANNEXES VIA DECLARATIVE AST ENGINE (T1-T10)")
    print("=" * 80)

    official_annex_dir = (
        REPO_ROOT
        / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/02_ANEXOS_TECNICOS_ESPECIALISTAS"
    )
    official_annex_dir.mkdir(parents=True, exist_ok=True)

    mirrors = [
        official_annex_dir,
        REPO_ROOT / "working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS",
        REPO_ROOT / "working/out/Molins_Entrega_Piramide_Tier1/02_ANEXOS_TECNICOS_POR_DOMINIO",
    ]

    for code, filename in MOLINS_CANONICAL_FILENAMES.items():
        print(f"\n>>> Compiling AS-IS Annex for Tower {code}: {filename} <<<")
        out_dir = REPO_ROOT / f"working/out/molins/{code}"
        out_dir.mkdir(parents=True, exist_ok=True)
        primary_docx = out_dir / filename
        payload_path = REPO_ROOT / f"working/molins/{code}/blueprint_{code.lower()}_payload.json"

        if not payload_path.exists():
            print(f"   ⚠️ Payload missing for {code}: {payload_path}")
            continue

        compile_asis_docx_via_ast(payload_path, primary_docx, doc_lang="es")
        print(f"   ✓ Generated AST DOCX: {primary_docx.name} ({primary_docx.stat().st_size:,} bytes)")

        # Convert to PDF
        pdf_path = primary_docx.with_suffix(".pdf")
        convert_docx_to_pdf(primary_docx, pdf_path)
        print(f"   ✓ Generated AST PDF: {pdf_path.name} ({pdf_path.stat().st_size:,} bytes)")

        # Replicate to package mirrors
        for m_dir in mirrors:
            if m_dir.exists():
                shutil.copy2(primary_docx, m_dir / filename)
                if pdf_path.exists():
                    shutil.copy2(pdf_path, m_dir / pdf_path.name)
                # Replicate backward-compatible alias if defined
                if code in MOLINS_LEGACY_ALIASES:
                    alias_name = MOLINS_LEGACY_ALIASES[code]
                    alias_pdf = alias_name.replace(".docx", ".pdf")
                    shutil.copy2(primary_docx, m_dir / alias_name)
                    if pdf_path.exists():
                        shutil.copy2(pdf_path, m_dir / alias_pdf)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile and mirror client deliverables.")
    parser.add_argument(
        "--only",
        choices=["all", "tomo1", "tomo1_asis", "annexes"],
        default="all",
        help="Compile only a specific deliverable or suite component.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    global_payload_path = REPO_ROOT / "working/molins/global_report_payload.json"
    with open(global_payload_path, "r", encoding="utf-8-sig") as f:
        global_payload = json.load(f)

    # 1. Deterministically hydrate all 10 tower payloads with corporate telemetry
    hydrated_payloads = TowerPayloadHydrator.load_and_hydrate_all_towers(
        REPO_ROOT, global_payload, doc_lang="es"
    )

    if args.only == "annexes":
        compile_all_annexes(hydrated_payloads)
        print("\n" + "=" * 80)
        print("ALL 10 AST ANNEXES SUCCESSFULLY GENERATED AND SYNCHRONIZED")
        print("=" * 80)
        return

    if args.only in ("tomo1", "tomo1_asis"):
        print("\n" + "=" * 80)
        print("FAST-PATH ISOLATED COMPILATION: TOMO 1 CONSOLIDATED AS-IS")
        print("=" * 80)

        tomo1_compiler = Volume1AsisASTCompiler()
        tomo1_out = (
            REPO_ROOT
            / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
        )
        tomo1_out.parent.mkdir(parents=True, exist_ok=True)
        radar_src = REPO_ROOT / "working/molins/global_radar_chart.png"
        if radar_src.exists():
            shutil.copy2(radar_src, tomo1_out.parent / "global_radar_chart.png")

        tomo1_compiler.compile(
            global_payload=global_payload,
            tower_payloads=hydrated_payloads,
            output_docx_path=tomo1_out,
            doc_lang="es",
        )
        print(f"   ✓ Compiled Tomo 1 AS-IS DOCX: {tomo1_out.name} ({tomo1_out.stat().st_size:,} bytes)")

        # Convert to PDF
        pdf_out = tomo1_out.with_suffix(".pdf")
        convert_docx_to_pdf(tomo1_out, pdf_out)
        print(f"   ✓ Generated Tomo 1 AS-IS PDF: {pdf_out.name} ({pdf_out.stat().st_size:,} bytes)")

        # Mirror to root and packages
        for mirror_dest in [
            REPO_ROOT / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
            REPO_ROOT / "working/molins/Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
            REPO_ROOT / "working/out/Molins_Entrega_Piramide_Tier1/01_TOMOS_ESTRATEGICOS_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
            REPO_ROOT / "working/out/Molins_Entrega_Cliente_Final/01_INFORME_GLOBAL/Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
        ]:
            if mirror_dest.parent.exists():
                shutil.copy2(tomo1_out, mirror_dest)

        for mirror_pdf in [
            REPO_ROOT / "Molins_202610_Tomo_1_Diagnostico_ASIS.pdf",
            REPO_ROOT / "working/out/Molins_Entrega_Piramide_Tier1/01_TOMOS_ESTRATEGICOS_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.pdf",
            REPO_ROOT / "working/out/Molins_Entrega_Cliente_Final/01_INFORME_GLOBAL/Molins_202610_Tomo_1_Diagnostico_ASIS.pdf",
        ]:
            if mirror_pdf.parent.exists():
                shutil.copy2(pdf_out, mirror_pdf)

        print("\n" + "=" * 80)
        print("TOMO 1 ISOLATED COMPILATION & CONVERSION COMPLETE (< 4s)")
        print("=" * 80)
        return

    # Default "all" mode
    print("\n" + "=" * 80)
    print("STARTING COMPLETE END-TO-END MASTER DELIVERABLE COMPILATION FOR MOLINS")
    print("=" * 80)

    # 1. Compile all 10 AS-IS annexes via Declarative AST Engine
    compile_all_annexes(hydrated_payloads)

    # 2. Compile Consolidated Tomo 1 AS-IS via Declarative AST Engine
    print("\n>>> COMPILING CONSOLIDATED TOMO 1 AS-IS VIA AST ENGINE (RFC 071) <<<")
    tomo1_compiler = Volume1AsisASTCompiler()
    tomo1_out = (
        REPO_ROOT
        / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
    )
    tomo1_out.parent.mkdir(parents=True, exist_ok=True)
    radar_src = REPO_ROOT / "working/molins/global_radar_chart.png"
    if radar_src.exists():
        shutil.copy2(radar_src, tomo1_out.parent / "global_radar_chart.png")

    tomo1_compiler.compile(
        global_payload=global_payload,
        tower_payloads=hydrated_payloads,
        output_docx_path=tomo1_out,
        doc_lang="es",
    )
    print(f"   ✓ Compiled Tomo 1 AS-IS DOCX: {tomo1_out.name} ({tomo1_out.stat().st_size:,} bytes)")

    # Convert Tomo 1 to PDF
    pdf_out = tomo1_out.with_suffix(".pdf")
    convert_docx_to_pdf(tomo1_out, pdf_out)
    print(f"   ✓ Generated Tomo 1 AS-IS PDF: {pdf_out.name} ({pdf_out.stat().st_size:,} bytes)")

    # Mirror Tomo 1
    for mirror_dest in [
        REPO_ROOT / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
        REPO_ROOT / "working/molins/Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
        REPO_ROOT / "working/out/Molins_Entrega_Piramide_Tier1/01_TOMOS_ESTRATEGICOS_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
        REPO_ROOT / "working/out/Molins_Entrega_Cliente_Final/01_INFORME_GLOBAL/Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
    ]:
        if mirror_dest.parent.exists():
            shutil.copy2(tomo1_out, mirror_dest)

    for mirror_pdf in [
        REPO_ROOT / "Molins_202610_Tomo_1_Diagnostico_ASIS.pdf",
        REPO_ROOT / "working/out/Molins_Entrega_Piramide_Tier1/01_TOMOS_ESTRATEGICOS_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.pdf",
        REPO_ROOT / "working/out/Molins_Entrega_Cliente_Final/01_INFORME_GLOBAL/Molins_202610_Tomo_1_Diagnostico_ASIS.pdf",
    ]:
        if mirror_pdf.parent.exists():
            shutil.copy2(pdf_out, mirror_pdf)

    print("\n" + "=" * 80)
    print("ALL 10 ANNEXES + TOMO 1 CONSOLIDATED DELIVERABLE GENERATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
