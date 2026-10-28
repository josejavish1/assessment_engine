"""Cognitive Evolution Engine (RFC-015 SOTA Master Pipeline).

Provides deterministic meta-intelligence and autonomous evolution:
- CognitiveArbiter: Asymmetric dialectic loop (Synthesizer vs Grounded Skeptic).
- EpistemicDistiller: SOTA mining and 3-Cube Matrix distillation.
- ClosureTribunal: Deterministic closure gates (AST, Radon, Mutation CTF, Cube Parity).
- AstSignatureGuard: Public interface drift prevention and signature snapshotting.
- EphemeralWorktree: Zero-risk isolated git sandboxing.
"""
from __future__ import annotations

from assessment_engine.infrastructure.evolution.ast_signature_guard import (
    AstSignatureGuard,
    ast_signature_guard,
    diff_ast_signatures,
    snapshot_file,
)
from assessment_engine.infrastructure.evolution.closure_tribunal import (
    ClosureTribunal,
    closure_tribunal,
)
from assessment_engine.infrastructure.evolution.cognitive_arbiter import (
    CognitiveArbiter,
    SkepticRole,
    SynthesizerRole,
    VerdictStatus,
)
from assessment_engine.infrastructure.evolution.complexity_guard import (
    audit_code_complexity,
    compute_mccabe_complexity,
)
from assessment_engine.infrastructure.evolution.epistemic_distiller import (
    EpistemicDistiller,
    epistemic_distiller,
)
from assessment_engine.infrastructure.evolution.worktree_runner import (
    EphemeralWorktree,
    worktree_runner,
)

__all__ = [
    "AstSignatureGuard",
    "ClosureTribunal",
    "CognitiveArbiter",
    "EphemeralWorktree",
    "EpistemicDistiller",
    "SkepticRole",
    "SynthesizerRole",
    "VerdictStatus",
    "ast_signature_guard",
    "audit_code_complexity",
    "closure_tribunal",
    "compute_mccabe_complexity",
    "diff_ast_signatures",
    "epistemic_distiller",
    "snapshot_file",
    "worktree_runner",
]
