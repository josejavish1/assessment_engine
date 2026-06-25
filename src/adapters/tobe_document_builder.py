import glob
import json
import os
import sys
from pathlib import Path


def build_master_ast(working_dir: str, output_path: str):
    """Compile a master Abstract Syntax Tree (AST) from multiple source JSON files.

    Scans a specified working directory to discover and aggregate data from
    technology "tower" payloads and an optional global executive summary. The
    function searches for tower files matching the pattern `T*/blueprint_*_payload.json`
    and a single optional `global_tobe_executive_summary.json` file.

    For each tower, it calculates average maturity scores based on its constituent
    "pillars." The aggregated tower data and the global summary are then compiled
    into a single master AST object and serialized to a JSON file at the specified
    output path.

    The compilation process is robust to errors in individual files; if a JSON
    payload is malformed, it is skipped with a logged warning, and processing
    continues. However, if no valid tower payloads are found, the function
    terminates without generating an output file.

    Args:
        working_dir (str): The path to the root directory to scan. This directory
            is expected to contain subdirectories named 'T*' (e.g., 'T01', 'T02'),
            each holding a 'blueprint_*_payload.json' file.
        output_path (str): The file path where the compiled master AST will be
            written as a JSON file.

    Returns:
        None. The function writes the compiled AST directly to the filesystem.

    Raises:
        PermissionError: If the process lacks read permissions for `working_dir`
            or its contents, or write permissions for the directory containing
            `output_path`.
        IsADirectoryError: If `output_path` specifies an existing directory
            instead of a file.
    """
    print(f"📦 Iniciando Compilación del AST de Documento TO-BE en: {working_dir}")
    
    # Initiates the data aggregation process by fetching all tower-specific payloads. Each tower represents a distinct vertical or domain, forming the foundational data layer of the final Abstract Syntax Tree (AST).
    payloads = []
    search_pattern = os.path.join(working_dir, "T*", "blueprint_*_payload.json")
    
    for file_path in sorted(glob.glob(search_pattern)):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            try:
                data = json.load(f)
                payloads.append(data)
                print(f"   ├─ Cargada torre: {data.get('document_meta', {}).get('tower_name', 'TXX')}")
            except Exception as e:
                print(f"   ⚠️ Error leyendo payload {file_path}: {e}")
                
    if not payloads:
        print("❌ Error: No se encontraron payloads de torres para compilar el AST.")
        return
        
    client_name = payloads[0].get("document_meta", {}).get("client_name", "Cliente")
    
    # Fetches the global executive summary payload, which provides a cross-cutting, high-level synthesis of all underlying tower data.
    global_summary_path = os.path.join(working_dir, "global_tobe_executive_summary.json")
    global_summary = {}
    if os.path.exists(global_summary_path):
        with open(global_summary_path, 'r', encoding='utf-8-sig') as f:
            try:
                global_summary = json.load(f)
                print("   ├─ Cargado Sumario Ejecutivo Global")
            except Exception as e:
                print(f"   ⚠️ Error leyendo sumario ejecutivo: {e}")
    else:
        print("   ⚠️ Sumario ejecutivo global no encontrado. El AST se generará sin resumen general.")

    # Constructs the master Abstract Syntax Tree (AST) by integrating the tower-specific and executive summary payloads. This hierarchical data structure provides a canonical, unified representation of the entire assessment.
    master_ast = {
        "metadata": {
            "client_name": client_name,
            "document_type": "TO-BE_Master_Report",
            "version": "1.2.0",
            "compiled_at_utc": Path(working_dir).name
        },
        "global_summary": global_summary,
        "towers": []
    }
    
    for payload in payloads:
        tower_meta = payload.get("document_meta", {})
        tower_name = tower_meta.get("tower_name", "Torre Tecnológica")
        
        # Computes the aggregated average scores for each dimension of the maturity model. These metrics are essential for rendering the summary view.
        pil_scores = [p.get("score", 0.0) for p in payload.get("pillars_analysis", [])]
        t_scores = [p.get("target_score", 4.0) for p in payload.get("pillars_analysis", [])]
        avg_score = sum(pil_scores) / len(pil_scores) if pil_scores else 0.0
        avg_target = sum(t_scores) / len(t_scores) if t_scores else 4.0
        
        tower_data = {
            "tower_name": tower_name,
            "score": round(avg_score, 2),
            "target": round(avg_target, 2),
            "pillars": []
        }
        
        for pilar in payload.get("pillars_analysis", []):
            tobe_raw = pilar.get("target_architecture_tobe", {})
            
            p_data = {
                "pilar_name": pilar.get("pilar_name", "Pilar Desconocido"),
                "asis_description": pilar.get("asis_architecture_description", "No descripto."),
                "score": pilar.get("score", 0.0),
                "target_score": pilar.get("target_score", 4.0),
                "vision_3_years": tobe_raw.get("vision_3_years", tobe_raw.get("vision", "No definido.")),
                "vision_5_years": tobe_raw.get("vision_5_years", "No definido."),
                "levers_technology": tobe_raw.get("levers_technology", []),
                "levers_process": tobe_raw.get("levers_process", []),
                "levers_operation": tobe_raw.get("levers_operation", []),
                "expected_benefits": tobe_raw.get("expected_benefits", []),
                "cost_of_inaction_risks": tobe_raw.get("cost_of_inaction_risks", [])
            }
            tower_data["pillars"].append(p_data)
            
        master_ast["towers"].append(tower_data)

    # Serializes and persists the fully constructed master AST to the designated storage backend, ensuring its availability for downstream consumers and archival.
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(master_ast, indent=4, ensure_ascii=False), encoding="utf-8-sig")
    print(f"✅ AST de Documento TO-BE compilado con éxito en: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python tobe_document_builder.py <working_dir> <output_ast.json>")
        sys.exit(1)
    build_master_ast(sys.argv[1], sys.argv[2])
