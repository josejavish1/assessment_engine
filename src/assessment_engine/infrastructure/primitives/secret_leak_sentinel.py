"""
Secret Leak & Sensitive Credential Sentinel — GEMA 73 (SOTA 2026).
Scans codebase files for hardcoded API keys, private keys, passwords, and tokens.
Generates safe .env.example templates automatically.
Protects repository integrity against credential exposure accidents.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.secret_leak_sentinel")


class SecretLeakSentinelPrimitive:
    """
    Centinela anti-fugas de secretos y credenciales.
    """

    PATTERNS = {
        "gemini_api_key": re.compile(r"AIza[0-9A-Za-z-_]{35}"),
        "stripe_secret": re.compile(r"sk_(live|test)_[0-9a-zA-Z]{24,}"),
        "github_token": re.compile(r"ghp_[0-9a-zA-Z]{36}"),
        "private_key": re.compile(r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----"),
        "jwt_token": re.compile(r"ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*")
    }

    def scan_file_for_leaks(self, file_path: Path) -> list[dict[str, Any]]:
        """Scan a file for potential exposed secrets."""
        if not file_path.exists() or file_path.is_dir():
            return []

        # Omitir archivos binarios y venvs
        if file_path.suffix in (".pyc", ".db", ".png", ".jpg", ".svg", ".lock"):
            return []

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        findings = []

        for name, pat in self.PATTERNS.items():
            for m in pat.finditer(text):
                # Discard if it is a placeholder or an example comment.
                matched = m.group(0)
                if any(ex in matched.lower() for ex in ["example", "sample", "your_", "dummy"]):
                    continue
                findings.append({
                    "file": file_path.name,
                    "secret_type": name,
                    "preview": matched[:6] + "..." + matched[-4:]
                })

        return findings

    def generate_env_example(self, env_file: Path) -> str:
        """Generate a secure .env.example from an existing .env by clearing actual values."""
        if not env_file.exists():
            return "# .env.example\nAPP_ENV=production\nPORT=8000\nSECRET_KEY=your_secret_key_here\n"

        lines = []
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                lines.append(line)
            elif "=" in line:
                k, _ = line.split("=", 1)
                lines.append(f"{k}=your_{k.lower()}_here")

        return "\n".join(lines) + "\n"


secret_leak_sentinel = SecretLeakSentinelPrimitive()
