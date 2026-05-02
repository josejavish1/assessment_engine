from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

LIVE_PYTHON_PREFIXES = ("src/assessment_engine/", "tests/")

# Marcadores estructurales que DEBEN estar presentes en archivos nuevos
# para confirmar que provienen de una plantilla Golden Path.
GOLDEN_PATH_MARKERS = [
    "# --- START OF BUSINESS LOGIC ---",  # Para workers y endpoints
    "# --- ARRANGE ---",                  # Para tests
]

def git_added_files(repo_root: Path, base_sha: str | None, head_sha: str | None) -> list[str]:
    """Obtiene los archivos Python recién añadidos en la PR (estado A)."""
    if not base_sha or not head_sha:
        return []
    
    result = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-status", base_sha, head_sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Could not compute changed files.")

    added_files = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[0].startswith("A"):
            added_files.append(parts[1].strip())

    return added_files

def check_golden_path_compliance(repo_root: Path, target_files: list[str]) -> list[str]:
    violations = []
    for rel_path in target_files:
        if not rel_path.endswith(".py") or rel_path.endswith("__init__.py"):
            continue
        if not rel_path.startswith(LIVE_PYTHON_PREFIXES):
            continue
            
        file_path = repo_root / rel_path
        if not file_path.is_file():
            continue
            
        content = file_path.read_text(encoding="utf-8")
        
        # Escape hatch (Opt-out explícito): Si un archivo es un helper, modelo o constante,
        # puede eludir la regla añadiendo este pragma, justificando que no es un servicio/worker.
        if "golden-path: ignore" in content.lower():
            continue
        
        has_marker = any(marker in content for marker in GOLDEN_PATH_MARKERS)
        if not has_marker:
            violations.append(rel_path)
            
    return violations

def main() -> int:
    parser = argparse.ArgumentParser(description="Architectural Fitness Function: Golden Paths")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--base-sha", type=str)
    parser.add_argument("--head-sha", type=str)
    
    args, unknown = parser.parse_known_args()
    
    if not args.base_sha or not args.head_sha:
        # Modo local para el orquestador: verificar contra origin/main
        args.base_sha = "origin/main"
        args.head_sha = "HEAD"

    try:
        added_files = git_added_files(args.repo_root, args.base_sha, args.head_sha)
        violations = check_golden_path_compliance(args.repo_root, added_files)
        
        if violations:
            print("\n[ERROR] FITNESS FUNCTION FAILED: Golden Path violation detected.")
            print("Los siguientes archivos nuevos no parecen usar las plantillas oficiales:")
            for v in violations:
                print(f"  - {v}")
            print("\nAcción requerida: NUNCA crees archivos Python desde cero para lógica de negocio o tests.")
            print("DEBES usar las plantillas en 'templates/golden_paths/' que contienen los bloques")
            print("estructurales requeridos (ej. '# --- START OF BUSINESS LOGIC ---' o '# --- ARRANGE ---').\n")
            return 1
            
        if added_files:
            print(f"Architectural fitness check passed. {len(added_files)} new files comply with Golden Paths.")
        return 0
        
    except Exception as e:
        print(f"Error executing fitness function: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
