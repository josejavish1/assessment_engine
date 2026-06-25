"""Contains the primary logic and utility functions for the Assessment Engine's AI client pipeline."""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from vertexai.agent_engines import AdkApp

from assessment_engine.scripts.lib.json_from_model import parse_json_from_text
from assessment_engine.scripts.lib.runtime_env import get_vertex_query_timeout_seconds

#
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A global semaphore to limit concurrent requests to the AI service, preventing rate-limiting errors and managing resource contention.
VERTEX_CONCURRENCY_LIMIT = 5
_vertex_semaphore = asyncio.Semaphore(VERTEX_CONCURRENCY_LIMIT)


class VertexQueryTimeoutError(RuntimeError):
    """Raised when a query to the Vertex AI service exceeds the configured timeout period."""


def extract_model_text(event: Any) -> Optional[str]:
    """Extracts the text content from a model response event.

    This function safely traverses a dictionary, typically representing a JSON
    object from a streaming API, to find and return the core text payload.
    It specifically searches for the text within the first valid part of a
    content block.

    Args:
        event (Any): The model response event object. The function is designed
            to parse a dictionary with a structure such as
            `{'content': {'parts': [{'text': 'some_text'}]}}`.

    Returns:
        Optional[str]: The extracted text string if found. Returns None if the
            event is not a dictionary, or if the expected nested structure and
            keys are absent.
    """
    if isinstance(event, dict):
        content = event.get("content", {})
        parts = content.get("parts", [])
        for part in parts:
            if isinstance(part, dict) and "text" in part:
                return str(part["text"])
    return None


@retry(
    retry=retry_if_exception(lambda exc: not isinstance(exc, VertexQueryTimeoutError))
    & retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.INFO),
    reraise=True,
)
async def _execute_query_with_retry(
    app: AdkApp, user_id: str, message: str
) -> Tuple[str, List[str]]:
    """Executes a query against the AI agent, incorporating a retry mechanism to handle transient failures."""
    async with _vertex_semaphore:
        lines = []
        last_text = None
        timeout_seconds = get_vertex_query_timeout_seconds()
        try:
            async with asyncio.timeout(timeout_seconds):
                async for event in app.async_stream_query(
                    user_id=user_id,
                    message=message,
                ):
                    lines.append(str(event))
                    text = extract_model_text(event)
                    if text:
                        last_text = text
        except TimeoutError as exc:
            raise VertexQueryTimeoutError(
                f"Vertex agent query timed out after {timeout_seconds:.0f}s for user_id={user_id}."
            ) from exc

        if not last_text:
            raise RuntimeError("Respuesta vacía o incompleta del modelo.")

        return last_text, lines


def _robust_unwrap_and_validate(data: Any, schema: Any) -> Any:
    """Attempts to validate input data against a Pydantic schema, with specific handling for common nested data structures."""
    try:
        return schema.model_validate(data).model_dump(by_alias=True)
    except Exception as e:
        if isinstance(data, dict):
            if len(data) == 1:
                first_val = list(data.values())[0]
                if isinstance(first_val, (dict, list)):
                    return _robust_unwrap_and_validate(first_val, schema)
            for v in data.values():
                if isinstance(v, (dict, list)):
                    try:
                        return schema.model_validate(v).model_dump(by_alias=True)
                    except Exception:
                        pass
        logger.error(
            f"Fallo de validación SRE. Keys del JSON recibido: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        )
        raise e


# Estimated pricing model per one million tokens, based on approximate rates for the Gemini 2.5 Pro model.
PRICING = {
    "input": 1.25,  # Cost in USD per one million tokens.
    "output": 5.00,  # Cost in USD per one million tokens.
}


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate the estimated cost based on input and output token counts."""
    cost = (input_tokens / 1_000_000 * PRICING["input"]) + (
        output_tokens / 1_000_000 * PRICING["output"]
    )
    return round(cost, 5)


async def run_agent(
    app: AdkApp,
    user_id: str,
    message: str,
    raw_output_file: Optional[Path] = None,
    schema: Any = None,
    run_id: str | None = None,
) -> Union[Dict[str, Any], Any]:
    r"""{'docstring': "Asynchronously executes a generative AI agent with telemetry and validation.\n\nThis function orchestrates a call to an AI agent, including retry logic,\ncapturing the raw output, parsing it as JSON, and optionally validating it\nagainst a provided schema. It guarantees that performance and cost telemetry\nare logged for every execution via a `finally` block, regardless of whether\nthe call succeeds or fails.\n\nArgs:\n    app (AdkApp): The `AdkApp` instance containing the agent to be executed.\n    user_id (str): The unique identifier for the user initiating the request.\n    message (str): The input prompt to be sent to the AI agent.\n    raw_output_file (Optional[pathlib.Path]): If provided, the raw text\n        output from the agent will be written to this file. Defaults to None.\n    schema (Any): An optional validation schema (e.g., a Pydantic model)\n        against which the agent's JSON output is validated. Defaults to None.\n    run_id (Optional[str]): An optional unique identifier for this execution,\n        which will be included in telemetry logs for improved traceability.\n        Defaults to None.\n\nReturns:\n    Union[Dict[str, Any], Any]: An instance of the provided `schema`\n    populated with validated JSON data if a schema is given. Otherwise,\n    returns the raw parsed JSON as a `Dict[str, Any]`.\n\nRaises:\n    Exception: Propagates any exception encountered during the AI query,\n        JSON parsing, or schema validation after the failure is logged.\n        Common propagated exceptions include API client errors,\n        `json.JSONDecodeError` for malformed JSON, or schema validation\n        errors (e.g., `pydantic.ValidationError`)."}."""
    start_time = time.monotonic()

    #
    input_tokens_est = len(message) // 4
    output_tokens_est = 0

    try:
        last_text, lines = await _execute_query_with_retry(app, user_id, message)
        output_tokens_est = len(last_text) // 4

        if raw_output_file:
            raw_output_file.write_text("\n".join(lines), encoding="utf-8")

        data = parse_json_from_text(last_text)

        if schema:
            return _robust_unwrap_and_validate(data, schema)

        return cast(Dict[str, Any], data)

    except Exception as e:
        log_msg = (
            f"Fallo crítico tras múltiples reintentos para el usuario {user_id}: {e}"
        )
        if run_id:
            log_msg = f"[run_id={run_id}] {log_msg}"
        logger.error(log_msg)
        raise

    finally:
        end_time = time.monotonic()
        duration = end_time - start_time
        cost = estimate_cost(input_tokens_est, output_tokens_est)

        try:
            retries = (
                getattr(_execute_query_with_retry, "retry").statistics.get(
                    "attempt_number", 1
                )
                - 1
            )
        except Exception:
            retries = 0

        #
        agent_obj = getattr(app, "_agent", None)
        telemetry_data = {
            "run_id": run_id,
            "agent_name": getattr(agent_obj, "name", "N/A"),
            "model": getattr(agent_obj, "model", "N/A"),
            "duration_seconds": round(duration, 2),
            "retries": retries,
            "cost_usd": cost,
            "tokens": {"input": input_tokens_est, "output": output_tokens_est},
            "output_schema": schema.__name__ if schema else "Raw JSON",
        }
        log_msg = "AI Agent Telemetry"
        if run_id:
            log_msg = f"[run_id={run_id}] {log_msg}"
        logger.info(log_msg, extra={"telemetry": telemetry_data})


async def call_agent(
    model_name: str,
    prompt: str,
    raw_output_file: Optional[Path] = None,
    instruction: str = "",
    output_schema: Any = None,
    tools: Optional[list[Callable[..., Any]]] = None,
    run_id: str | None = None,
) -> Any:
    """Initializes and executes a generative AI agent in a single asynchronous call.

    This function provides a high-level interface that selects one of two execution
    paths based on environment variables:

    1.  **Direct `google-generativeai` Client**: If the `GOOGLE_GENAI_USE_VERTEXAI`
        environment variable is set to "0" and `GEMINI_API_KEY` is present, this
        path uses the `google.genai` library directly. This mode is intended
        for simple, non-interactive generation tasks and does not support tools.
    2.  **Agent Development Kit (ADK) Agent**: Otherwise, it uses the full ADK
        to create and run a stateful agent. This path supports tools and more
        complex, potentially multi-turn interactions.

    Args:
        model_name: The name of the generative model to use (e.g., 'gemini-1.5-pro').
        prompt: The primary user input or question for the agent.
        raw_output_file: If provided, the raw text response from the model is
            written to this file path.
        instruction: A system-level instruction to guide the model's behavior.
        output_schema: A schema, such as a Pydantic `BaseModel` class, to
            structure and validate the model's final JSON output.
        tools: A list of callable functions for the agent to use. This argument
            is only effective when using the ADK execution path.
        run_id: A unique identifier for the execution run. This argument is only
            used in the ADK execution path.

    Returns:
        The parsed JSON output from the model. If an `output_schema` is
        provided, this will be a validated instance of that schema.

    Raises:
        ValueError: If the model's output cannot be parsed as JSON or does not
            conform to the provided `output_schema`.
        google.api_core.exceptions.GoogleAPICallError: If an error occurs during
            an API call to the backend service (e.g., authentication failure,
            model not found).
    """
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "1") == "0" and os.environ.get(
        "GEMINI_API_KEY"
    ):
        from google import genai

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

        # The configuration dictionary is constructed in this specific manner to satisfy the strict type-checking requirements of both Mypy and the Google Generative AI SDK.
        config: Dict[str, Any] = {
            "system_instruction": instruction,
            "response_mime_type": "application/json",
        }
        if output_schema:
            config["response_schema"] = output_schema

        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=cast(Any, config),
        )
        if raw_output_file and response.text:
            raw_output_file.write_text(response.text, encoding="utf-8")

        data = parse_json_from_text(response.text or "{}")
        if output_schema:
            return _robust_unwrap_and_validate(data, output_schema)
        return data

    from google.adk.agents import Agent

    agent = Agent(
        model=model_name,
        name="ad_hoc_agent",
        instruction=instruction,
        output_schema=output_schema,
        tools=tools or [],  # type: ignore
    )
    app = AdkApp(agent=agent)
    return await run_agent(
        app=app,
        user_id="ad-hoc-user",
        message=prompt,
        raw_output_file=raw_output_file,
        schema=output_schema,
        run_id=run_id,
    )
