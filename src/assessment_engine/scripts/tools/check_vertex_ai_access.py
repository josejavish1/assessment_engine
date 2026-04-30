"""
Módulo check_vertex_ai_access.py.
Valida de forma explícita el acceso base a Vertex AI antes de lanzar agentes.
"""

from __future__ import annotations

import argparse

from assessment_engine.scripts.lib.runtime_env import run_vertex_ai_preflight


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=None)
    args = parser.parse_args(argv)

    result = run_vertex_ai_preflight(
        model_name=args.model,
        timeout_seconds=args.timeout_seconds,
    )
    print("✅ Vertex AI preflight passed.")
    print(f"   - project: {result['project']}")
    print(f"   - location: {result['location']}")
    print(f"   - model: {result['model']}")
    print(f"   - timeout_seconds: {result['timeout_seconds']}")


if __name__ == "__main__":
    main()
