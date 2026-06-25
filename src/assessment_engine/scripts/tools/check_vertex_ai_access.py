"""Verifies fundamental access to Vertex AI services.

This script serves as a pre-flight check to confirm that the execution
environment possesses the necessary credentials and permissions to interact
with Google Cloud Vertex AI before initiating more complex agentic processes.
"""

from __future__ import annotations

import argparse
import logging

from assessment_engine.scripts.lib.runtime_env import run_vertex_ai_preflight

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    """Run the Vertex AI preflight check from the command line.

    This function serves as the main entry point for the script. It parses
    command-line arguments to configure the preflight check parameters, invokes
    the core check logic, and logs the resulting configuration details upon
    successful execution.

    Args:
        argv: A list of command-line arguments, excluding the script name.
            If None, `sys.argv[1:]` is used. Supports `--model` to specify
            a model name and `--timeout-seconds` to set a request timeout.
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
