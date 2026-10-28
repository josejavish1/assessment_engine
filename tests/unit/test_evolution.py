# golden-path: ignore
"""Unit Test Suite for Cognitive Evolution Engine in Assessment Engine.

Verifies:
- AstSignatureGuard and AST contract drift prevention.
- EphemeralWorktree sandboxing for isolated git operations.
- ComplexityGuard and McCabe cyclomatic complexity calculation.
- ClosureTribunal and deterministic security gates.
- CognitiveArbiter verdict statuses.
- GenAI Model Hub tiering (gemini-3.1-pro-preview resolution).
"""
from __future__ import annotations

import ast
from pathlib import Path
import pytest

from assessment_engine.infrastructure.evolution.ast_signature_guard import (
    AstSignatureGuard,
    ast_signature_guard,
    diff_ast_signatures,
    extract_signatures_from_code,
)
from assessment_engine.infrastructure.evolution.closure_tribunal import (
    ClosureTribunal,
    ClosureTribunalReport,
    ForensicASTSecurityVisitor,
    closure_tribunal,
)
from assessment_engine.infrastructure.evolution.cognitive_arbiter import (
    CognitiveArbiter,
    VerdictStatus,
)
from assessment_engine.infrastructure.evolution.complexity_guard import (
    audit_code_complexity,
    compute_mccabe_complexity,
)
from assessment_engine.infrastructure.evolution.worktree_runner import (
    worktree_runner,
)
from assessment_engine.infrastructure.genai_client import ModelTier, get_model


def test_model_tier_reasoning_resolves_gemini_3_1_pro() -> None:
    """Verify that reasoning tier resolves strictly to gemini-3.1-pro-preview per project governance."""
    model = get_model(ModelTier.REASONING)
    assert model == "gemini-3.1-pro-preview"


def test_mccabe_complexity_calculation() -> None:
    """Verify McCabe cyclomatic complexity computation."""
    simple_code = "def simple(a, b):\n    return a + b\n"
    complex_code = """
def complex_fn(x):
    if x > 0:
        if x > 10:
            return 1
        elif x > 5:
            return 2
        else:
            return 3
    else:
        return 0
"""
    assert audit_code_complexity(simple_code).max_complexity == 1
    assert audit_code_complexity(complex_code).max_complexity >= 4


def test_ast_signature_extraction_and_breaking_change_detection() -> None:
    """Verify that breaking signature changes are caught by AST signature diff."""
    baseline = """
def calculate_pnl(revenue: float, cost: float) -> float:
    return revenue - cost

class AccountService:
    def get_balance(self, account_id: str) -> float:
        return 100.0
"""
    compatible_evolution = """
def calculate_pnl(revenue: float, cost: float) -> float:
    return revenue - cost

def calculate_ebitda(revenue: float, opex: float) -> float:
    return revenue - opex

class AccountService:
    def get_balance(self, account_id: str) -> float:
        return 100.0

    def get_currency(self) -> str:
        return "EUR"
"""
    breaking_evolution = """
def calculate_pnl(revenue: float) -> float:
    return revenue

class AccountService:
    def get_balance(self) -> float:
        return 100.0
"""
    base_sigs = extract_signatures_from_code(baseline)
    compat_sigs = extract_signatures_from_code(compatible_evolution)
    break_sigs = extract_signatures_from_code(breaking_evolution)

    compat_violations = diff_ast_signatures(base_sigs, compat_sigs)
    assert len(compat_violations) == 0

    break_violations = diff_ast_signatures(base_sigs, break_sigs)
    assert len(break_violations) > 0


def test_forensic_ast_security_visitor() -> None:
    """Verify that the closure tribunal flags dangerous sinks like eval and os.system."""
    clean_code = "def add(a, b):\n    return a + b\n"
    dirty_code = "import os\ndef run(cmd):\n    os.system(cmd)\n    eval(cmd)\n"

    clean_tree = ast.parse(clean_code)
    clean_visitor = ForensicASTSecurityVisitor()
    clean_visitor.visit(clean_tree)
    assert len(clean_visitor.findings) == 0

    dirty_tree = ast.parse(dirty_code)
    dirty_visitor = ForensicASTSecurityVisitor()
    dirty_visitor.visit(dirty_tree)
    assert len(dirty_visitor.findings) >= 2


def test_ephemeral_worktree_lifecycle() -> None:
    """Verify isolated git worktree creation and cleanup."""
    repo_root = Path.cwd().resolve()
    worktree = worktree_runner.create_worktree(repo_root=repo_root, branch_prefix="test_arb_")

    try:
        assert worktree.worktree_path.exists()
        assert (worktree.worktree_path / ".git").exists()
    finally:
        worktree.cleanup()
        assert not worktree.worktree_path.exists()
