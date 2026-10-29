r"""The ai_client.py module.\n\nThis module encapsulates the core logic and utilities for interfacing with the Assessment Engine pipeline."""

import asyncio
import json
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

from assessment_engine.infrastructure.json_from_model import parse_json_from_text
from assessment_engine.infrastructure.runtime_env import (
    get_vertex_query_timeout_seconds,
)

#
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#
VERTEX_CONCURRENCY_LIMIT = 5
_vertex_semaphore = asyncio.Semaphore(VERTEX_CONCURRENCY_LIMIT)


class TokenBucketRateLimiter:
    """Thread-safe and async token bucket rate limiter with a strict RPM ceiling (default 1800 RPM)."""

    def __init__(self, max_rpm: int = 1800) -> None:
        self.capacity = max(1.0, float(max_rpm) / 60.0)  # 30 tokens per second for 1800 RPM
        self.tokens = self.capacity
        self.rate = self.capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.last_update = time.monotonic()
                self.tokens = 0.0
            else:
                self.tokens -= 1.0


_rate_limiter = TokenBucketRateLimiter(
    max_rpm=int(os.environ.get("AI_MAX_RPM", "1800"))
)


def ensure_vertexai_initialized() -> None:
    """Ensures Vertex AI is initialized in the global region with valid credentials."""
    import os

    import vertexai
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        sa_path = os.path.expanduser("~/.secrets/sa-key.json")
        if os.path.exists(sa_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_path
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "sub403o4u0q5")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
    try:
        vertexai.init(
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        )
    except Exception as e:
        logger.debug("vertexai.init fallback exception: %s", e)


class VertexQueryTimeoutError(RuntimeError):
    """{'docstring': 'Error raised when a request to a Vertex AI service times out.'}."""


def extract_model_text(event: Any) -> Optional[str]:
    """Safely extracts the first text block from a model response event.

    Parses a nested dictionary, such as an event from a streaming model API, to
    locate and return the first textual content block. The function is designed
    to robustly handle malformed or incomplete data by traversing the expected
    structure `event['content']['parts'][...]['text']`.

    It gracefully handles missing keys, incorrect types, or empty lists at any
    level of the nested structure without raising exceptions.

    Args:
        event (Any): The model response event, expected to be a dictionary.

    Returns:
        Optional[str]: The string content from the first part containing a 'text'
            key. Returns None if no such part is found or if the event
            structure does not conform to the expected format.
    """
    if isinstance(event, dict):
        content = event.get("content", {})
        parts = content.get("parts", [])
        for part in parts:
            if isinstance(part, dict) and "text" in part:
                return str(part["text"])
    return None


def sanitize_gemini_schema(schema_input: Any) -> Any:
    """Recursively removes 'additionalProperties' from JSON schema dictionaries to satisfy Gemini API strictness."""
    if not schema_input:
        return None
    if isinstance(schema_input, type) and hasattr(schema_input, "model_json_schema"):
        schema_dict = schema_input.model_json_schema()
    elif isinstance(schema_input, dict):
        import copy

        schema_dict = copy.deepcopy(schema_input)
    else:
        return schema_input

    def _strip_unsupported(node: Any) -> Any:
        if isinstance(node, dict):
            node.pop("additionalProperties", None)
            for v in node.values():
                _strip_unsupported(v)
        elif isinstance(node, list):
            for item in node:
                _strip_unsupported(item)
        return node

    return _strip_unsupported(schema_dict)


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
    """Executes a query against the specified agent, incorporating retry logic to handle transient failures."""
    use_vertex = (
        os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "1").strip().lower()
        not in ("0", "false", "no")
    )
    api_key = os.environ.get("GEMINI_API_KEY")

    if isinstance(app, AdkApp) and not use_vertex and api_key:
        from google import genai

        from assessment_engine.infrastructure.genai_client import get_fallback_model

        client = genai.Client(api_key=api_key)
        agent_obj = getattr(app, "_agent", None) or getattr(app, "_tmpl_attrs", {}).get("agent")
        current_model = getattr(agent_obj, "model", "gemini-3.8-flash")
        instruction = getattr(agent_obj, "instruction", None)
        output_schema = getattr(agent_obj, "output_schema", None)

        config: Dict[str, Any] = {
            "response_mime_type": "application/json",
        }
        if instruction:
            config["system_instruction"] = instruction
        if output_schema:
            config["response_schema"] = sanitize_gemini_schema(output_schema)

        timeout_seconds = get_vertex_query_timeout_seconds()
        try:
            await _rate_limiter.acquire()
            async with asyncio.timeout(timeout_seconds):
                response = await client.aio.models.generate_content(
                    model=current_model,
                    contents=message,
                    config=cast(Any, config),
                )
                resp_text = response.text or ""
                return resp_text, [resp_text]
        except Exception as exc:
            fallback = get_fallback_model(current_model)
            if fallback and fallback != current_model:
                logger.warning(
                    f"⚠️ [AI Studio Failover] Error en modelo primario '{current_model}': {exc}. "
                    f"Failing over immediately to backup model '{fallback}' for next retry..."
                )
                if agent_obj:
                    agent_obj.model = fallback
            raise

    ensure_vertexai_initialized()
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
        except Exception as exc:
            from assessment_engine.infrastructure.genai_client import (
                get_fallback_model,
            )

            agent_obj = getattr(app, "_agent", None) or getattr(app, "_tmpl_attrs", {}).get("agent")
            current_model = getattr(agent_obj, "model", None)
            fallback = get_fallback_model(current_model)
            if fallback and fallback != current_model:
                logger.warning(
                    f"⚠️ [AI Failover] Error en modelo primario '{current_model}': {exc}. "
                    f"Failing over immediately to backup model '{fallback}' for next retry..."
                )
                agent_obj.model = fallback

            if isinstance(exc, TimeoutError):
                raise VertexQueryTimeoutError(
                    f"Vertex agent query timed out after {timeout_seconds:.0f}s for user_id={user_id}."
                ) from exc
            raise

        if not last_text:
            raise RuntimeError("Empty or incomplete response from model.")

        return last_text, lines


def _robust_unwrap_and_validate(data: Any, schema: Any) -> Any:
    """Validates input data against a specified schema, with explicit handling for common nested data structures."""
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
                    except (OSError, ValueError, KeyError, AttributeError) as ex:

                        logger.debug(f"[Fallback] Handled exception: {ex}")
        logger.error(
            f"SRE Validation Failure. Received JSON keys: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        )
        raise e


# Model-Agnostic Pricing (USD per one million tokens)
PRICING = {
    "flash": {"input": 0.075, "output": 0.30},
    "reasoning": {"input": 1.25, "output": 5.00},
    "default": {"input": 1.25, "output": 5.00},
}


def estimate_cost(
    input_tokens: int, output_tokens: int, model: str = "default"
) -> float:
    """Calculate the estimated cost of an API request based on token usage.

    Automatically maps any flash variant to high-efficiency flash tier rates,
    and all reasoning models to standard cognitive rates.
    """
    clean_model = model.lower()
    if "flash" in clean_model:
        price = PRICING["flash"]
    else:
        price = PRICING["reasoning"]

    cost = (input_tokens / 1_000_000 * price["input"]) + (
        output_tokens / 1_000_000 * price["output"]
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
    """Executes an agent, parses its JSON response, and logs detailed telemetry.

    This function orchestrates the full lifecycle of an asynchronous agent
    interaction. It sends a message to the agent, handles transient failures
    with an automatic retry mechanism, and processes the response. The agent's
    text output is expected to be a valid JSON string.

    If a `schema` is provided (e.g., a Pydantic model), the parsed JSON is
    validated and coerced into an instance of that schema. If `raw_output_file`
    is specified, the raw agent output is persisted to disk.

    A `finally` block guarantees that a comprehensive telemetry record is logged
    for every execution attempt. This record includes performance metrics such
    as duration, estimated token counts, approximate cost, and the number of
    retries, ensuring observability even in cases of failure.

    Args:
        app: The configured application instance which contains the agent
            definition.
        user_id: A unique identifier for the end-user initiating the request.
        message: The input prompt to be processed by the agent.
        raw_output_file: If provided, the raw text output from the agent is
            written to this file path.
        schema: An optional class or type (e.g., a Pydantic model) used to
            validate and parse the agent's JSON output.
        run_id: An optional identifier for this specific execution, used for
            correlating logs and telemetry.

    Returns:
        An instance of the provided `schema` if validation is successful, or a
        `dict` representing the parsed JSON if no `schema` is provided.

    Raises:
        json.JSONDecodeError: If the agent's output is not a parsable JSON
            string.
        pydantic.ValidationError: If a `schema` is provided and the JSON data
            fails validation against it.
        IOError: If an error occurs while writing the output to the
            `raw_output_file`.
        Exception: Propagates the underlying exception from the agent execution
            if all retry attempts are exhausted.
    """
    start_time = time.monotonic()

    # A placeholder value for token counts, to be populated later in the execution flow.
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
            f"Critical failure after multiple retries for user {user_id}: {e}"
        )
        if run_id:
            log_msg = f"[run_id={run_id}] {log_msg}"
        logger.error(log_msg)
        raise

    finally:
        end_time = time.monotonic()
        duration = end_time - start_time

        #
        agent_obj = getattr(app, "_agent", None)
        model_name = getattr(agent_obj, "model", "default")

        cost = estimate_cost(input_tokens_est, output_tokens_est, model=model_name)

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
        persist_finops_telemetry(telemetry_data)


def persist_finops_telemetry(telemetry_data: dict[str, Any]) -> None:
    """Appends atomic AI invocation metrics to the client's FinOps token ledger for cost and quota governance."""
    client_id = (
        os.environ.get("ASSESSMENT_CLIENT_ID")
        or os.environ.get("CLIENT_ID")
        or os.environ.get("CLIENT_NAME")
    )
    if not client_id and os.environ.get("ASSESSMENT_CASE_DIR"):
        try:
            client_id = Path(os.environ["ASSESSMENT_CASE_DIR"]).parent.name
        except Exception:
            pass
    if not client_id:
        return

    from assessment_engine.infrastructure.text_utils import slugify

    client_slug = slugify(client_id)
    ledger_file = Path("working") / client_slug / "finops_token_ledger.jsonl"
    try:
        ledger_file.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": time.time(),
            "tower_id": os.environ.get("ASSESSMENT_TOWER_ID", "GLOBAL"),
            **telemetry_data,
        }
        with open(ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as ex:
        logger.debug(f"[FinOps] Error appending token telemetry: {ex}")


async def call_agent(
    model_name: str,
    prompt: str,
    raw_output_file: Optional[Path] = None,
    instruction: str = "",
    output_schema: Any = None,
    tools: Optional[list[Callable[..., Any]]] = None,
    run_id: str | None = None,
) -> Any:
    """Execute a single-turn agent interaction with a generative model.

    This function provides a dual-mode interface for interacting with Google's
    generative models, determined by environment variables.

    1.  **Direct API Mode**: If the `GOOGLE_GENAI_USE_VERTEXAI` environment
        variable is set to '0' and `GEMINI_API_KEY` is present, the function
        communicates directly with the Google Generative AI API.
    2.  **ADK Mode**: Otherwise, it constructs and executes a temporary agent
        using the Google Agent Development Kit (ADK) framework.

    Args:
        model_name: The identifier for the generative model to be invoked (e.g.,
            'gemini-3.1-pro-preview').
        prompt: The user-provided query or instruction for the model.
        raw_output_file: An optional file path to which the raw JSON response from
            the model will be written. Defaults to None.
        instruction: A system-level instruction to guide model behavior,
            influencing its persona, style, or response format.
        output_schema: A Pydantic model or compatible type used to validate and
            structure the model's JSON output. Defaults to None.
        tools: A list of callable functions available to the model. This
            argument is only effective when operating in ADK mode. Defaults to None.
        run_id: An optional identifier for a specific execution trace. This
            argument is only effective when operating in ADK mode. Defaults to
            None.

    Returns:
        The model's response, parsed and validated. If an `output_schema` is
        provided, the return value is an instance of that schema. Otherwise, it
        is the parsed JSON object (e.g., a dict).

    Raises:
        pydantic.ValidationError: If `output_schema` is provided and the model's
            output fails validation against the schema.
        json.JSONDecodeError: If the model's response cannot be parsed as valid
            JSON.
        google.api_core.exceptions.GoogleAPICallError: If an error occurs during
            the API call to the generative model service.
        IOError: If `raw_output_file` is specified but the file cannot be written.
    """
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "1") == "0" and os.environ.get(
        "GEMINI_API_KEY"
    ):
        from google import genai

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

        # The configuration dictionary is constructed to satisfy both Mypy static type checking and the GenAI library's expected type structure.
        config: Dict[str, Any] = {
            "system_instruction": instruction,
            "response_mime_type": "application/json",
        }
        if output_schema:
            config["response_schema"] = sanitize_gemini_schema(output_schema)

        await _rate_limiter.acquire()
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=cast(Any, config),
        )
        if raw_output_file and response.text:
            raw_output_file.write_text(response.text, encoding="utf-8")

        u_meta = getattr(response, "usage_metadata", None)
        in_tok = getattr(u_meta, "prompt_token_count", None) or (len(prompt) // 4)
        out_tok = getattr(u_meta, "candidates_token_count", None) or (len(response.text or "") // 4)
        c_usd = estimate_cost(in_tok, out_tok, model=model_name)
        persist_finops_telemetry({
            "run_id": run_id,
            "agent_name": "ad_hoc_agent",
            "model": model_name,
            "duration_seconds": 0.0,
            "retries": 0,
            "cost_usd": c_usd,
            "tokens": {"input": in_tok, "output": out_tok},
            "output_schema": getattr(output_schema, "__name__", "Raw JSON"),
        })

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
        tools=tools or [],  # type: ignore # TODO(jsanchhi): #82 Resolve tools typing mismatch with google.adk.agents.Agent schema.
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
