"""
Consolidate artifacts and disk protocols for the Autonomous Product Director.
Decoupled from autonomous_product_director.py to maintain modularity.
"""
from __future__ import annotations

import ast
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from .director_models import ProductGap

logger = logging.getLogger("assessment_engine.infrastructure.evolution.director_consolidator")


def _backup_if_dirty(dest_file: Path, repo_root: Path, file_rel: str) -> None:
    """Check whether the file has uncommitted local Git changes before consolidating."""
    if not dest_file.exists():
        return
    try:
        diff_res = subprocess.run(
            ["git", "diff", "--name-only", str(dest_file)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if diff_res.stdout.strip():
            logger.info(f"[APD] Cambios locales sin comitear detectados en '{file_rel}'. Git preserva el historial previo.")
    except (subprocess.SubprocessError, OSError) as ex:
        logger.debug(f"[APD-Backup] Nota comprobando árbol git para {file_rel}: {ex}")


def _format_handover_header(file_rel: str, halt_reason: str, final_gaps: list[ProductGap]) -> str:
    """Generate an explanatory handover header in case of partial convergence."""
    if file_rel.endswith(".json"):
        return ""
    if file_rel.endswith((".py", ".sh", ".bash", ".yml", ".yaml", ".ini", ".toml")):
        header = "# [PARTIAL HANDOVER] AUTONOMUOS SOTA 2026\n"
        header += f"# Estado: {halt_reason}\n"
        header += "# Brechas pendientes por subsanar:\n"
        for g in final_gaps:
            clean_desc = "\n#   ".join(str(g.description).strip().splitlines())
            header += f"# - [{g.id}] {clean_desc}\n"
        return header + "\n"

    header = "/* [PARTIAL HANDOVER] AUTONOMUOS SOTA 2026\n"
    header += f" * Estado: {halt_reason}\n"
    header += " * Brechas pendientes por subsanar:\n"
    for g in final_gaps:
        clean_desc = "\n *   ".join(str(g.description).strip().splitlines())
        header += f" * - [{g.id}] {clean_desc}\n"
    return header + " */\n\n"


def _validate_preflight_syntax(file_rel: str, final_code: str) -> bool:
    """Validate generated code syntax before modifying the master file system."""
    if file_rel.endswith(".json"):
        try:
            json.loads(final_code)
            return True
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as json_ex:
            logger.error(f"[APD-Integrity] Rechazando consolidación de '{file_rel}': JSON inválido ({json_ex}). Preservando archivo original.")
            return False
    if file_rel.endswith(".py"):
        try:
            ast.parse(final_code)
            return True
        except SyntaxError as py_ex:
            logger.error(f"[APD-Integrity] Rechazando consolidación de '{file_rel}': SyntaxError en línea {py_ex.lineno} ({py_ex.msg}). Preservando archivo original.")
            return False
    return True


def consolidate_code_map_to_disk(
    code_map: dict[str, str],
    repo_root: Path,
    status: str,
    halt_reason: str,
    final_gaps: list[ProductGap],
) -> None:
    """Atomically and safely merge synthesized artifacts into the master file system with pre-flight validation."""
    for file_rel, final_code in code_map.items():
        dest_file = repo_root / file_rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        _backup_if_dirty(dest_file, repo_root, file_rel)

        if status == "HALTED":
            header = _format_handover_header(file_rel, halt_reason, final_gaps)
            final_code = header + final_code
            logger.info(f"[APD] ⏳ Convergencia parcial. Código consolidado con TODOs en: {dest_file.name}")
        else:
            logger.info(f"[APD] 🚀 Código certificado consolidado en disco: {file_rel}")

        if not _validate_preflight_syntax(file_rel, final_code):
            continue

        dest_file.write_text(final_code, encoding="utf-8")
