from typing import Any

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
    """Loads and validates a JSON object from a file against a Pydantic schema.

    This function employs a two-phase loading pattern for resilience. It first
    attempts a strict validation of the JSON content using `schema.model_validate`.
    If validation fails, its behavior is determined by the `mode` parameter.

    In 'tolerant' mode (the default), validation errors are logged, and a Pydantic
    model instance is created using `schema.model_construct`. This approach
    bypasses validation to produce a best-effort object, allowing downstream
    systems to continue operating with potentially incomplete or malformed data.

    In 'strict' mode, the original `pydantic.ValidationError` is re-raised,
    enforcing data integrity at the cost of halting execution on contract
    deviations.

    Args:
        path (pathlib.Path): The path to the JSON file to load.
        schema (Type[T]): The Pydantic model to use for validation and parsing.
        artifact_name (str): A descriptive name for the data artifact, used in
            log messages. Defaults to "Artifact".
        mode (ContractLoadMode): A keyword-only argument specifying the loading
            strategy, either 'tolerant' or 'strict'. Defaults to 'tolerant'.

    Returns:
        T: An instance of the provided `schema`. In 'tolerant' mode, if validation
            fails, the returned object is constructed without validation and may be
            incomplete or contain data that does not conform to the schema.

    Raises:
        FileNotFoundError: If the file specified by `path` does not exist.
        json.JSONDecodeError: If the file content cannot be parsed as JSON.
        pydantic.ValidationError: If `mode` is 'strict' and the JSON data fails
            to validate against the `schema`.
        TypeError: If the top-level JSON value is not a dictionary, which is
            required for Pydantic model instantiation.
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
        #
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

        # ENTER RECOVERY: A validation failure has occurred. A model instance is constructed via `model_construct` to bypass validation, preserving operational continuity.
        #
        # The `ValidationError` triggers a fallback path. `model_construct` is used to create an instance without re-running validators, providing a best-effort object for downstream consumers.
        # This two-phase parse (validate then construct-on-fail) is a deliberate resilience pattern. Failures are logged for audit, but a partial object is returned to prevent system failure.
        return schema.model_construct(**data)
    except Exception as e:
        logger.error(f"❌ Error inesperado validando {artifact_name}: {e}")
        if mode == "strict":
            raise
        return schema.model_construct(**data)


def save_versioned_payload(path: Path, payload: BaseModel, artifact_type: str) -> Any:
    r"""{'docstring': 'Save a Pydantic model to a versioned JSON file.\n\n    Serializes a Pydantic model to a JSON file, ensuring the presence of\n    versioning metadata. If the payload has a `generation_metadata` attribute\n    that is `None`, this function injects a default `VersionMetadata` instance,\n    using the provided `artifact_type` and a hardcoded artifact version of\n    "1.0.0".\n\n    The model is dumped to a dictionary using field aliases while preserving `None`\n    values. The resulting dictionary is then serialized to a JSON string with an\n    indent of 2 and written to the specified path as a UTF-8 encoded file.\n\n    Args:\n        path: The `pathlib.Path` object for the destination file.\n        payload: The Pydantic `BaseModel` instance to be serialized. Note that\n            this object may be modified in-place.\n        artifact_type: A string identifying the artifact type, used to\n            construct the default `VersionMetadata` if required.\n\n    Raises:\n        ImportError: If the required `VersionMetadata` schema cannot be\n            imported from `domain.schemas.common`.\n        OSError: If an error occurs during file writing (e.g., permission\n            denied, invalid path).\n        TypeError: If the payload contains data types that are not serializable\n            to JSON.\n        ValueError: If the payload fails validation during serialization or\n            contains circular references.'}."""
    # For payloads lacking a metadata block, inject default metadata if the target schema defines it to ensure structural consistency.
    if hasattr(payload, "generation_metadata") and payload.generation_metadata is None:
        from assessment_engine.domain.schemas.common import VersionMetadata

        payload.generation_metadata = VersionMetadata(
            artifact_type=artifact_type, artifact_version="1.0.0"
        )

    data = payload.model_dump(by_alias=True, exclude_none=False)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"✅ Artefacto {artifact_type} guardado en: {path}")
