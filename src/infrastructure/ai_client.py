"""
Módulo ai_client.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

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

from infrastructure.json_from_model import parse_json_from_text
from infrastructure.runtime_env import get_vertex_query_timeout_seconds

# Configuración de Logging básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Semáforo global
VERTEX_CONCURRENCY_LIMIT = 5
_vertex_semaphore = asyncio.Semaphore(VERTEX_CONCURRENCY_LIMIT)


class VertexQueryTimeoutError(RuntimeError):
    """La consulta a Vertex AI superó el timeout configurado."""


def extract_model_text(event: Any) -> Optional[str]:
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
    """
    Realiza la consulta al agente con lógica de reintentos.
    """
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
    """
    Intenta validar los datos contra el esquema, manejando anidamientos comunes.
    """
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


# Precios estimados por 1M tokens (Gemini 2.5 Pro aprox)
PRICING = {
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},  # $ per 1M tokens
    "gemini-2.5-flash": {"input": 0.10, "output": 0.40},
    "default": {"input": 1.25, "output": 5.00},
}


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "default") -> float:
    # Normalize model name for pricing lookups
    clean_model = model.lower()
    price = PRICING.get(clean_model, PRICING["default"])
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
    """
    Ejecuta un agente de forma asíncrona y captura telemetría avanzada.
    """
    start_time = time.monotonic()

    # Placeholder para tokens
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
        
        # Telemetry Metadata
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

        # Telemetry Output
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
    """
    Helper simplificado para inicializar y correr un AdkApp en una sola llamada.
    """
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "1") == "0" and os.environ.get(
        "GEMINI_API_KEY"
    ):
        from google import genai

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

        # Build config carefully to satisfy Mypy/GenAI types
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
