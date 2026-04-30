"""
Módulo ai_client.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Optional

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


class VertexQueryTimeoutError(RuntimeError):
    """La consulta a Vertex AI superó el timeout configurado."""


def extract_model_text(event: Any) -> Optional[str]:
    if isinstance(event, dict):
        content = event.get("content", {})
        parts = content.get("parts", [])
        for part in parts:
            if isinstance(part, dict) and "text" in part:
                return part["text"]
    return None


@retry(
    retry=retry_if_exception(
        lambda exc: not isinstance(exc, VertexQueryTimeoutError)
    )
    & retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.INFO),
    reraise=True,
)
async def _execute_query_with_retry(app: AdkApp, user_id: str, message: str) -> tuple[str, list[str]]:
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
        logger.error(f"Fallo de validación SRE. Keys del JSON recibido: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        raise e

async def run_agent(
    app: AdkApp, 
    user_id: str, 
    message: str, 
    raw_output_file: Optional[Path] = None,
    schema: Any = None
) -> dict:
    """
    Ejecuta un agente de forma asíncrona y captura telemetría.
    """
    start_time = time.monotonic()
    
    try:
        last_text, lines = await _execute_query_with_retry(app, user_id, message)
        
        if raw_output_file:
            raw_output_file.write_text("\n".join(lines), encoding="utf-8")

        data = parse_json_from_text(last_text)
        
        if schema:
            return _robust_unwrap_and_validate(data, schema)
                
        return data
        
    except Exception as e:
        logger.error(f"Fallo crítico tras múltiples reintentos para el usuario {user_id}: {e}")
        raise
        
    finally:
        end_time = time.monotonic()
        duration = end_time - start_time
        retries = _execute_query_with_retry.retry.statistics.get("attempt_number", 1) - 1
        
        # Safely access agent and model info
        agent_obj = getattr(app, "_agent", None)
        agent_name = getattr(agent_obj, "name", "N/A")
        model_name = getattr(agent_obj, "model", "N/A")

        # Telemetry Output
        print("\n---")
        print("🤖 AI Agent Telemetry:")
        print(f"   - Agent Name: {agent_name}")
        print(f"   - Model: {model_name}")
        print(f"   - User ID: {user_id}")
        print(f"   - Duration: {duration:.2f}s")
        print(f"   - Retries: {retries}")
        print(f"   - Output Schema: {schema.__name__ if schema else 'Raw JSON'}")
        print("---\n")


async def call_agent(model_name: str, prompt: str, raw_output_file: Optional[Path] = None, instruction: str = "", output_schema: Any = None) -> dict:
    """
    Helper simplificado para inicializar y correr un AdkApp en una sola llamada.
    """
    from google.adk.agents import Agent
    agent = Agent(
        model=model_name,
        name="ad_hoc_agent",
        instruction=instruction,
        output_schema=output_schema,
    )
    app = AdkApp(agent=agent)
    return await run_agent(
        app=app,
        user_id="ad-hoc-user",
        message=prompt,
        raw_output_file=raw_output_file,
        schema=output_schema
    )
