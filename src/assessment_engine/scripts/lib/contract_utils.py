"""
Módulo contract_utils.py.
Proporciona utilidades para la validación resiliente de contratos entre etapas.
Permite detectar desviaciones de esquema sin necesariamente abortar la ejecución.
"""

import json
import logging
from pathlib import Path
from typing import Literal, Type, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
ContractLoadMode = Literal["strict", "tolerant"]

logger = logging.getLogger("assessment_engine.contracts")


def robust_load_payload(
    path: Path,
    schema: Type[T],
    artifact_name: str = "Artifact",
    *,
    mode: ContractLoadMode = "tolerant",
) -> T:
    """
    Carga un JSON y lo valida contra un esquema Pydantic de forma resiliente.
    Si hay errores de validación, los registra detalladamente pero intenta
    devolver un objeto válido (usando valores por defecto o parciales).
    """
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el artefacto: {path}")

    try:
        content = path.read_text(encoding="utf-8-sig")
        data = json.loads(content)
    except Exception as e:
        logger.error(
            f"❌ Error crítico cargando JSON de {artifact_name} en {path}: {e}"
        )
        raise

    try:
        # Intento de validación estricta
        return schema.model_validate(data)
    except ValidationError as e:
        logger.warning(
            f"⚠️ Desviación de contrato detectada en {artifact_name} ({path.name}):"
        )
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            logger.warning(f"   - Campo [{loc}]: {msg}")

        if mode == "strict":
            raise

        # Modo de recuperación: Intentar construir el modelo ignorando errores (best effort)
        # o devolviendo el modelo validado parcialmente si es posible.
        # En esta fase B4, devolvemos el objeto validado con 'model_construct'
        # para asegurar que el informe salga, pero habiendo avisado del fallo.
        return schema.model_construct(**data)
    except Exception as e:
        logger.error(f"❌ Error inesperado validando {artifact_name}: {e}")
        if mode == "strict":
            raise
        return schema.model_construct(**data)


def save_versioned_payload(path: Path, payload: BaseModel, artifact_type: str):
    """
    Guarda un payload asegurando que incluya metadatos de versión y use alias.
    """
    # Si el payload no tiene metadatos, intentamos inyectarlos si el modelo lo permite
    if hasattr(payload, "generation_metadata") and payload.generation_metadata is None:
        from .common import VersionMetadata

        payload.generation_metadata = VersionMetadata(
            artifact_type=artifact_type, artifact_version="1.0.0"
        )

    data = payload.model_dump(by_alias=True, exclude_none=False)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"✅ Artefacto {artifact_type} guardado en: {path}")
