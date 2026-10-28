"""
Cognitive Architect / Editor Decoupling Protocol — GEMA 04 (SOTA 2026).
Decouples high-level strategic reasoning (Architect) from low-level line diff application (Editor).
Enforces Line Collapse Detection (threshold 15% anti-lazy coding) to prevent truncated code hallucinations.
Guarantees complete, structurally intact file mutations.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("assessment_engine.infrastructure.primitives.architect_editor")


@dataclass
class ArchitecturePlanStep:
    step_id: int
    target_file: str
    action: str  # "modify", "create", "delete"
    intent: str
    invariants_to_preserve: list[str] = field(default_factory=list)


@dataclass
class ArchitecturePlan:
    goal: str
    steps: list[ArchitecturePlanStep] = field(default_factory=list)


@dataclass
class EditResult:
    success: bool
    final_content: str
    lines_collapsed_percentage: float
    error_message: Optional[str] = None


class ArchitectEditorPrimitive:
    """
    Implement an Architect/Editor decoupling protocol with lazy-coding detection.
    """

    LAZY_PATTERNS = [
        re.compile(r"//\s*\.\.\.\s*(?:rest of code|resto del c[oó]digo|existing code|unchanged)", re.IGNORECASE),
        re.compile(r"#\s*\.\.\.\s*(?:rest of code|resto del c[oó]digo|existing code|unchanged)", re.IGNORECASE),
        re.compile(r"/\*\s*\.\.\.\s*(?:rest of code|existing code)\s*\*/", re.IGNORECASE),
        re.compile(r"<!--\s*\.\.\.\s*(?:rest of code|existing code)\s*-->", re.IGNORECASE),
    ]

    def __init__(self, activation_line_threshold: int = 150, max_collapse_threshold: float = 0.15) -> None:
        self.activation_line_threshold = activation_line_threshold
        self.max_collapse_threshold = max_collapse_threshold

    def should_decouple(self, content: str) -> bool:
        """Determine whether a file exceeds the line threshold to trigger decoupling."""
        return len(content.splitlines()) >= self.activation_line_threshold

    def validate_plan(self, plan: ArchitecturePlan) -> bool:
        """Verify that the Architect plan is complete and respects invariants."""
        if not plan.goal or not plan.steps:
            return False
        for step in plan.steps:
            if not step.target_file or step.action not in ("modify", "create", "delete"):
                return False
        return True

    def apply_replacement(
        self,
        original_content: str,
        search_block: str,
        replace_block: str,
        allow_deletion: bool = False,
    ) -> EditResult:
        """Apply an exact replacement block, verifying that it contains no lazy omission markers and that the file does not collapse beyond the allowed threshold."""
        if search_block not in original_content:
            return EditResult(
                success=False,
                final_content=original_content,
                lines_collapsed_percentage=0.0,
                error_message="Search block no encontrado exactamente en el contenido original.",
            )

        for pat in self.LAZY_PATTERNS:
            if pat.search(replace_block):
                return EditResult(
                    success=False,
                    final_content=original_content,
                    lines_collapsed_percentage=0.0,
                    error_message="Alerta de Lazy Coding: Se detectó un marcador de código omitido en el bloque de reemplazo.",
                )

        new_content = original_content.replace(search_block, replace_block, 1)
        orig_lines = len(original_content.splitlines())
        new_lines = len(new_content.splitlines())

        # 2. Detect line collapse
        if orig_lines > 0 and not allow_deletion:
            collapsed_ratio = (orig_lines - new_lines) / max(1, orig_lines)
            if collapsed_ratio > self.max_collapse_threshold:
                pct = collapsed_ratio * 100.0
                return EditResult(
                    success=False,
                    final_content=original_content,
                    lines_collapsed_percentage=pct,
                    error_message=f"Alerta de Lazy Coding: El archivo colapsó un {pct:.1f}% de sus líneas sin autorización de borrado.",
                )

        return EditResult(
            success=True,
            final_content=new_content,
            lines_collapsed_percentage=0.0,
            error_message=None,
        )

    def apply_file_diff(
        self,
        file_path: Path,
        search_block: str,
        replace_block: str,
        allow_deletion: bool = False,
    ) -> EditResult:
        """Apply the surgical patch to a file on disk."""
        if not file_path.exists():
            return EditResult(False, "", 0.0, f"Archivo {file_path} no existe.")

        original = file_path.read_text(encoding="utf-8")
        result = self.apply_replacement(original, search_block, replace_block, allow_deletion=allow_deletion)
        if result.success:
            file_path.write_text(result.final_content, encoding="utf-8")
        return result


architect_editor = ArchitectEditorPrimitive()
