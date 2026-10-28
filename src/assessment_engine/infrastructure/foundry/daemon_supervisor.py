"""
Manage background processes and local daemons (TCP readiness and sandboxing). Decoupled from workspace.py following the Strangler Fig pattern.
Provides:
- build_daemon_environment: Build an environment purged of API secrets.
- resolve_daemon_port: Resolve or dynamically reassign free TCP ports if the requested port is in use.
- poll_daemon_readiness: Poll the local TCP socket actively in a non-blocking manner.
- start_background_service: Launch daemons with Bubblewrap sandboxing (/usr/bin/bwrap).
- stop_background_service: Terminate process groups gracefully with SIGTERM -> SIGKILL escalation.
- http_health_check: Perform empirical HTTP GET checks against local services.
"""
from __future__ import annotations

import logging
import os
import re
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.config.sre_constants import (
    DEFAULT_RETRY_BACKOFF_SEC,
    HEARTBEAT_INTERVAL_SEC,
    PROCESS_STARTUP_GRACE_SEC,
)

logger = logging.getLogger("assessment_engine.infrastructure.foundry.daemon_supervisor")


def build_daemon_environment(workspace_dir: Path, factory_root: Path) -> dict[str, str]:
    """Build a clean environment for background processes by purging API secrets."""
    env_vars = os.environ.copy()
    for secret_var in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
        env_vars.pop(secret_var, None)

    local_venv_bin = workspace_dir / ".venv" / "bin"
    global_venv_bin = factory_root / "venv" / "bin"
    path_dirs = []
    if local_venv_bin.exists():
        path_dirs.append(str(local_venv_bin))
        env_vars["VIRTUAL_ENV"] = str(workspace_dir / ".venv")
    if global_venv_bin.exists():
        path_dirs.append(str(global_venv_bin))
    if path_dirs:
        env_vars["PATH"] = ":".join(path_dirs) + ":" + env_vars.get("PATH", "")
    return env_vars


def resolve_daemon_port(command: str, port: int | None) -> tuple[int | None, str]:
    """Detect or dynamically reassign a free port if the requested port is occupied."""
    def _is_port_in_use(p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", p)) == 0

    def _find_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return int(s.getsockname()[1])

    target_port = port
    if not target_port:
        m = re.search(r"--port\s+(\d+)|:(\d+)", command)
        if m:
            target_port = int(m.group(1) or m.group(2))

    if target_port and _is_port_in_use(target_port):
        free_p = _find_free_port()
        logger.info(f"Port {target_port} was busy on host. Dynamically re-routing daemon to free port {free_p}.")
        if re.search(r"--port\s+\d+", command):
            command = re.sub(r"--port\s+\d+", f"--port {free_p}", command)
        elif f":{target_port}" in command:
            command = command.replace(f":{target_port}", f":{free_p}")
        target_port = free_p

    return target_port, command


def poll_daemon_readiness(
    proc: Any, target_port: int, log_path: Path, log_file: str, timeout_seconds: int
) -> str:
    """Poll the daemon TCP socket actively until initialization completes."""
    start = time.time()
    ready = False
    while time.time() - start < timeout_seconds:
        if proc.poll() is not None:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                err = lf.read()[:600]
            return f"CRASH: Daemon (PID={proc.pid}) exited immediately with code {proc.returncode}. Log:\n{err}"
        try:
            with socket.create_connection(("127.0.0.1", target_port), timeout=0.2):
                ready = True
                break
        except (ConnectionRefusedError, OSError):
            time.sleep(HEARTBEAT_INTERVAL_SEC)

    if not ready:
        return f"TIMEOUT: Daemon (PID={proc.pid}) launched, but port {target_port} was not accessible within {timeout_seconds}s."
    return f"DAEMON_READY: PID={proc.pid} | TCP Port {target_port} OPEN | Log={log_file}"


def start_background_service_process(
    workspace_dir: Path,
    factory_root: Path,
    active_pids: set[int],
    command: str,
    port: int | None = None,
    log_file: str = "service.log",
    timeout_seconds: int = 15,
) -> str:
    """Start a background server with TCP socket verification and optional Bubblewrap sandboxing."""
    env_vars = build_daemon_environment(workspace_dir, factory_root)
    target_port, command = resolve_daemon_port(command, port)
    log_path = workspace_dir / log_file
    bwrap_bin = "/usr/bin/bwrap"
    use_bwrap = os.path.exists(bwrap_bin)

    cmd_exec: list[str] = [
        bwrap_bin,
        "--die-with-parent",
        "--ro-bind", "/", "/",
        "--dev", "/dev",
        "--proc", "/proc",
        "--tmpfs", "/tmp",
        "--bind", str(workspace_dir), str(workspace_dir),
        "--chdir", str(workspace_dir),
        "/usr/bin/bash", "-c", command
    ] if use_bwrap else ["bash", "-c", command]

    try:
        with open(log_path, "w", encoding="utf-8") as out_f:
            proc = subprocess.Popen(
                cmd_exec,
                cwd=workspace_dir,
                env=env_vars,
                stdout=out_f,
                stderr=subprocess.STDOUT,
                process_group=0
            )

        if target_port:
            status = poll_daemon_readiness(proc, target_port, log_path, log_file, timeout_seconds)
            if "DAEMON_READY" in status:
                active_pids.add(proc.pid)
            return status

        time.sleep(DEFAULT_RETRY_BACKOFF_SEC)
        active_pids.add(proc.pid)
        return f"DAEMON_STARTED: PID={proc.pid} (No TCP port probed) | Log={log_file}"
    except (subprocess.SubprocessError, OSError) as e:
        return f"DAEMON_LAUNCH_ERROR: {e!s}"


def stop_background_service_process(active_pids: set[int], pid: int) -> str:
    """Terminate a process group gracefully using SIGTERM with SIGKILL escalation."""
    try:
        active_pids.discard(pid)
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
        for _ in range(10):
            time.sleep(HEARTBEAT_INTERVAL_SEC)
            try:
                os.kill(pid, 0)
            except OSError:
                return f"DAEMON_STOPPED: PID={pid} terminated gracefully."
        os.killpg(pgid, signal.SIGKILL)
        return f"DAEMON_TERMINATED: PID={pid} force-killed with SIGKILL after timeout."
    except ProcessLookupError:
        active_pids.discard(pid)
        return f"DAEMON_INACTIVE: PID={pid} was not running."
    except (PermissionError, OSError) as e:
        return f"DAEMON_STOP_ERROR ({pid}): {e!s}"


def http_health_check_endpoint(
    url: str, expected_status: int = 200, timeout_seconds: int = 10
) -> str:
    """Execute an HTTP GET request against the service to verify its response."""
    start = time.time()
    last_err = ""
    while time.time() - start < timeout_seconds:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AutonomousFactoryValidator/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                status = resp.getcode()
                body = resp.read(1000).decode("utf-8", errors="ignore")
                if status == expected_status:
                    return f"HTTP_OK: Received {status} OK.\nBody:\n{body[:300]}"
                return f"HTTP_STATUS_MISMATCH: Status={status} (Expected={expected_status})\nBody:\n{body[:300]}"
        except urllib.error.HTTPError as e:
            if e.code == expected_status:
                return f"HTTP_OK: Received expected status {e.code}: {e.reason}"
            last_err = f"HTTP {e.code}: {e.reason}"
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = str(e)
        time.sleep(PROCESS_STARTUP_GRACE_SEC)
    return f"HTTP_CHECK_FAILED after {timeout_seconds}s. Last error: {last_err}"
