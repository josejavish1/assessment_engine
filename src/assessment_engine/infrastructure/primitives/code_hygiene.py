"""
Fast Code Hygiene & Formatter Primitive — GEMA 09 (SOTA 2026).
Integrates Biome (Rust ultra-fast linter & formatter for TS/JS/CSS/JSON in sub-5ms)
with a deterministic Python fallback engine for zero-dependency environments.
Enforces POSIX final newlines, removes trailing whitespace, and organizes import headers.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("assessment_engine.infrastructure.primitives.code_hygiene")


@dataclass
class HygieneResult:
    success: bool
    formatted_files: int
    execution_time_ms: float
    output_log: str


class CodeHygienePrimitive:
    """
    Sanitize and format web and backend code using Biome with fallback.
    """

    def __init__(self) -> None:
        self.binary = shutil.which("biome")

    def is_available(self) -> bool:
        """Determine whether the official Biome binary is available in PATH."""
        return self.binary is not None

    def _run_python_hygiene_fallback(self, target_path: Path, start: float) -> HygieneResult:
        try:
            files_to_clean = [target_path] if target_path.is_file() else list(target_path.rglob("*"))
            cleaned_count = sum(
                1 for f in files_to_clean
                if f.is_file() and f.suffix in (".py", ".ts", ".js", ".tsx", ".jsx", ".json", ".css", ".html") and self.clean_file(f)
            )
            elapsed_ms = (time.time() - start) * 1000
            return HygieneResult(True, cleaned_count, elapsed_ms, f"Formateo determinista aplicado a {cleaned_count} archivos (Biome no instalado).")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            elapsed_ms = (time.time() - start) * 1000
            return HygieneResult(False, 0, elapsed_ms, f"Error en fallback de higiene: {ex}")

    def polish_frontend_code(self, target_path: Path) -> HygieneResult:
        """Ejecuta Biome sobre archivos TypeScript, JavaScript, CSS o JSON. Fallback a Python."""
        start = time.time()
        if not target_path.exists():
            return HygieneResult(False, 0, 0.0, f"Ruta {target_path} no existe")

        if self.is_available() and self.binary:
            cmd: list[str] = [str(self.binary), "check", "--write", "--unsafe", str(target_path.resolve())]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                elapsed_ms = (time.time() - start) * 1000
                return HygieneResult(True, 1, elapsed_ms, res.stdout or "Biome formatted successfully")
            except subprocess.CalledProcessError as e:
                elapsed_ms = (time.time() - start) * 1000
                return HygieneResult(False, 0, elapsed_ms, e.stderr or str(e))

        return self._run_python_hygiene_fallback(target_path, start)

    def clean_file_content(self, raw_code: str) -> str:
        """Strip trailing whitespace and ensure a trailing POSIX newline."""
        lines = [line.rstrip() for line in raw_code.splitlines()]
        compacted: list[str] = []
        consecutive_empty = 0
        for l in lines:
            if not l:
                consecutive_empty += 1
                if consecutive_empty <= 2:
                    compacted.append(l)
            else:
                consecutive_empty = 0
                compacted.append(l)

        cleaned = "\n".join(compacted).strip() + "\n"
        return cleaned

    def clean_file(self, target_file: Path) -> bool:
        """Sanitize a file on disk."""
        if not target_file.exists() or target_file.is_dir():
            return False
        try:
            raw = target_file.read_text(encoding="utf-8")
            cleaned = self.clean_file_content(raw)
            if cleaned != raw:
                target_file.write_text(cleaned, encoding="utf-8")
                return True
            return False
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return False


code_hygiene = CodeHygienePrimitive()
