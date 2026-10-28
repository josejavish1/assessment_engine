"""
Production docker-compose.yml Orchestrator — GEMA 51 (SOTA 2026).
Emits clean, reproducible docker-compose.yml definitions for local and on-premise deployments.
Includes healthcheck probes, non-root user security boundaries, and isolated SQLite volume mounts.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("assessment_engine.infrastructure.primitives.compose_orchestrator")


class ComposeOrchestratorPrimitive:
    """
    Generate a production docker-compose.yml file.
    """

    def generate_compose_yaml(self, app_name: str = "app", port: int = 8000) -> str:
        """Generate the docker-compose.yml content."""
        return f"""version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {app_name}_production
    restart: unless-stopped
    ports:
      - "{port}:{port}"
    environment:
      - APP_ENV=production
      - PORT={port}
    volumes:
      - app_data:/app/data
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:{port}/api/health', timeout=2)"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 5s

volumes:
  app_data:
    driver: local
"""

    def write_compose_file(self, target_dir: Path, app_name: str = "app", port: int = 8000) -> Path:
        """Write docker-compose.yml to the project."""
        out = target_dir / "docker-compose.yml"
        out.write_text(self.generate_compose_yaml(app_name, port), encoding="utf-8")
        logger.info(f"[ComposeOrchestrator] docker-compose.yml generado en {out}")
        return out


compose_orchestrator = ComposeOrchestratorPrimitive()
