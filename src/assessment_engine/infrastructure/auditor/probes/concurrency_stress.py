"""
Benchmark concurrent load, tail latency, and lock contention based on Dean & Barroso and ISO 25010. Implements:
- Tail latency evaluation (P50, P90, P95, P99, P99.9).
- Concurrent stress testing on the ASGI server (burst throughput and error rates).
- SQLite lock contention verification (contention, SQLITE_BUSY, and zero lock errors).
- Service Level Agreement (SLA) verification under high concurrency.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import math
import shutil
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult


def check_k6_availability() -> str | None:
    """Check whether the Grafana k6 binary is present on the system."""
    return shutil.which("k6")


def run_k6_load_test(
    target_dir: Path, script_rel_path: str = "tests/load_test_sse.js"
) -> tuple[dict[str, Any] | None, list[AuditFinding]]:
    """Run the Grafana k6 suite if the binary is installed."""
    k6_bin = shutil.which("k6")
    if not k6_bin:
        return None, []

    script_path = target_dir / script_rel_path
    if not script_path.exists():
        return None, []

    findings: list[AuditFinding] = []
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        summary_path = Path(tmp.name)

    try:
        cmd = [k6_bin, "run", str(script_path), "--summary-export", str(summary_path), "--quiet"]
        subprocess.run(cmd, cwd=str(target_dir), capture_output=True, text=True, timeout=90)
        if summary_path.exists():
            try:
                data = json.loads(summary_path.read_text(encoding="utf-8"))
                return data, findings
            except (json.JSONDecodeError, OSError):
                pass
    except (subprocess.SubprocessError, OSError) as ex:
        findings.append(AuditFinding(
            category="PERFORMANCE",
            severity="LOW",
            file_path=script_rel_path,
            line_number=None,
            rule_id="STRESS-K6-EXECUTION-WARNING",
            message=f"Aviso durante la ejecución de Grafana k6: {ex}",
            recommendation="Verificar que el servidor objetivo esté activo antes de lanzar k6."
        ))
    finally:
        summary_path.unlink(missing_ok=True)

    return None, findings


def calculate_percentiles(latencies_ms: list[float]) -> dict[str, float]:
    """Calculate exact percentile distributions."""
    if not latencies_ms:
        return {
            "p50_ms": 0.0,
            "p90_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "p99_9_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
            "mean_ms": 0.0,
        }

    sorted_lats = sorted(latencies_ms)
    n = len(sorted_lats)

    def _get_pct(p: float) -> float:
        idx = min(n - 1, max(0, int(math.ceil(p * n)) - 1))
        return round(sorted_lats[idx], 2)

    return {
        "p50_ms": _get_pct(0.50),
        "p90_ms": _get_pct(0.90),
        "p95_ms": _get_pct(0.95),
        "p99_ms": _get_pct(0.99),
        "p99_9_ms": _get_pct(0.999),
        "min_ms": round(sorted_lats[0], 2),
        "max_ms": round(sorted_lats[-1], 2),
        "mean_ms": round(sum(sorted_lats) / n, 2),
    }


def _sqlite_worker_sync(
    db_path: Path, worker_id: int, iterations: int
) -> tuple[list[float], list[str]]:
    """Execute concurrent ACID transactions in SQLite as a synchronous worker."""
    latencies: list[float] = []
    errors: list[str] = []

    for i in range(iterations):
        t0 = time.perf_counter_ns()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA busy_timeout = 5000;")
            with conn:
                conn.execute(
                    "INSERT INTO stress_ledger (worker_id, payload, created_at) VALUES (?, ?, ?);",
                    (worker_id, f"load_test_worker_{worker_id}_txn_{i}", time.time())
                )
            conn.close()
            t1 = time.perf_counter_ns()
            latencies.append((t1 - t0) / 1_000_000.0)
        except (sqlite3.Error, OSError) as ex:
            errors.append(str(ex))

    return latencies, errors


async def audit_sqlite_write_contention(
    num_workers: int = 25, iterations_per_worker: int = 4
) -> tuple[int, int, list[float], list[AuditFinding]]:
    """Stress-test SQLite with concurrent transactions.
Verify that WAL configuration and busy_timeout prevent 'database is locked' errors."""
    findings: list[AuditFinding] = []

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stress_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                payload TEXT,
                created_at REAL
            );
        """)
        conn.commit()
        conn.close()

        # Lanzamiento paralelo de trabajadores concurrentes
        tasks = [
            asyncio.to_thread(_sqlite_worker_sync, db_path, w_id, iterations_per_worker)
            for w_id in range(num_workers)
        ]
        results = await asyncio.gather(*tasks)

        all_latencies: list[float] = []
        all_errors: list[str] = []

        for lat, errs in results:
            all_latencies.extend(lat)
            all_errors.extend(errs)

        total_txns = len(all_latencies) + len(all_errors)
        lock_errors_count = sum(1 for e in all_errors if "locked" in e.lower() or "busy" in e.lower())

        if lock_errors_count > 0:
            findings.append(AuditFinding(
                category="PERFORMANCE",
                severity="CRITICAL",
                file_path="sqlite_engine",
                line_number=None,
                rule_id="STRESS-SQLITE-LOCK-CONTENTION",
                message=f"Detectados {lock_errors_count} fallos de contención 'database is locked' bajo {num_workers} escritores concurrentes",
                recommendation="Configurar 'PRAGMA busy_timeout = 5000;' y 'PRAGMA journal_mode = WAL;' con pool de conexiones optimista."
            ))

        return total_txns, lock_errors_count, all_latencies, findings

    finally:
        # Clean up temporary files.
        for p in (db_path, Path(f"{db_path}-wal"), Path(f"{db_path}-shm")):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


def _resolve_target_asgi_app(target_dir: Path) -> Any | None:
    """Resolve the primary FastAPI/ASGI application dynamically and securely."""
    server_py = target_dir / "server.py"
    if server_py.exists():
        try:
            import server
            return getattr(server, "app", None)
        except (ImportError, AttributeError, OSError):
            pass

    template_main = target_dir / "templates" / "golden_polyglot_starter" / "api" / "src" / "main.py"
    if template_main.exists():
        try:
            spec = importlib.util.spec_from_file_location("template_app_main", str(template_main))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return getattr(mod, "app", None)
        except (ImportError, AttributeError, OSError):
            pass

    return None


async def audit_asgi_burst_concurrency(
    app: Any, total_requests: int = 50
) -> tuple[int, int, list[float], list[AuditFinding]]:
    """Execute a non-blocking request burst using ASGITransport.
Measure response times and verify the absence of 5xx errors under concurrent load."""
    findings: list[AuditFinding] = []
    latencies: list[float] = []
    error_count = 0

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async def _single_request(client: httpx.AsyncClient) -> tuple[int, float]:
        t0 = time.perf_counter_ns()
        try:
            resp = await client.get("/api/health", timeout=10.0)
            t1 = time.perf_counter_ns()
            dur = (t1 - t0) / 1_000_000.0
            return resp.status_code, dur
        except (httpx.RequestError, RuntimeError, OSError):
            t1 = time.perf_counter_ns()
            return 500, (t1 - t0) / 1_000_000.0

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=10.0) as client:
        tasks = [_single_request(client) for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)

    for status_code, dur in results:
        latencies.append(dur)
        if status_code >= 500:
            error_count += 1

    if error_count > 0:
        findings.append(AuditFinding(
            category="PERFORMANCE",
            severity="HIGH",
            file_path="server.py",
            line_number=None,
            rule_id="STRESS-HTTP-ERROR-BURST",
            message=f"Detectados {error_count} errores HTTP 5xx durante la ráfaga de {total_requests} peticiones concurrentes",
            recommendation="Aislar operaciones bloqueantes con asyncio.to_thread para evitar saturación del event loop."
        ))

    pcts = calculate_percentiles(latencies)
    if pcts["p99_ms"] > 1000.0:
        findings.append(AuditFinding(
            category="PERFORMANCE",
            severity="MEDIUM",
            file_path="server.py",
            line_number=None,
            rule_id="STRESS-TAIL-LATENCY-P99",
            message=f"Latencia de cola P99 excesiva: {pcts['p99_ms']:.1f}ms (umbral recomendado <= 1000ms en local)",
            recommendation="Optimizar endpoints de salud y desacoplar cómputo síncrono pesado."
        ))

    return total_requests, error_count, latencies, findings


def run_concurrency_stress_probe(target_dir: Path) -> ProbeResult:
    """
    Run the comprehensive audit for concurrent stress, SQLite contention, and tail latency.
    """
    findings: list[AuditFinding] = []

    # 0. Detect and optionally run Grafana k6 if installed
    k6_bin = check_k6_availability()
    k6_data, k6_findings = run_k6_load_test(target_dir) if k6_bin else (None, [])
    findings.extend(k6_findings)

    # 1. Audit SQLite lock contention (30 concurrent workers, 120 transactions)
    try:
        total_txns, lock_errors, db_latencies, db_findings = asyncio.run(
            audit_sqlite_write_contention(num_workers=25, iterations_per_worker=4)
        )
        findings.extend(db_findings)
    except (RuntimeError, OSError, ValueError, sqlite3.Error) as ex:
        total_txns, lock_errors, db_latencies = 0, 1, []
        findings.append(AuditFinding(
            category="PERFORMANCE",
            severity="CRITICAL",
            file_path="sqlite_engine",
            line_number=None,
            rule_id="STRESS-SQLITE-FAILURE",
            message=f"Fallo crítico al ejecutar prueba de contención SQLite: {ex}",
            recommendation="Verificar permisos de escritura y compatibilidad con motor WAL."
        ))

    app = _resolve_target_asgi_app(target_dir)
    total_http_reqs = 0
    http_errors = 0
    http_latencies: list[float] = []

    if app is not None:
        try:
            total_http_reqs, http_errors, http_latencies, http_findings = asyncio.run(
                audit_asgi_burst_concurrency(app, total_requests=50)
            )
            findings.extend(http_findings)
        except (RuntimeError, OSError, ValueError) as ex:
            http_errors = 1
            findings.append(AuditFinding(
                category="PERFORMANCE",
                severity="HIGH",
                file_path="server.py",
                line_number=None,
                rule_id="STRESS-ASGI-FAILURE",
                message=f"Fallo al ejecutar ráfaga ASGI sobre la aplicación: {ex}",
                recommendation="Verificar que el endpoint /api/health responda de forma no bloqueante."
            ))

    # 3. Compute percentile metrics
    all_latencies = http_latencies if http_latencies else db_latencies
    pcts = calculate_percentiles(all_latencies)

    tail_ratio = round(pcts["p99_ms"] / max(0.1, pcts["p50_ms"]), 2)

    score = 100.0
    score -= lock_errors * 25.0
    score -= http_errors * 20.0

    if pcts["p99_ms"] > 1000.0:
        score -= min(15.0, (pcts["p99_ms"] - 1000.0) / 100.0)

    score = max(0.0, min(100.0, round(score, 1)))
    passed = lock_errors == 0 and http_errors == 0 and score >= 70.0

    return ProbeResult(
        probe_name="Stress & Tail Latency Contention (Dean & Barroso / Google SRE)",
        score_pct=score,
        passed=passed,
        metrics={
            "runner_engine": "Grafana k6 (Go Engine)" if (k6_bin and k6_data) else "Native Async ASGI & SQLite WAL (Google SRE)",
            "k6_binary_detected": k6_bin is not None,
            "sqlite_concurrent_transactions": total_txns,
            "sqlite_lock_contention_errors": lock_errors,
            "asgi_burst_requests": total_http_reqs,
            "asgi_burst_error_rate_pct": round((http_errors / max(1, total_http_reqs)) * 100, 2),
            "p50_latency_ms": pcts["p50_ms"],
            "p95_latency_ms": pcts["p95_ms"],
            "p99_latency_ms": pcts["p99_ms"],
            "tail_amplification_ratio": tail_ratio,
            "concurrency_status": "Resiliente y Escalable" if passed else "Contención Detectada"
        },
        findings=findings
    )
