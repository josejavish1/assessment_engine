"""The `check_vertex_ai_access.py` module.

Provides functionality to explicitly validate foundational access to Vertex AI. This pre-flight check is intended to run prior to agent instantiation to ensure proper credentials and permissions are configured.
"""

from __future__ import annotations

import argparse
import logging

from infrastructure.runtime_env import run_vertex_ai_preflight

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    """Executes the Vertex AI preflight check from the command line.

    Parses command-line arguments for the model name and timeout duration. It then
    invokes the preflight check routine and logs the details of a successful
    verification, including project, location, and model information.

    Args:
        argv: An optional list of command-line arguments. If None, `sys.argv[1:]`
            is used by the argument parser.

    Raises:
        KeyError: If the dictionary returned by the preflight check is missing
            an expected key, such as 'project' or 'location'.
    """
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
