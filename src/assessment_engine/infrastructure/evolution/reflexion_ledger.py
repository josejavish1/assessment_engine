"""
Provide an episodic memory and continuous learning ledger. Based on the Reflexion framework (Princeton / NeurIPS 2023) and iterative self-play:
1. Store empirically detected failure anti-patterns in SQLite WAL.
2. Track error frequencies to prioritize corrective axioms.
3. Inject hard constraints (preflight axioms) during the mission planning phase.
4. Prevent recurring dependency, syntax, or authority boundary errors.
"""
from __future__ import annotations

import hashlib
import logging
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.evolution.reflexion_ledger")


@dataclass(frozen=True)
class FailureAntipattern:
    """Represent an atomic record of a failure anti-pattern in the repository."""
    category: str
    error_signature: str
    target_ext: str
    corrective_axiom: str
    frequency: int
    culprit_pattern: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class ContrastiveExemplar:
    """Represent a contrastive pair (erroneous snippet vs. verified surgical diff)."""
    category: str
    task_hint: str
    failed_snippet: str
    verified_diff: str
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return asdict(self)


class ReflexionLedger:
    """
    Manage SQLite relational memory for orchestrator self-training.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            base_dir = Path.cwd() / ".evolution"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "reflexion_ledger.db"
        else:
            self.db_path = db_path
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()
        self._seed_foundational_axioms()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS failure_antipatterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    error_signature TEXT NOT NULL UNIQUE,
                    target_ext TEXT NOT NULL,
                    culprit_pattern TEXT,
                    corrective_axiom TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_hash TEXT NOT NULL,
                    component_rel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    iterations INTEGER NOT NULL,
                    timestamp REAL NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contrastive_exemplars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    task_hint TEXT NOT NULL,
                    failed_snippet TEXT NOT NULL,
                    verified_diff TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
            """)
            conn.commit()

    def _seed_foundational_axioms(self) -> None:
        """Pre-seed core lessons learned to protect the baseline."""
        foundational = [
            (
                "DEP_UNINSTALLED",
                "TS2307_CANNOT_FIND_MODULE",
                ".tsx",
                "@tanstack/react-virtual",
                "Prohibited from importing third-party libraries missing from package.json. Use native primitives at $0.00 marginal cost.",
            ),
            (
                "AUTHORITY_TAMPERING",
                "CLIENT_SIDE_STATE_TAMPERING",
                ".tsx",
                "localStorage.setItem('xp', ...)",
                "Prohibited from mutating balances or XP in localStorage. Backend is sole authoritative source; client only renders state.",
            ),
            (
                "SYNTAX_CORRUPTION",
                "SYNTAX_MEMO_CLOSURE_ERROR",
                ".tsx",
                "React.memo(...); };",
                "In TypeScript/React, components or functions wrapped in React.memo must terminate with '});' and never '};'.",
            ),
            (
                "ARCH_NESTING",
                "JSX_NESTING_FALSE_POSITIVE",
                ".tsx",
                "<Badge><div...",
                "Nested JSX in React components does not constitute cyclomatic control-flow complexity; do not apply guard clauses to visual tags.",
            ),
            (
                "CODE_HYGIENE",
                "PYTHON_COMMENT_IN_TYPESCRIPT",
                ".tsx",
                "# comment in tsx",
                "Strictly use '//' and '/* ... */' for comments in TypeScript/JavaScript, and '#' exclusively in Python.",
            ),
            (
                "AUTH_SECURITY",
                "AUTH_STRING_MATCHING_BYPASS",
                ".py",
                "request.url.path.startswith(...) for auth",
                "Prohibited from protecting backend routes by string parsing request.url.path in middlewares. In FastAPI, security must be declarative via dependencies=[Depends(guard)] in app.include_router().",
            ),
            (
                "TEST_DRIFT",
                "TEST_MOCK_ENDPOINT_DRIFT",
                ".py",
                "client.get('/api/fake/endpoint')",
                "Prohibited from evaluating security or authorizations against fictitious endpoints in tests. Assertions must strictly target real routes registered in app.routes.",
            ),
            (
                "PERF_CWV",
                "CWV_LCP_SLOW_IMAGE",
                ".tsx",
                'loading="lazy" on hero',
                "To guarantee LCP <= 2.5s, critical above-the-fold hero images must declare fetchpriority='high' and never loading='lazy'.",
            ),
            (
                "PERF_CWV",
                "CWV_CLS_UNSIZED_MEDIA",
                ".tsx",
                "<img without dimensions>",
                "Every visual <img> or iframe must declare explicit width and height attributes or aspect-ratio container to enforce CLS <= 0.1.",
            ),
            (
                "PERF_CWV",
                "CWV_INP_LONG_TASK",
                ".tsx",
                "synchronous blocking loop > 50ms",
                "Break down heavy main-thread compute via scheduler.yield() or Web Workers to keep tasks < 50ms and INP <= 200ms.",
            ),
        ]

        now = time.time()
        with self._get_connection() as conn:
            for cat, sig, ext, culp, axiom in foundational:
                conn.execute("""
                    INSERT INTO failure_antipatterns (
                        category, error_signature, target_ext, culprit_pattern, corrective_axiom, frequency, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    ON CONFLICT(error_signature) DO UPDATE SET
                        corrective_axiom = excluded.corrective_axiom,
                        updated_at = excluded.updated_at;
                """, (cat, sig, ext, culp, axiom, now, now))
            conn.commit()

    def record_failure(
        self,
        category: str,
        error_signature: str,
        target_file: str,
        corrective_axiom: str,
        culprit_pattern: str = "",
    ) -> None:
        """Record a failure or increment its recurrence frequency."""
        ext = Path(target_file).suffix.lower() or ".unknown"
        now = time.time()

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO failure_antipatterns (
                    category, error_signature, target_ext, culprit_pattern, corrective_axiom, frequency, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(error_signature) DO UPDATE SET
                    frequency = frequency + 1,
                    corrective_axiom = excluded.corrective_axiom,
                    updated_at = excluded.updated_at;
            """, (category, error_signature, ext, culprit_pattern, corrective_axiom, now, now))
            conn.commit()
            logger.info(f"[ReflexionLedger] Anti-pattern '{error_signature}' recorded/updated in memory.")

    def record_antipattern(
        self,
        category: str,
        error_signature: str,
        target_ext: str = ".json",
        corrective_axiom: str = "",
        culprit_pattern: str = "",
    ) -> None:
        """Record an antipattern or learned corrective axiom into persistent memory."""
        self.record_failure(
            category=category,
            error_signature=error_signature,
            target_file=target_ext,
            corrective_axiom=corrective_axiom,
            culprit_pattern=culprit_pattern,
        )

    def record_episode(
        self,
        task: str,
        component_rel: str,
        status: str,
        iterations: int,
    ) -> None:
        """Archive the outcome of an evolutionary mission."""
        task_hash = hashlib.sha256(task.strip().encode("utf-8")).hexdigest()[:16]
        now = time.time()

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO execution_episodes (task_hash, component_rel, status, iterations, timestamp)
                VALUES (?, ?, ?, ?, ?);
            """, (task_hash, component_rel, status, iterations, now))
            conn.commit()

    def get_preflight_axioms(
        self, target_file_or_task: str, limit: int = 8, category: str | None = None
    ) -> list[str]:
        """
        Return high-priority corrective axioms applicable to the target file or task.
        """
        ext = Path(target_file_or_task).suffix.lower()

        with self._get_connection() as conn:
            if category:
                cursor = conn.execute("""
                    SELECT category, corrective_axiom, frequency 
                    FROM failure_antipatterns 
                    WHERE category = ?
                    ORDER BY updated_at DESC, frequency DESC
                    LIMIT ?;
                """, (category, limit))
            elif ext:
                cursor = conn.execute("""
                    SELECT category, corrective_axiom, frequency 
                    FROM failure_antipatterns 
                    WHERE target_ext = ? OR target_ext = '.all'
                    ORDER BY frequency DESC, updated_at DESC
                    LIMIT ?;
                """, (ext, limit))
            else:
                cursor = conn.execute("""
                    SELECT category, corrective_axiom, frequency 
                    FROM failure_antipatterns 
                    ORDER BY frequency DESC, updated_at DESC
                    LIMIT ?;
                """, (limit,))

            rows = cursor.fetchall()

        axioms: list[str] = []
        for cat, axiom, freq in rows:
            axioms.append(f"[{cat}] {axiom} (Historical frequency: {freq})")

        return axioms

    def record_contrastive_exemplar(
        self,
        category: str,
        task_hint: str,
        failed_snippet: str,
        verified_diff: str,
    ) -> None:
        """Record a contrastive pair (failing snippet vs. surgical diff that passed the gate)."""
        now = time.time()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO contrastive_exemplars (category, task_hint, failed_snippet, verified_diff, created_at)
                VALUES (?, ?, ?, ?, ?);
            """, (category, task_hint, failed_snippet[:2000], verified_diff[:3000], now))
            conn.commit()
            logger.info(f"[ReflexionLedger] Contrastive pair archived for '{task_hint}' ({category}).")

    def get_contrastive_exemplars(self, task_hint: str, limit: int = 2) -> list[ContrastiveExemplar]:
        """Retrieve the most recent contrastive surgical diffs related to the task or component."""
        ext = Path(task_hint).suffix.lower()
        stem = Path(task_hint).stem.lower()
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT category, task_hint, failed_snippet, verified_diff, created_at
                FROM contrastive_exemplars
                WHERE task_hint LIKE ? OR task_hint LIKE ? OR task_hint LIKE ?
                ORDER BY created_at DESC
                LIMIT ?;
            """, (f"%{ext}%", f"%{stem}%", "%", limit))
            rows = cursor.fetchall()

        return [
            ContrastiveExemplar(
                category=r[0],
                task_hint=r[1],
                failed_snippet=r[2],
                verified_diff=r[3],
                created_at=r[4],
            )
            for r in rows
        ]

    def format_preflight_prompt_block(self, target_file_or_task: str) -> str:
        """Format axioms and contrastive exemplars into a Markdown block ready for LLM injection."""
        axioms = self.get_preflight_axioms(target_file_or_task)
        exemplars = self.get_contrastive_exemplars(target_file_or_task, limit=1)

        if not axioms and not exemplars:
            return ""

        lines: list[str] = []
        if axioms:
            lines.append("### PRIOR EMPIRICAL LEARNING AXIOMS (REFLEXION LEDGER - DO NOT REPEAT):")
            for idx, ax in enumerate(axioms, 1):
                lines.append(f"{idx}. {ax}")
            lines.append("All synthesized code must strictly adhere to these axioms before compilation.\n")

        if exemplars:
            lines.append("### PRIOR CONTRASTIVE SURGICAL PATCH EXEMPLARS (GROUND-TRUTH FEW-SHOT):")
            for ex in exemplars:
                lines.append(f"// Caso: {ex.category} en '{ex.task_hint}'")
                lines.append(f"// Verified Surgical Diff passing quality gates:\n{ex.verified_diff}\n")

        return "\n".join(lines)


reflexion_ledger = ReflexionLedger()
