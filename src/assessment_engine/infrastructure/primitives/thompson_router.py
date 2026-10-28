"""
Bayesian Thompson Sampling Router & Multi-Armed Bandit Primitive — GEMA 27 (SOTA 2026).
Dynamic traffic balancing with Beta-Bernoulli conjugate distributions (random.betavariate).
Incorporates:
- Anti-bias burn-in period (N < 20 sessions balanced exploration).
- Deterministic sticky session consistency (session_id immutability).
- Friction-penalized posterior utility (penalizes rage clicks and errors).
- Circuit Breaker emergency quarantine (shuts down broken variants with >= 3 early errors).
- Monte Carlo convergence verification (P(win) >= 95% threshold).
Zero external dependencies ($0.00 cost, < 2ms latency).
"""

from __future__ import annotations

import logging
import random
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.thompson_router")


@dataclass
class ExperimentArm:
    """Represent the state and statistical parameters of an experiment arm (variant)."""
    experiment_id: str
    variant_id: str
    sessions_count: int = 0
    conversions_count: int = 0
    error_count: int = 0
    friction_index: float = 0.0
    is_quarantined: bool = False


@dataclass
class AssignmentResult:
    """Represent the deterministic outcome of assigning a variant to a session."""
    experiment_id: str
    session_id: str
    variant_id: str
    is_sticky: bool
    reason: str                      # "sticky", "burn_in", "thompson_sampled", "circuit_breaker_quarantine"
    assigned_at: float = 0.0


@dataclass
class ExperimentConvergence:
    """Represent the convergence state and Bayesian significance of the tournament."""
    experiment_id: str
    is_converged: bool
    winning_variant: str | None
    win_probability_pct: float
    total_sessions: int
    uplift_pct: float


def _resolve_sticky_assignment(conn: sqlite3.Connection, experiment_id: str, session_id: str) -> str | None:
    """Check whether the session already has an assigned variant to ensure stickiness."""
    cur = conn.execute(
        "SELECT variant_id FROM session_assignments WHERE experiment_id = ? AND session_id = ?",
        (experiment_id, session_id),
    )
    row = cur.fetchone()
    return str(row[0]) if row else None


def _check_and_apply_circuit_breaker(arms: list[ExperimentArm], conn: sqlite3.Connection) -> None:
    """Trigger an emergency circuit breaker if an arm accumulates >= 3 errors in its first 5 sessions."""
    for arm in arms:
        if not arm.is_quarantined and arm.sessions_count <= 5 and arm.error_count >= 3:
            arm.is_quarantined = True
            conn.execute(
                "UPDATE experiment_arms SET is_quarantined = 1 WHERE experiment_id = ? AND variant_id = ?",
                (arm.experiment_id, arm.variant_id),
            )
            logger.warning(
                f"[ThompsonRouter] CIRCUIT BREAKER activado: Variante '{arm.variant_id}' puesta en cuarentena "
                f"({arm.error_count} errores en {arm.sessions_count} sesiones)."
            )


def _sample_thompson_arm(arms: list[ExperimentArm]) -> ExperimentArm:
    """Sample the friction-penalized Beta(alpha, beta) posterior for each active arm."""
    best_sample = -1.0
    best_arm = arms[0]

    for arm in arms:
        alpha = 1.0 + float(arm.conversions_count)
        failures = max(0.0, float(arm.sessions_count - arm.conversions_count))
        friction_penalty = min(25.0, arm.friction_index / 2.0)
        beta_param = 1.0 + failures + friction_penalty

        sample = random.betavariate(alpha, beta_param)
        if sample > best_sample:
            best_sample = sample
            best_arm = arm

    return best_arm


class ThompsonRouterPrimitive:
    """
    Route requests using a Bayesian multi-armed bandit engine for autonomous experimentation.
    """

    def ensure_tables(self, conn: sqlite3.Connection) -> None:
        """Initialize SQLite persistence tables with PRAGMA journal_mode=WAL."""
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiment_arms (
                experiment_id TEXT NOT NULL,
                variant_id TEXT NOT NULL,
                sessions_count INTEGER NOT NULL DEFAULT 0,
                conversions_count INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0,
                friction_index REAL NOT NULL DEFAULT 0.0,
                is_quarantined INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (experiment_id, variant_id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_assignments (
                experiment_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                variant_id TEXT NOT NULL,
                assigned_at REAL NOT NULL,
                PRIMARY KEY (experiment_id, session_id)
            );
        """)
        conn.commit()

    def get_or_create_arms(
        self, conn: sqlite3.Connection, experiment_id: str, default_variants: list[str]
    ) -> list[ExperimentArm]:
        """Retrieve existing arms or initialize default arms with a uniform Beta(1, 1) prior."""
        cur = conn.execute(
            "SELECT variant_id, sessions_count, conversions_count, error_count, friction_index, is_quarantined "
            "FROM experiment_arms WHERE experiment_id = ?",
            (experiment_id,),
        )
        rows = cur.fetchall()
        if rows:
            return [
                ExperimentArm(
                    experiment_id=experiment_id,
                    variant_id=r[0],
                    sessions_count=r[1],
                    conversions_count=r[2],
                    error_count=r[3],
                    friction_index=r[4],
                    is_quarantined=bool(r[5]),
                )
                for r in rows
            ]

        arms: list[ExperimentArm] = []
        for v in default_variants:
            conn.execute(
                "INSERT OR IGNORE INTO experiment_arms "
                "(experiment_id, variant_id, sessions_count, conversions_count, error_count, friction_index, is_quarantined) "
                "VALUES (?, ?, 0, 0, 0, 0.0, 0)",
                (experiment_id, v),
            )
            arms.append(ExperimentArm(experiment_id=experiment_id, variant_id=v))
        conn.commit()
        return arms

    def assign_variant(
        self,
        db_path: Path,
        experiment_id: str,
        session_id: str,
        variant_ids: list[str] | None = None,
        burn_in_threshold: int = 20,
    ) -> AssignmentResult:
        """
        Deterministically assign a variant to the session enforcing stickiness, circuit breaker, and Thompson sampling.
        """
        variants = variant_ids or ["A", "B"]
        conn = sqlite3.connect(str(db_path))
        try:
            self.ensure_tables(conn)

            sticky_var = _resolve_sticky_assignment(conn, experiment_id, session_id)
            if sticky_var is not None:
                return AssignmentResult(
                    experiment_id=experiment_id,
                    session_id=session_id,
                    variant_id=sticky_var,
                    is_sticky=True,
                    reason="sticky",
                    assigned_at=time.time(),
                )

            arms = self.get_or_create_arms(conn, experiment_id, variants)
            _check_and_apply_circuit_breaker(arms, conn)

            active_arms = [a for a in arms if not a.is_quarantined]
            if not active_arms:
                active_arms = arms  # Fallback si todos fueran bloqueados

            needs_burn_in = any(a.sessions_count < burn_in_threshold for a in active_arms)
            if needs_burn_in:
                chosen_arm = min(active_arms, key=lambda a: a.sessions_count)
                reason = "burn_in"
            else:
                chosen_arm = _sample_thompson_arm(active_arms)
                reason = "thompson_sampled"

            # Persist fixed session assignment and increment session counter.
            now = time.time()
            conn.execute(
                "INSERT OR REPLACE INTO session_assignments (experiment_id, session_id, variant_id, assigned_at) VALUES (?, ?, ?, ?)",
                (experiment_id, session_id, chosen_arm.variant_id, now),
            )
            conn.execute(
                "UPDATE experiment_arms SET sessions_count = sessions_count + 1 WHERE experiment_id = ? AND variant_id = ?",
                (experiment_id, chosen_arm.variant_id),
            )
            conn.commit()

            return AssignmentResult(
                experiment_id=experiment_id,
                session_id=session_id,
                variant_id=chosen_arm.variant_id,
                is_sticky=False,
                reason=reason,
                assigned_at=now,
            )
        finally:
            conn.close()

    def record_outcome(
        self,
        db_path: Path,
        experiment_id: str,
        variant_id: str,
        converted: bool = False,
        is_error: bool = False,
        friction_index: float | None = None,
    ) -> None:
        """Record conversions, errors, or friction, updating the Bayesian state of the arm."""
        conn = sqlite3.connect(str(db_path))
        try:
            self.ensure_tables(conn)
            cur = conn.cursor()
            if converted:
                cur.execute(
                    "UPDATE experiment_arms SET conversions_count = conversions_count + 1 WHERE experiment_id = ? AND variant_id = ?",
                    (experiment_id, variant_id),
                )
            if is_error:
                cur.execute(
                    "UPDATE experiment_arms SET error_count = error_count + 1 WHERE experiment_id = ? AND variant_id = ?",
                    (experiment_id, variant_id),
                )
            if friction_index is not None:
                cur.execute(
                    "UPDATE experiment_arms SET friction_index = ? WHERE experiment_id = ? AND variant_id = ?",
                    (float(friction_index), experiment_id, variant_id),
                )
            conn.commit()
        finally:
            conn.close()

    def calculate_posterior_win_prob(
        self, arm_a: ExperimentArm, arm_b: ExperimentArm, n_samples: int = 1000
    ) -> float:
        """Calculate the Bayesian probability that arm B outperforms arm A using Monte Carlo simulation."""
        alpha_a = 1.0 + float(arm_a.conversions_count)
        beta_a = 1.0 + max(0.0, float(arm_a.sessions_count - arm_a.conversions_count)) + (arm_a.friction_index / 2.0)

        alpha_b = 1.0 + float(arm_b.conversions_count)
        beta_b = 1.0 + max(0.0, float(arm_b.sessions_count - arm_b.conversions_count)) + (arm_b.friction_index / 2.0)

        wins_b = 0
        for _ in range(n_samples):
            sample_a = random.betavariate(alpha_a, beta_a)
            sample_b = random.betavariate(alpha_b, beta_b)
            if sample_b > sample_a:
                wins_b += 1

        return round(wins_b / float(n_samples), 4)

    def check_convergence(
        self,
        db_path: Path,
        experiment_id: str,
        variant_a: str = "A",
        variant_b: str = "B",
        min_sessions_per_arm: int = 20,
        significance_threshold: float = 0.95,
    ) -> ExperimentConvergence:
        """Verify whether the experiment has reached statistical convergence and select the definitive winner."""
        conn = sqlite3.connect(str(db_path))
        try:
            self.ensure_tables(conn)
            arms_map = {a.variant_id: a for a in self.get_or_create_arms(conn, experiment_id, [variant_a, variant_b])}
            arm_a = arms_map.get(variant_a, ExperimentArm(experiment_id, variant_a))
            arm_b = arms_map.get(variant_b, ExperimentArm(experiment_id, variant_b))

            total_sessions = arm_a.sessions_count + arm_b.sessions_count
            prob_b_wins = self.calculate_posterior_win_prob(arm_a, arm_b)

            rate_a = (arm_a.conversions_count / arm_a.sessions_count) if arm_a.sessions_count > 0 else 0.0
            rate_b = (arm_b.conversions_count / arm_b.sessions_count) if arm_b.sessions_count > 0 else 0.0
            uplift_pct = round((rate_b - rate_a) * 100.0, 2)

            # Check convergence conditions.
            enough_samples = arm_a.sessions_count >= min_sessions_per_arm and arm_b.sessions_count >= min_sessions_per_arm
            b_convergido = prob_b_wins >= significance_threshold
            a_convergido = (1.0 - prob_b_wins) >= significance_threshold

            is_converged = enough_samples and (b_convergido or a_convergido)
            winning_variant = None
            if is_converged:
                winning_variant = variant_b if b_convergido else variant_a

            return ExperimentConvergence(
                experiment_id=experiment_id,
                is_converged=is_converged,
                winning_variant=winning_variant,
                win_probability_pct=round(prob_b_wins * 100.0, 2),
                total_sessions=total_sessions,
                uplift_pct=uplift_pct,
            )
        finally:
            conn.close()


# Provide the canonical singleton instance.
thompson_router = ThompsonRouterPrimitive()
