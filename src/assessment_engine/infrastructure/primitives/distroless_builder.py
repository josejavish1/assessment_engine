"""
Google Distroless Multi-Stage Containerfile Generator — GEMA 48 (SOTA 2026).
Compiles a minimal, immutable Dockerfile using Google Container Tools Distroless.
Stage 1: Python builder with dependencies.
Stage 2: Distroless non-root runtime without shells, package managers, or root privileges (<60MB).
Zero attack surface for production deployment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("assessment_engine.infrastructure.primitives.distroless_builder")


@dataclass
class ContainerfileConfig:
    python_version: str = "3.11"
    distroless_base: str = "gcr.io/distroless/python3-debian12:nonroot"
    app_port: int = 8000


class DistrolessBuilderPrimitive:
    """
    Generate a multi-stage Dockerfile using Google Distroless.
    """

    def __init__(self, config: ContainerfileConfig | None = None) -> None:
        self.config = config or ContainerfileConfig()

    def generate_dockerfile(self) -> str:
        """Generate the deterministic Containerfile content."""
        return f"""# ETAPA 1: Builder
FROM python:{self.config.python_version}-slim AS builder
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM {self.config.distroless_base}
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \\
    PATH=/root/.local/bin:$PATH \\
    PYTHONPATH=/root/.local/lib/python{self.config.python_version}/site-packages:/app

COPY --from=builder /root/.local /root/.local
COPY . /app

USER nonroot
EXPOSE {self.config.app_port}

ENTRYPOINT ["python3", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "{self.config.app_port}"]
"""

    def write_dockerfile(self, target_dir: Path) -> Path:
        """Write the Dockerfile to the target directory."""
        out = target_dir / "Dockerfile"
        out.write_text(self.generate_dockerfile(), encoding="utf-8")
        logger.info(f"[DistrolessBuilder] Dockerfile generado en {out}")
        return out


distroless_builder = DistrolessBuilderPrimitive()
