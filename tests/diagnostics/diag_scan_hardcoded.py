import os
import re
from pathlib import Path

def scan_project():
    root_dir = Path("/home/jsanchhi/assessment_engine")
    
    # Directories to scan
    scan_dirs = ["src", "engine_config", "tests"]
    
    # File extensions to scan
    scan_exts = {".py", ".json", ".yaml", ".yml", ".md", ".sh"}
    
    # Patterns to look for (case-insensitive)
    patterns = {
        "CLIENT_NAMES": re.compile(r"\b(redeia|eurovision)\b", re.IGNORECASE),
        "SECTORS": re.compile(r"\b(energía|energy|retail|banca|finanzas|seguros|salud|hospital)\b", re.IGNORECASE),
        "CRITICAL": re.compile(r"\b(infraestructura crítica|critical infrastructure)\b", re.IGNORECASE)
    }
    
    findings = []
    
    for d in scan_dirs:
        target_dir = root_dir / d
        if not target_dir.exists():
            continue
            
        for filepath in target_dir.rglob("*"):
            if filepath.is_file() and filepath.suffix in scan_exts:
                # Skip known ingest scripts which naturally contain client names
                if filepath.name in ["ingest_redeia.py", "ingest_eurovision.py"]:
                    continue
                    
                try:
                    content = filepath.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    content = filepath.read_text(encoding="utf-8-sig", errors="ignore")
                    
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    for category, pattern in patterns.items():
                        matches = pattern.finditer(line)
                        for match in matches:
                            # Context context to see if it's a legitimate generic comment/variable or hardcoding
                            findings.append({
                                "file": str(filepath.relative_to(root_dir)),
                                "line_num": i + 1,
                                "category": category,
                                "match": match.group(0),
                                "line_text": line.strip()
                            })

    # Group and print findings
    print("="*80)
    print("🚀 AUDITORÍA MATEMÁTICA: ESCANEO DE HARDCODING (MULTI-TENANT)")
    print("="*80)
    
    if not findings:
        print("✅ EL CÓDIGO ESTÁ 100% LIMPIO. No se detectaron clientes ni sectores hardcodeados.")
        return
        
    current_file = ""
    for f in findings:
        if f["file"] != current_file:
            print(f"\n📁 Archivo: {f['file']}")
            current_file = f["file"]
        
        print(f"   Línea {f['line_num']} [{f['category']} - '{f['match']}']: {f['line_text']}")

if __name__ == "__main__":
    scan_project()