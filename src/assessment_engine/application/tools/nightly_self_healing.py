# golden-path: ignore
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from assessment_engine.application.tools import (
    validate_documentation_governance as governance,
)

FENCED_BLOCK_RE = re.compile(
    r"```(?:bash|sh|shell|console|python)?\n(.*?)\n```", re.DOTALL
)


def update_front_matter_status_to_needs_review(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return

    front_matter_lines = parts[1].splitlines()
    new_fm_lines = []
    for line in front_matter_lines:
        if line.strip().startswith("status:"):
            new_fm_lines.append("status: Needs Review")
        else:
            new_fm_lines.append(line)

    parts[1] = "\n".join(new_fm_lines) + "\n"
    path.write_text("---\n".join(parts), encoding="utf-8")
    print(
        f"  [DECAY] Modificado front matter del archivo físico a 'Needs Review': {path}"
    )


def update_map_status_to_needs_review(map_path: Path, doc_path: str) -> None:
    text = map_path.read_text(encoding="utf-8")
    escaped_doc_path = re.escape(doc_path)
    pattern = re.compile(
        rf"(- path:\s+{escaped_doc_path}\b.*?)(?=\n- path:|\Z)", re.DOTALL
    )

    match = pattern.search(text)
    if match:
        block = match.group(1)
        new_block = re.sub(r"(\n\s+status:\s+)Verified", r"\1Needs Review", block)
        text = text.replace(block, new_block)
        map_path.write_text(text, encoding="utf-8")
        print(
            f"  [DECAY] Modificado status a 'Needs Review' en documentation-map.yaml para: {doc_path}"
        )


def add_source_of_truth_to_front_matter(path: Path, new_srcs: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return

    fm = yaml.safe_load(parts[1]) or {}
    if not isinstance(fm, dict):
        return

    existing_sots = fm.get("source_of_truth", [])
    if not isinstance(existing_sots, list):
        existing_sots = [existing_sots]

    updated_sots = list(existing_sots)
    changed = False
    for src in new_srcs:
        if src not in updated_sots:
            updated_sots.append(src)
            changed = True

    if changed:
        fm["source_of_truth"] = updated_sots
        new_fm_text = yaml.safe_dump(fm, sort_keys=False, default_flow_style=False)
        parts[1] = new_fm_text
        path.write_text("---\n".join(parts), encoding="utf-8")
        print(
            f"  [SOT REPARADO] Se añadieron dependencias en el front matter de {path}: {new_srcs}"
        )


def add_source_of_truth_to_map(
    map_path: Path, doc_path: str, new_srcs: list[str]
) -> None:
    text = map_path.read_text(encoding="utf-8")
    escaped_doc_path = re.escape(doc_path)
    pattern = re.compile(
        rf"(- path:\s+{escaped_doc_path}\b.*?)(?=\n- path:|\Z)", re.DOTALL
    )

    match = pattern.search(text)
    if match:
        block = match.group(1)
        data = yaml.safe_load(block[2:])
        existing_sots = data.get("source_of_truth", [])
        if not isinstance(existing_sots, list):
            existing_sots = [existing_sots]

        updated_sots = list(existing_sots)
        changed = False
        for src in new_srcs:
            if src not in updated_sots:
                updated_sots.append(src)
                changed = True

        if changed:
            data["source_of_truth"] = updated_sots
            new_block_content = yaml.safe_dump(
                data, sort_keys=False, default_flow_style=False
            )
            indented_lines = []
            for i, line in enumerate(new_block_content.splitlines()):
                if i == 0:
                    indented_lines.append(f"- {line}")
                else:
                    indented_lines.append(f"  {line}")
            new_block = "\n".join(indented_lines) + "\n"

            text = text.replace(block, new_block)
            map_path.write_text(text, encoding="utf-8")
            print(
                f"  [SOT REPARADO] Se añadieron dependencias en el documentation-map.yaml para: {doc_path}"
            )


def find_correct_script_path(repo_root: Path, stale_rel_path: str) -> str | None:
    filename = Path(stale_rel_path).name
    if not filename.endswith(".py"):
        match = re.search(r"([a-zA-Z0-9_\-]+\.py)\b", stale_rel_path)
        if match:
            filename = match.group(1)
        else:
            return None

    for p in repo_root.glob(f"**/{filename}"):
        if ".venv" not in p.parts:
            return p.relative_to(repo_root).as_posix()
    return None


def repair_stale_command_in_file(
    file_path: Path, old_cmd: str, repo_root: Path
) -> str | None:
    script_match = re.search(r"\bpython3?\s+([a-zA-Z0-9_\-/]+\.py)\b", old_cmd)
    if script_match:
        stale_path = script_match.group(1)
        correct_path = find_correct_script_path(repo_root, stale_path)
        if correct_path and correct_path != stale_path:
            new_cmd = old_cmd.replace(stale_path, correct_path)
            text = file_path.read_text(encoding="utf-8")
            if old_cmd in text:
                text = text.replace(old_cmd, new_cmd)
                file_path.write_text(text, encoding="utf-8")
                print(
                    "  [REPARADO] Se corrigió automáticamente la ruta en el Markdown!"
                )
                print(f"    Antes: {stale_path}")
                print(f"    Ahora: {correct_path}")
                return new_cmd
    return None


def query_gemini_api(api_key: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Error llamando a la API de Gemini: {e}")
        return ""


def clean_json_response(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return {}


def run_command_safely(cmd: str, repo_root: Path) -> tuple[int, str]:
    cmd_run = cmd.replace("<client>", "smoke_ivirma")
    cmd_run = cmd_run.replace("<client_name>", "smoke_ivirma")
    cmd_run = cmd_run.replace("<client_id>", "smoke_ivirma")
    cmd_run = cmd_run.replace("<tower>", "T5")
    cmd_run = cmd_run.replace("<TOWER>", "T5")
    cmd_run = cmd_run.replace("Txx", "T5")
    cmd_run = cmd_run.replace(
        "/ruta/al/contexto.docx", "templates/golden_paths/README.md"
    )
    cmd_run = cmd_run.replace(
        "/ruta/a/respuestas.txt", "templates/golden_paths/README.md"
    )

    if "venv" in cmd_run or "install --upgrade pip" in cmd_run:
        return 0, "Skipped venv creation/upgrade"

    cmd_run = cmd_run.replace("./.venv/bin/python", sys.executable)
    cmd_run = cmd_run.replace("python ", f"{sys.executable} ")

    print(f"    Ejecutando: {cmd_run}")
    try:
        res = subprocess.run(
            cmd_run,
            shell=True,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=25,
        )
        output = res.stdout + res.stderr
        return res.returncode, output
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT EXPIRED"
    except Exception as e:
        return 1, f"EXECUTION ERROR: {e}"


def run_runnable_docs_validation(
    repo_root: Path, map_path: Path, doc_path: str, file_path: Path
) -> bool:
    print(f"=== [EVOLUCIÓN 1: RUNNABLE DOCS] Validando comandos en {doc_path} ===")
    text = file_path.read_text(encoding="utf-8")
    blocks = FENCED_BLOCK_RE.findall(text)

    passed = True
    for block in blocks:
        lines = block.splitlines()
        last_cmd_output = ""
        for line in lines:
            line_stripped = line.strip()
            if (
                line_stripped.startswith("./.venv/bin/python")
                or line_stripped.startswith("python")
                or line_stripped.startswith("pytest")
                or line_stripped.startswith("PYTHONPATH=src")
            ):
                code, output = run_command_safely(line_stripped, repo_root)
                last_cmd_output = output
                if code != 0:
                    print(
                        f"  [ERROR] Falló comando en {doc_path}. Intentando autocuración activa de ruta..."
                    )
                    new_cmd = repair_stale_command_in_file(
                        file_path, line_stripped, repo_root
                    )
                    if new_cmd:
                        code_retry, output_retry = run_command_safely(
                            new_cmd, repo_root
                        )
                        last_cmd_output = output_retry
                        if code_retry == 0:
                            print("  [ÉXITO] Autocuración de comando exitosa!")
                            continue

                    print("  [FALLO] No se pudo autocurar el comando.")
                    print(f"    Comando: {line_stripped}")
                    print(f"    Output:\n{output}")
                    passed = False
                    break
            elif "ASSERT_OUTPUT:" in line_stripped:
                match = re.search(r"ASSERT_OUTPUT:\s*\"([^\"]+)\"", line_stripped)
                if match:
                    expected = match.group(1)
                    if expected not in last_cmd_output:
                        print(f"  [FALLO] Aserción de salida fallida en {doc_path}")
                        print(f'    Se esperaba encontrar: "{expected}"')
                        print(f"    Output real:\n{last_cmd_output}")
                        passed = False
                        break
        if not passed:
            break

    if not passed:
        update_front_matter_status_to_needs_review(file_path)
        update_map_status_to_needs_review(map_path, doc_path)
        return False

    print(
        f"  [ÉXITO] Todos los snippets ejecutables y aserciones de {doc_path} pasaron correctamente."
    )
    return True


def run_ai_semantic_auditor_validation(
    repo_root: Path,
    map_path: Path,
    doc_path: str,
    file_path: Path,
    source_of_truth: list[str],
    api_key: str,
) -> bool:
    print(
        f"=== [EVOLUCIÓN 2: AI SEMANTIC AUDITOR] Evaluando {doc_path} contra schemas ==="
    )

    schemas_content_list = []
    for s_path in source_of_truth:
        resolved_s = (repo_root / s_path).resolve()
        if (
            resolved_s.exists()
            and resolved_s.is_file()
            and s_path.endswith((".py", ".json"))
        ):
            schemas_content_list.append(
                f"--- SOURCE: {s_path} ---\n{resolved_s.read_text(encoding='utf-8')}"
            )

    if not schemas_content_list:
        print(
            "  [IGNORADO] No hay archivos de esquema de origen para auditar semánticamente."
        )
        return True

    markdown_content = file_path.read_text(encoding="utf-8")
    schemas_content = "\n\n".join(schemas_content_list)

    prompt = f"""
You are a Staff Software Engineer at Google/Palantir specializing in hexagonal architecture and contract enforcement.
Below is the technical documentation Markdown file for a data contract/boundary:
--- START DOCUMENT ({doc_path}) ---
{markdown_content}
--- END DOCUMENT ---

Below are the Python source of truth files (Pydantic schemas/classes/config) that define the actual data structures:
--- START SCHEMAS ---
{schemas_content}
--- END SCHEMAS ---

Audit the documentation Markdown against the Python source of truth.
Verify if there are any discrepancies, missing fields, wrong data types, or obsolete/stale descriptions.

If there are any discrepancies or stale areas, you must perform the following actions:
1. Describe the changes needed in "reason".
2. Set "status" to "repaired".
3. Provide the COMPLETE, corrected Markdown content in "corrected_content". You must output the entire repaired Markdown file, with corrected tables, field lists, or metadata.

Your response must be in strict JSON format:
{{
  "status": "ok" | "repaired",
  "reason": "Detailed description of changes, or empty if ok",
  "corrected_content": "The full repaired Markdown document, or empty if ok"
}}
"""
    res_text = query_gemini_api(api_key, prompt)
    res_json = clean_json_response(res_text)

    if res_json.get("status") == "repaired":
        reason = res_json.get("reason", "Unknown discrepancy")
        corrected_content = res_json.get("corrected_content", "")

        if corrected_content and len(corrected_content) > 100:
            print(f"  [AUTOCURADO] Gemini reparó el contenido físico de {doc_path}!")
            print(f"    Razón de la discrepancia: {reason}")
            file_path.write_text(corrected_content, encoding="utf-8")
            return True
        else:
            print(
                "  [ALARMA] Intento de autocuración por IA falló (contenido vacío o inválido)."
            )
            update_front_matter_status_to_needs_review(file_path)
            update_map_status_to_needs_review(map_path, doc_path)
            return False

    elif res_json.get("status") == "alarm":
        reason = res_json.get("reason", "Unknown discrepancy")
        print(
            f"  [ALARMA] Auditoría semántica falló para {doc_path} sin opción de reparación."
        )
        print(f"    Razón: {reason}")
        update_front_matter_status_to_needs_review(file_path)
        update_map_status_to_needs_review(map_path, doc_path)
        return False

    print(f"  [ÉXITO] Auditoría semántica pasada para {doc_path}.")
    return True


def run_automated_stale_decay_validation(
    map_path: Path, doc_path: str, file_path: Path, last_verified: date | None
) -> bool:
    print(
        f"=== [EVOLUCIÓN 3: AUTOMATED STALE DECAY] Evaluando frescura de {doc_path} ==="
    )
    if not last_verified:
        print("  [FALLO] No se pudo determinar la fecha de última verificación.")
        update_front_matter_status_to_needs_review(file_path)
        update_map_status_to_needs_review(map_path, doc_path)
        return False

    today = date.today()
    age_days = (today - last_verified).days
    print(f"  Última verificación: {last_verified} ({age_days} días de antigüedad)")

    if age_days > 120:
        print(
            "  [DEGRADADO] El documento ha superado el límite de frescura de 120 días."
        )
        update_front_matter_status_to_needs_review(file_path)
        update_map_status_to_needs_review(map_path, doc_path)
        return False

    print(
        f"  [ÉXITO] El documento se encuentra dentro del rango de frescura ({age_days}/120 días)."
    )
    return True


def discover_and_register_untracked_md(
    repo_root: Path, map_path: Path, tracked_paths: set[str]
) -> None:
    print("\n=== [BLINDAJE 1] Buscando archivos Markdown huérfanos ===")

    # Exclude typical strategy and legacy generated paths from active tracking
    exclude_patterns = [
        "docs/reference/generated/legacy-gemini/**",
        "docs/strategy/**",
    ]
    ignored_keywords = [
        ".venv",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "working/",
    ]

    untracked_found = []
    # Search for all .md files in the repo root and docs/
    for md_p in repo_root.glob("**/*.md"):
        # Normalize relative path
        rel_posix = md_p.resolve().relative_to(repo_root).as_posix()

        # Check exclusion keywords
        if any(kw in rel_posix for kw in ignored_keywords):
            continue

        # Check exclusion patterns
        is_excluded = False
        for pattern in exclude_patterns:
            if "/" in pattern:
                # Match relative path
                if Path(rel_posix).match(pattern) or md_p.match(pattern):
                    is_excluded = True
                    break
            else:
                if md_p.name == pattern:
                    is_excluded = True
                    break

        if is_excluded:
            continue

        if rel_posix not in tracked_paths:
            untracked_found.append((rel_posix, md_p))

    if not untracked_found:
        print("  [ÉXITO] No se descubrieron nuevos archivos Markdown huérfanos.")
        return

    # Read current map content
    map_text = map_path.read_text(encoding="utf-8")

    # We append untracked entries right under the entries: line of the map file
    for rel_posix, md_p in untracked_found:
        print(f"  [AUTOCURADO] Descubierto Markdown huérfano: '{rel_posix}'")

        # Check if the physical file has a front matter
        fm = governance.read_front_matter(md_p)
        if not fm:
            # Write default front matter to physical file!
            default_fm = f"""---
status: Draft
owner: docs-governance
source_of_truth: []
last_verified_against: {date.today().isoformat()}
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---

"""
            # Prepend front matter
            content = md_p.read_text(encoding="utf-8")
            md_p.write_text(default_fm + content, encoding="utf-8")
            print(
                f"    [REPARADO] Escrita cabecera por defecto en archivo físico: {rel_posix}"
            )
            fm = yaml.safe_load(default_fm[4:-5])

        # Format map entry block
        entry_yaml = {
            "path": rel_posix,
            "kind": "document",
            "title": md_p.stem.replace("_", " ").replace("-", " ").title(),
            "doc_type": fm.get("doc_type", "canonical"),
            "status": fm.get("status", "Draft"),
            "owner": fm.get("owner", "docs-governance"),
            "applies_to": fm.get("applies_to", ["humans", "ai-agents"]),
            "source_of_truth": fm.get("source_of_truth", []),
            "last_verified_against": fm.get(
                "last_verified_against", date.today().isoformat()
            ),
        }

        entry_block_content = yaml.safe_dump(
            entry_yaml, sort_keys=False, default_flow_style=False
        )
        indented_lines = []
        for i, line in enumerate(entry_block_content.splitlines()):
            if i == 0:
                indented_lines.append(f"- {line}")
            else:
                indented_lines.append(f"  {line}")
        new_entry_block = "\n".join(indented_lines) + "\n"

        # Find entries: header and insert new entry right below it
        entries_line = "entries:\n"
        if entries_line in map_text:
            map_text = map_text.replace(entries_line, f"entries:\n{new_entry_block}")

    map_path.write_text(map_text, encoding="utf-8")
    print(
        f"  [ÉXITO] Se agregaron {len(untracked_found)} nuevos registros de Markdown al mapa de documentación."
    )


def discover_dynamic_source_of_truth_dependencies(
    repo_root: Path, map_path: Path, doc_path: str, file_path: Path
) -> None:
    print(
        f"=== [BLINDAJE 2] Escaneando dependencias de importación para {doc_path} ==="
    )

    # 1. Parse markdown for python scripts in commands
    text = file_path.read_text(encoding="utf-8")
    blocks = FENCED_BLOCK_RE.findall(text)

    referenced_scripts = set()
    for block in blocks:
        for line in block.splitlines():
            script_match = re.search(r"\bpython3?\s+([a-zA-Z0-9_\-/]+\.py)\b", line)
            if script_match:
                referenced_scripts.add(script_match.group(1))

    if not referenced_scripts:
        return

    transitive_deps = set()
    for rel_s in referenced_scripts:
        resolved_s = repo_root / rel_s
        if not resolved_s.exists():
            continue

        transitive_deps.add(rel_s)
        # Scan python script for local imports, e.g. "from assessment_engine.infrastructure.runtime_env import ..."
        try:
            content = resolved_s.read_text(encoding="utf-8")
            import_matches = re.findall(
                r"\bfrom\s+(assessment_engine\.[a-zA-Z0-9_\.]+)\s+import\b", content
            )
            for mod in import_matches:
                # Convert module namespace to relative posix path, e.g. assessment_engine.infrastructure.runtime_env -> src/assessment_engine/infrastructure/runtime_env.py
                rel_mod_path = f"src/{mod.replace('.', '/')}.py"
                if (repo_root / rel_mod_path).exists():
                    transitive_deps.add(rel_mod_path)
                else:
                    # Try package root namespace
                    pkg_mod_path = f"src/{mod.replace('.', '/')}/__init__.py"
                    if (repo_root / pkg_mod_path).exists():
                        transitive_deps.add(pkg_mod_path)
        except Exception:
            pass

    if not transitive_deps:
        return

    # Check if these are already in SOT
    front_matter = governance.read_front_matter(file_path) or {}
    existing_sots = front_matter.get("source_of_truth", [])
    if not isinstance(existing_sots, list):
        existing_sots = [existing_sots]

    missing_sots = []
    for dep in sorted(transitive_deps):
        # Normalize paths to match relative structure, e.g. ../../src/... inside md of docs/operations
        # In Markdown of docs/operations/, path is: ../../src/assessment_engine/...
        # In documentation-map.yaml, path is: src/assessment_engine/...
        # Let's normalize it to map structure
        map_dep_path = dep
        if map_dep_path not in existing_sots:
            # Check physical file relative path
            # From docs/operations/installation.md (depth 2), rel is: ../../src/assessment_engine/...
            # Let's construct correct relative path based on document depth
            depth = len(Path(doc_path).parts) - 1
            rel_prefix = "../" * depth if depth > 0 else "./"
            md_dep_path = f"{rel_prefix}{dep}"

            # Verify we don't duplicate under different relative formats
            md_already_mapped = False
            for existing in existing_sots:
                if dep in existing or Path(existing).name == Path(dep).name:
                    md_already_mapped = True
                    break

            if not md_already_mapped:
                missing_sots.append((map_dep_path, md_dep_path))

    if missing_sots:
        print(
            f"  [SOT] Descubiertas {len(missing_sots)} dependencias transitivas faltantes para {doc_path}!"
        )
        # Add to Markdown front matter
        add_source_of_truth_to_front_matter(
            file_path, [md_p for _, md_p in missing_sots]
        )
        # Add to documentation-map.yaml
        add_source_of_truth_to_map(
            map_path, doc_path, [map_p for map_p, _ in missing_sots]
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Nightly Active Self-Healing and Documentation Decay Engine"
    )
    parser.add_argument(
        "--repo-root", default=".", help="Ruta de la raíz del repositorio"
    )
    parser.add_argument(
        "--documentation-map",
        default="docs/documentation-map.yaml",
        help="Ruta del mapa de documentación",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    map_path = Path(args.documentation_map).resolve()

    if not map_path.exists():
        print(f"ERROR: No existe el mapa de documentación en: {map_path}")
        return 1

    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("VERTEX_AI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )

    documentation_map = governance.load_yaml(map_path)
    entries = documentation_map.get("entries", [])

    # Blindaje 0: Sanitize documentation map and clean up obsolete local files/folders (Zero-Entropy)
    import shutil

    cleaned_entries = []
    pollution_removed = 0
    ignored_keywords = [
        ".venv",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "working/",
    ]
    for entry in entries:
        if isinstance(entry, dict) and "path" in entry:
            path_val = entry["path"]
            if any(kw in path_val for kw in ignored_keywords):
                pollution_removed += 1
                continue
        cleaned_entries.append(entry)

    if pollution_removed > 0:
        print(
            f"  [AUTO-HEAL] Purgadas {pollution_removed} entradas polucionadas de terceros del mapa de documentación!"
        )
        documentation_map["entries"] = cleaned_entries
        with open(map_path, "w", encoding="utf-8") as f:
            yaml.dump(
                documentation_map,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        entries = cleaned_entries

    # Saneamiento de basura local en working/
    working_dir = repo_root / "working"
    if working_dir.exists():
        # Auto-delete test_client residue
        test_client_dir = working_dir / "test_client"
        if test_client_dir.exists():
            shutil.rmtree(test_client_dir)
            print(
                "  [AUTO-HEAL] Eliminada carpeta residual de pruebas 'working/test_client' del disco."
            )
        # Auto-delete stale compressed files
        for p in working_dir.glob("*"):
            if p.suffix in (".zip", ".gz", ".tar"):
                p.unlink()
                print(
                    f"  [AUTO-HEAL] Eliminado archivo de respaldo obsoleto del disco: {p.name}"
                )

    tracked_paths = set()
    for entry in entries:
        if isinstance(entry, dict) and "path" in entry:
            tracked_paths.add(entry["path"])

    # Blindaje 1: Discover and register untracked markdown files automatically
    discover_and_register_untracked_md(repo_root, map_path, tracked_paths)

    # Re-load map after potential additions from Blindaje 1
    documentation_map = governance.load_yaml(map_path)
    entries = documentation_map.get("entries", [])

    total_verified = 0
    failures = 0

    print("\n=====================================================================")
    print("INICIANDO MOTOR NOCTURNO DE AUTOCURACIÓN Y GOBERNANZA DE DOCUMENTACIÓN")
    print("=====================================================================\n")

    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") != "document":
            continue

        doc_path = entry.get("path", "")
        file_path = repo_root / doc_path

        if not file_path.exists():
            continue

        front_matter = governance.read_front_matter(file_path)
        if not front_matter or front_matter.get("status") != "Verified":
            continue

        total_verified += 1
        print(f"\n👉 Procesando: {doc_path}")

        # Get last verified date
        last_verified_val = front_matter.get("last_verified_against")
        last_verified_date = None
        if isinstance(last_verified_val, date):
            last_verified_date = last_verified_val
        elif isinstance(last_verified_val, str):
            try:
                last_verified_date = datetime.strptime(
                    last_verified_val, "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        # 1. Automated Stale Decay
        if not run_automated_stale_decay_validation(
            map_path, doc_path, file_path, last_verified_date
        ):
            failures += 1
            continue

        # 2. Runnable Docs (Execute bash/python commands in markdown with route-repair self-healing)
        if not run_runnable_docs_validation(repo_root, map_path, doc_path, file_path):
            failures += 1
            continue

        # Blindaje 2: Discover dynamic import dependencies and add to SOT automatically
        discover_dynamic_source_of_truth_dependencies(
            repo_root, map_path, doc_path, file_path
        )

        # 3. AI Semantic Auditor (Compare markdown contracts with actual schema code and active self-heal)
        source_of_truth = entry.get("source_of_truth", [])
        if api_key and source_of_truth:
            if not run_ai_semantic_auditor_validation(
                repo_root, map_path, doc_path, file_path, source_of_truth, api_key
            ):
                failures += 1
                continue
        elif not api_key:
            print(
                "  [INFO] No se detectó ninguna API key de Gemini. Omitiendo auditoría semántica con IA."
            )

    print("\n=====================================================================")
    print("BALANCE FINAL:")
    print(f"  Total documentos 'Verified' analizados: {total_verified}")
    print(f"  Documentos degradados a 'Needs Review': {failures}")
    print("=====================================================================")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
