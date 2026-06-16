"""
Módulo check_vertex_ai_access.py.
Valida de forma explícita el acceso base a Vertex AI antes de lanzar agentes.
"""

from __future__ import annotations

import argparse
import logging

from assessment_engine.scripts.lib.runtime_env import run_vertex_ai_preflight

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=None)
    args = parser.parse_args(argv)

    result = run_vertex_ai_preflight(
        model_name=args.model,
        timeout_seconds=args.timeout_seconds,
    )
    logger.info("✅ Vertex AI preflight passed.")
    logger.info(f"   - project: {result['project']}")
    logger.info(f"   - location: {result['location']}")
    logger.info(f"   - model: {result['model']}")
    logger.info(f"   - timeout_seconds: {result['timeout_seconds']}")


if __name__ == "__main__":
    main()
