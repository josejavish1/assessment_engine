"""
Módulo ai_client.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional

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

# Configuración de Logging básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Semáforo global
VERTEX_CONCURRENCY_LIMIT = 5
_vertex_semaphore = asyncio.Semaphore(VERTEX_CONCURRENCY_LIMIT)

# Cache para consultas a Vertex AI
_query_cache = {}
_CACHE_MAX_SIZE = 128


class VertexQueryTimeoutError(RuntimeError):
    """La consulta a Vertex AI superó el timeout configurado."""


def _extract_model_parts(event: Any) -> tuple[Optional[str], list[dict]]:
    """Extrae texto y `function_call` o `tool_calls` de un evento de streaming."""
    text_parts = []
    function_calls = []

    if isinstance(event, dict):
        content = event.get("content", {})
        parts = content.get("parts", [])
        for part in parts:
            if not isinstance(part, dict):
                continue
            if "text" in part and part["text"]:
                text_parts.append(part["text"])
            if "function_call" in part:
                function_calls.append(part["function_call"])
            elif "tool_calls" in part:
                function_calls.extend(part["tool_calls"])
    elif hasattr(event, "candidates") and event.candidates:
        parts = getattr(event.candidates[0].content, "parts", [])
        for part in parts:
            if getattr(part, "text", None):
                text_parts.append(part.text)
            if getattr(part, "function_call", None):
                fc = part.function_call
                function_calls.append({
                    "name": fc.name,
                    "args": dict(fc.args) if fc.args else {}
                })

    text = "".join(text_parts) if text_parts else None
    return text, function_calls


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
) -> tuple[str, list[dict], list[str]]:
    """
    Realiza la consulta al agente con lógica de reintentos, capturando texto y function calls.
    """
    async with _vertex_semaphore:
        lines = []
        full_text = []
        function_calls = []
        timeout_seconds = get_vertex_query_timeout_seconds()
        
        try:
            async with asyncio.timeout(timeout_seconds):
                async for event in app.async_stream_query(
                    user_id=user_id,
                    message=message,
                ):
                    text, new_fcs = _extract_model_parts(event)
                    if text:
                        lines.append(text)
                        full_text.append(text)
                    if new_fcs:
                        lines.append(str(new_fcs))
                        function_calls.extend(new_fcs)

        except TimeoutError as exc:
            raise VertexQueryTimeoutError(
                f"Vertex agent query timed out after {timeout_seconds:.0f}s for user_id={user_id}."
            ) from exc

        final_text = "".join(full_text)
        if not final_text and not function_calls:
            raise RuntimeError("Respuesta vacía o incompleta del modelo.")

        return final_text, function_calls, lines


def _robust_unwrap_and_validate(data: Any, schema: Any) -> Any:
    # This function remains the same
    try:
        return schema.model_validate(data).model_dump(by_alias=True)
    except Exception as e:
        if isinstance(data, dict):
            if len(data) == 1:
                first_val = list(data.values())[0]
                if isinstance(first_val, (dict, list)):
                    return _robust_unwrap_and_validate(first_val, schema)
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    try:
                        return schema.model_validate(v).model_dump(by_alias=True)
                    except Exception:
                        pass
        logger.error(
            f"Fallo de validación SRE. Keys del JSON recibido: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        )
        raise e


# Precios estimados por 1M tokens (Gemini 2.5 Pro aprox)
PRICING = {
    "input": 1.25,  # $ per 1M tokens
    "output": 5.00, # $ per 1M tokens
}

def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    cost = (input_tokens / 1_000_000 * PRICING["input"]) + (output_tokens / 1_000_000 * PRICING["output"])
    return round(cost, 5)

async def run_agent(
    app: AdkApp,
    user_id: str,
    message: str,
    raw_output_file: Optional[Path] = None,
    schema: Any = None,
    run_id: str | None = None,
) -> dict:
    """
    Ejecuta un agente de forma asíncrona y captura telemetría avanzada.
    """
    start_time = time.monotonic()
    
    # Build the function dispatcher from the agent's tools
    tmpl_attrs = getattr(app, "_tmpl_attrs", {})
    agent_ref = tmpl_attrs.get("agent")
    agent_tools = getattr(agent_ref, "tools", []) if agent_ref else []
    function_dispatcher = {
        tool.__name__: tool for tool in agent_tools
    }
    
    # Placeholder para tokens (el ADK actual no siempre los expone fácilmente en el stream)
    # En una implementación real extraeríamos esto de los metadatos de la respuesta final
    input_tokens_est = len(message) // 4
    output_tokens_est = 0
    is_cache_hit = False

    try:
        agent_name = getattr(getattr(app, "_agent", None), "name", "N/A")
        instruction = getattr(getattr(app, "_agent", None), "instruction", "")
        schema_name = schema.__name__ if schema else "Raw JSON"

        cache_key = (agent_name, instruction, schema_name, user_id, message)
        
        if cache_key in _query_cache:
            full_text, function_calls, lines = _query_cache[cache_key]
            is_cache_hit = True
        else:
            full_text, function_calls, lines = await _execute_query_with_retry(app, user_id, message)
            if len(_query_cache) >= _CACHE_MAX_SIZE:
                _query_cache.pop(next(iter(_query_cache)))
            _query_cache[cache_key] = (full_text, function_calls, lines)

        output_tokens_est = len(full_text) // 4 if full_text else 0

        if raw_output_file:
            raw_output_file.write_text("\n".join(lines), encoding="utf-8")

        if function_calls:
            logger.info(f"[run_id={run_id}] Function call(s) received: {function_calls}")
            tool_results = []
            for fc in function_calls:
                tool_name = fc.get("name")
                if not tool_name:
                    logger.warning(f"[run_id={run_id}] Received a function call without a name: {fc}")
                    continue

                if tool_name in function_dispatcher:
                    tool_func = function_dispatcher[tool_name]
                    tool_args = fc.get("args", {})
                    try:
                        # Argument validation could be added here if needed
                        result = tool_func(**tool_args)
                        tool_results.append(
                            {
                                "tool_name": tool_name,
                                "result": result,
                                "status": "OK",
                            }
                        )
                        logger.info(f"[run_id={run_id}] Executed tool '{tool_name}' with args {tool_args}. Result: {result}")
                    except Exception as e:
                        logger.error(f"[run_id={run_id}] Error executing tool '{tool_name}': {e}")
                        tool_results.append(
                            {
                                "tool_name": tool_name,
                                "error": str(e),
                                "status": "Error",
                            }
                        )
                else:
                    logger.warning(f"[run_id={run_id}] Model hallucinated function name '{tool_name}', which is not a registered tool.")
                    tool_results.append(
                        {
                            "tool_name": tool_name,
                            "error": f"Function '{tool_name}' not found.",
                            "status": "Error",
                        }
                    )
            import json
            follow_up_message = "Tool execution results:\n" + json.dumps(tool_results, indent=2) + "\n\nPlease continue and fulfill the original request schema."
            logger.info(f"[run_id={run_id}] Feeding tool results back to the model for continuation...")
            return await run_agent(
                app=app,
                user_id=user_id,
                message=follow_up_message,
                raw_output_file=raw_output_file,
                schema=schema,
                run_id=run_id
            )

        if not full_text:
             raise RuntimeError("Respuesta de texto vacía y sin 'function calls'.")

        data = parse_json_from_text(full_text)

        if schema:
            return _robust_unwrap_and_validate(data, schema)

        return data

    except Exception as e:
        log_msg = f"Fallo crítico tras múltiples reintentos para el usuario {user_id}: {e}"
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

        # Telemetry Output
        telemetry_data = {
            "run_id": run_id,
            "agent_name": getattr(getattr(app, "_agent", None), "name", "N/A"),
            "duration_seconds": round(duration, 2),
            "retries": retries,
            "cost_usd": cost,
            "tokens": {"input": input_tokens_est, "output": output_tokens_est},
            "output_schema": schema.__name__ if schema else "Raw JSON",
            "cache_hit": is_cache_hit,
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
) -> dict:
    """
    Helper simplificado para inicializar y correr un AdkApp en una sola llamada.
    """
    import os

    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "1") == "0" and os.environ.get(
        "GEMINI_API_KEY"
    ):
        from google import genai

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "system_instruction": instruction,
                "response_mime_type": "application/json",
                "response_schema": output_schema,
            },
        )
        text_parts = []
        if getattr(response, "candidates", None) and response.candidates:
            for part in getattr(response.candidates[0].content, "parts", []):
                if getattr(part, "text", None):
                    text_parts.append(part.text)
                elif getattr(part, "function_call", None):
                    text_parts.append(str(part.function_call))
        
        final_text = "".join(text_parts) if text_parts else (response.text or "{}")

        if raw_output_file and final_text:
            raw_output_file.write_text(final_text, encoding="utf-8")

        from assessment_engine.scripts.lib.json_from_model import parse_json_from_text

        data = parse_json_from_text(final_text)
        if output_schema:
            return _robust_unwrap_and_validate(data, output_schema)
        return data

    from google.adk.agents import Agent
    from vertexai.agent_engines import AdkApp
    import uuid

    unique_id = str(uuid.uuid4()).replace("-", "_")
    agent = Agent(
        model=model_name,
        name=f"ad_hoc_agent_{unique_id}",
        instruction=instruction,
        output_schema=output_schema,
        tools=tools or [],  # type: ignore
    )
    app = AdkApp(agent=agent)
    return await run_agent(
        app=app,
        user_id=f"user_{unique_id}",
        message=prompt,
        raw_output_file=raw_output_file,
        schema=output_schema,
        run_id=run_id,
    )
