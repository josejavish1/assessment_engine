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


def _sanitize_schema(schema_dict: Any) -> Any:
    if isinstance(schema_dict, dict):
        schema_dict.pop("additionalProperties", None)
        for value in schema_dict.values():
            _sanitize_schema(value)
    elif isinstance(schema_dict, list):
        for item in schema_dict:
            _sanitize_schema(item)
    return schema_dict

@retry(
    retry=retry_if_exception(lambda exc: not isinstance(exc, VertexQueryTimeoutError))
    & retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.INFO),
    reraise=True,
)
async def _execute_query_with_retry(
    app: AdkApp, user_id: str, message: str, schema: Any = None
) -> tuple[str, list[dict], list[str]]:
    """
    Realiza la consulta al agente utilizando google-genai con automatic_function_calling stateful.
    """
    from google import genai
    from google.genai import types

    async with _vertex_semaphore:
        timeout_seconds = get_vertex_query_timeout_seconds()
        
        tmpl_attrs = getattr(app, "_tmpl_attrs", {})
        agent_ref = tmpl_attrs.get("agent")
        model_name = getattr(agent_ref, "model", "gemini-2.5-pro")
        instruction = getattr(agent_ref, "instruction", "")
        agent_tools = getattr(agent_ref, "tools", []) if agent_ref else []

        client = genai.Client()
        
        # Google GenAI API does not support mixing function calling with JSON response mime type.
        # We rely on parse_json_from_text and _robust_unwrap_and_validate afterwards instead.
        if agent_tools:
            config_kwargs = {
                "system_instruction": instruction,
                "tools": agent_tools,
                "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=False),
                "temperature": getattr(agent_ref, "temperature", 0.0) if agent_ref else 0.0,
            }
        else:
            clean_schema = _sanitize_schema(schema.model_json_schema()) if schema else None
            config_kwargs = {
                "system_instruction": instruction,
                "response_mime_type": "application/json" if schema else "text/plain",
                "response_schema": clean_schema,
                "temperature": getattr(agent_ref, "temperature", 0.0) if agent_ref else 0.0,
            }
            
        config = types.GenerateContentConfig(**config_kwargs)

        try:
            async with asyncio.timeout(timeout_seconds):
                chat = client.aio.chats.create(
                    model=model_name,
                    config=config,
                )
                response = await chat.send_message(message)
                final_text = response.text or "{}"
                return final_text, [], [final_text]

        except TimeoutError as exc:
            raise VertexQueryTimeoutError(
                f"Vertex agent query timed out after {timeout_seconds:.0f}s for user_id={user_id}."
            ) from exc

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
    _tool_depth: int = 0,
) -> dict:
    """
    Ejecuta un agente de forma asíncrona y captura telemetría avanzada usando integración nativa genai.
    """
    start_time = time.monotonic()
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
            full_text, function_calls, lines = await _execute_query_with_retry(app, user_id, message, schema=schema)
            if len(_query_cache) >= _CACHE_MAX_SIZE:
                _query_cache.pop(next(iter(_query_cache)))
            _query_cache[cache_key] = (full_text, function_calls, lines)

        output_tokens_est = len(full_text) // 4 if full_text else 0

        if raw_output_file:
            raw_output_file.write_text("\n".join(lines), encoding="utf-8")

        if not full_text:
             raise RuntimeError("Respuesta de texto vacía.")

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
    
    Path("working/apex/call_agent_dump.txt").write_text(f"---INSTRUCTION---\n{instruction}\n\n---PROMPT---\n{prompt}\n", encoding="utf-8")

    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "1") == "0" and os.environ.get(
        "GEMINI_API_KEY"
    ):
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        
        config = types.GenerateContentConfig(
            system_instruction=instruction,
            response_mime_type="application/json" if output_schema else "text/plain",
            response_schema=output_schema,
            tools=tools if tools else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False) if tools else None,
        )
        
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
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
