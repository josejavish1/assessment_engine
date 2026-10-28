"""
Product Ledger: Deterministic cycle-detection and halt evaluator for product gaps.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .director_models import ProductGap


class ProductLedger:
    """
    Libro Mayor Determinista. Evita bucles infinitos mediante:
    1. Límite estricto de iteraciones (Cota de Rendimientos Decrecientes).
    2. Colisión de Hashes (Detección de Ciclos).
    3. Convergencia Absoluta (0 GAPs).
    """

    def __init__(self, max_iterations: int = 3) -> None:
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.seen_hashes: set[str] = set()
        self.history: list[list[ProductGap]] = []
        self.hash_history: list[str] = []

    def compute_hash(self, gaps: list[ProductGap]) -> str:
        """Compute a deterministic SHA-256 hash of the current approved gaps state."""
        approved_gaps = [g for g in gaps if g.is_yagni_approved]
        if not approved_gaps:
            return hashlib.sha256(b"empty").hexdigest()

        sorted_gaps = sorted([f"{g.id}:{g.target_module}" for g in approved_gaps])
        payload = json.dumps(sorted_gaps).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def evaluate_gaps(self, gaps: list[ProductGap]) -> tuple[bool, str]:
        """Evaluate suggested gaps and determine the halt condition."""
        self.current_iteration += 1
        approved_gaps = [g for g in gaps if g.is_yagni_approved]

        if not approved_gaps:
            return True, "HALT: Convergencia perfecta (0 GAPs aprobados)."

        if self.current_iteration > self.max_iterations:
            return True, f"HALT: Límite de iteraciones ({self.max_iterations}) superado. Rendimientos decrecientes."

        gap_hash = self.compute_hash(approved_gaps)
        if gap_hash in self.seen_hashes:
            return True, f"HALT: Colisión de hash detectada ({gap_hash[:8]}). Evitando ciclo infinito."

        self.seen_hashes.add(gap_hash)
        self.hash_history.append(gap_hash)
        self.history.append(approved_gaps)
        return False, "Continuar refinamiento"
