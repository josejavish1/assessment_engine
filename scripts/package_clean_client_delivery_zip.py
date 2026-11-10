#!/usr/bin/env python3
"""
Packages the official, certified Word deliverables for Cementos Molins into a clean ZIP archive.
Enforces the Zero-PDF invariant: only verified DOCX deliverables are included.
"""

import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIR = REPO_ROOT / "working/out/Molins_Entrega_Cliente_Final"
OUTPUT_ZIP = REPO_ROOT / "Molins_202610_Entrega_Cliente_DOCX.zip"

FILES_TO_PACK = [
    # 1. Tomo 1 Consolidado
    ("01_DIAGNOSTICO_GLOBAL/Molins_202610_Tomo_1_Diagnostico_ASIS.docx", 
     SOURCE_DIR / "01_DIAGNOSTICO_GLOBAL/Molins_202610_Tomo_1_Diagnostico_ASIS.docx"),
    
    # 2. Los 10 Anexos de Especialidad AS-IS
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_01_Data_Center_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_01_Data_Center_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_03_Redes_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_03_Redes_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_04_Datos_Storage_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_04_Datos_Storage_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_05_Resiliencia_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_05_Resiliencia_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_06_Seguridad_Identidad_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_06_Seguridad_Identidad_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_07_Operaciones_ITSM_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_07_Operaciones_ITSM_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_08_FinOps_Gobernanza_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_08_FinOps_Gobernanza_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_09_Puesto_Trabajo_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_09_Puesto_Trabajo_ASIS.docx"),
    ("02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_10_Sistemas_Expedicion_Operaciones_ASIS.docx",
     SOURCE_DIR / "02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_10_Sistemas_Expedicion_Operaciones_ASIS.docx"),
]

def main():
    print(f"Creando paquete ZIP limpio en: {OUTPUT_ZIP}...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for arcname, src_path in FILES_TO_PACK:
            if not src_path.exists():
                raise FileNotFoundError(f"Missing required file: {src_path}")
            size_kb = src_path.stat().st_size / 1024
            print(f"  + [{size_kb:.1f} KB] {arcname}")
            z.write(src_path, arcname=arcname)

    total_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"\n✓ Archivo ZIP generado con éxito: {OUTPUT_ZIP} ({total_mb:.2f} MB)")
    print(f"  Total documentos DOCX empaquetados: {len(FILES_TO_PACK)}")

if __name__ == "__main__":
    main()
