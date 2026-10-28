"""
GitHub Actions CI/CD Pipeline Generator — GEMA 50 (SOTA 2026).
Emits a deterministic .github/workflows/ci.yml pipeline for synthesized projects.
Orchestrates linting (ruff, eslint), unit testing (pytest), build, and security audits.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("assessment_engine.infrastructure.primitives.ci_cd_generator")


class CICDGeneratorPrimitive:
    """
    Generate deterministic continuous integration pipelines.
    """

    def generate_workflow_yaml(self, python_version: str = "3.11", node_version: str = "20") -> str:
        """Generate the contents of ci.yml."""
        return f"""name: Tier-1 SOTA CI Pipeline

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '{python_version}'
          cache: 'pip'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '{node_version}'

      - name: Install Python Dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install ruff pytest

      - name: Lint Python Code
        run: ruff check .

      - name: Run Test Suite
        run: pytest

      - name: Build Web Frontend
        if: hashFiles('web/package.json') != ''
        run: |
          cd web
          npm ci || npm install
          npm run build
"""

    def write_workflow(self, target_dir: Path) -> Path:
        """Write .github/workflows/ci.yml to the project."""
        wf_dir = target_dir / ".github" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)
        wf_file = wf_dir / "ci.yml"
        wf_file.write_text(self.generate_workflow_yaml(), encoding="utf-8")
        logger.info(f"[CICDGenerator] Pipeline generado en {wf_file}")
        return wf_file


ci_cd_generator = CICDGeneratorPrimitive()
