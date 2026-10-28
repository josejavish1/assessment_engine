"""
Provide isolated Bash command execution using Linux Bubblewrap (bwrap). Decoupled from workspace.py using the Strangler Fig pattern. Provides:
- check_bash_security_rules: Guard against destructive commands, GCP metadata SSRF, and credential access.
- prepare_sanitized_bash_env: Purge API keys and configure a hermetic PATH.
- build_bubblewrap_command: Assemble the bwrap sandbox with tmpfs over sensitive host paths.
- execute_sandboxed_bash: Execute commands non-interactively with timeouts and output capture.
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger("assessment_engine.infrastructure.foundry.bubblewrap_executor")


def check_bash_security_rules(command: str) -> tuple[str | None, str | None]:
    """Check for destructive commands, SSRF to GCP metadata, and host credentials.
Return (error_msg, security_alert_reason) or (None, None)."""
    destructive = ["rm -rf /", ":(){ :|:& };:", "mkfs", "dd if="]
    for pattern in destructive:
        if pattern in command:
            return (
                f"SECURITY_ERROR: Prohibited command detected ({pattern}). Aborted.",
                f"Comando destructivo ({pattern}) bloqueado"
            )

    metadata = ["169.254.169.254", "metadata.google.internal", "metadata.goog"]
    for meta in metadata:
        if meta in command:
            return (
                f"SECURITY_ERROR: Access to GCP Cloud Metadata Server ({meta}) is prohibited by Execution Guard.",
                f"SSRF a metadatos de GCP ({meta}) bloqueado"
            )

    sensitive = [".ssh", "id_rsa", "id_ed25519", "sa-key.json", "GOOGLE_APPLICATION_CREDENTIALS", "/etc/shadow"]
    for sens in sensitive:
        if sens in command:
            return (
                f"SECURITY_ERROR: Prohibited access to credential artifact ({sens}) detected by Execution Guard.",
                f"Acceso a credencial ({sens}) bloqueado"
            )

    return None, None


def prepare_sanitized_bash_env(workspace_dir: Path, factory_root: Path) -> dict[str, str]:
    """Sanitize environment variables and configure PATH for local virtual environments."""
    env_vars = os.environ.copy()
    for secret_var in [
        "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS",
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GCP_PROJECT", "CLOUDSDK_AUTH_ACCESS_TOKEN"
    ]:
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

    src_dir = workspace_dir / "src"
    if src_dir.exists():
        env_vars["PYTHONPATH"] = f"{src_dir}:{env_vars.get('PYTHONPATH', '')}"

    env_vars["npm_config_cache"] = "/tmp/npm-cache"
    env_vars["NPM_CONFIG_CACHE"] = "/tmp/npm-cache"
    return env_vars


def build_bubblewrap_command(
    bwrap_bin: str, workspace_dir: Path, factory_root: Path, command: str
) -> list[str]:
    """Build the hermetic Bubblewrap command with tmpfs over sensitive host paths."""
    sensitive_masks = [
        str(Path.home() / ".ssh"),
        str(Path.home() / ".gemini"),
        str(factory_root / "credentials")
    ]
    bwrap_args = [
        bwrap_bin,
        "--die-with-parent",
        "--ro-bind", "/", "/",
        "--dev", "/dev",
        "--proc", "/proc",
        "--tmpfs", "/tmp",
    ]
    for mask_path in sensitive_masks:
        if os.path.exists(mask_path):
            bwrap_args.extend(["--tmpfs", mask_path])

    bwrap_args.extend([
        "--bind", str(workspace_dir), str(workspace_dir),
        "--chdir", str(workspace_dir),
        "/usr/bin/bash", "-c", command
    ])
    return bwrap_args


def execute_sandboxed_bash(
    workspace_dir: Path, factory_root: Path, command: str, timeout: int = 120
) -> str:
    """Execute a bash command with Linux Bubblewrap isolation and environment sanitization."""
    sec_err, _ = check_bash_security_rules(command)
    if sec_err:
        return sec_err

    env_vars = prepare_sanitized_bash_env(workspace_dir, factory_root)
    bwrap_bin = "/usr/bin/bwrap"
    use_bwrap = os.path.exists(bwrap_bin)
    cmd_exec = (
        build_bubblewrap_command(bwrap_bin, workspace_dir, factory_root, command)
        if use_bwrap
        else ["bash", "-c", command]
    )

    try:
        proc = subprocess.run(
            cmd_exec,
            cwd=workspace_dir,
            env=env_vars,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        out = f"[EXIT CODE: {proc.returncode}]\n"
        if proc.stdout:
            if len(proc.stdout) > 4000:
                out += f"STDOUT (tail):\n{proc.stdout[-4000:]}\n"
            else:
                out += proc.stdout
        if proc.stderr:
            if len(proc.stderr) > 4000:
                out += f"\n[STDERR (tail)]\n{proc.stderr[-4000:]}"
            else:
                out += f"\n[STDERR]\n{proc.stderr}"
        return out
    except subprocess.TimeoutExpired:
        return f"[EXIT CODE: 124]\nTIMEOUT: Command '{command[:60]}...' exceeded {timeout} seconds limit."
    except (subprocess.SubprocessError, OSError) as e:
        return f"[EXIT CODE: 1]\nEXECUTION_ERROR: {e!s}"
