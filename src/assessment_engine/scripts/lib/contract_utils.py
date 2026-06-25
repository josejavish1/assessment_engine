"""Utilities for resilient data contract validation between processing stages.

This module facilitates the detection of schema deviations without halting execution,
thereby improving overall system robustness by decoupling data validation failures
from processing continuity.
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
    """Loads a JSON file and instantiates a Pydantic model with configurable validation.

    This function provides two modes for handling data that may not conform to the
    specified Pydantic schema. In 'strict' mode, any validation failure results
    in a `pydantic.ValidationError`. In the default 'tolerant' mode, validation
    errors are logged, and the function proceeds to construct the model instance
    without validation via `model_construct`. This tolerant behavior prioritizes
    operational robustness, allowing downstream systems to process potentially
    incomplete or malformed data, while logging provides visibility
    into data quality issues.

    Args:
        path: The file system path to the JSON file.
        schema: The Pydantic model class to use for parsing and validation.
        artifact_name: A descriptive name for the artifact being loaded, used
            for context in log messages. Defaults to "Artifact".
        mode: The validation mode. 'strict' raises an error on validation
            failure. 'tolerant' logs errors and returns a model instance
            constructed without validation. Defaults to 'tolerant'.

    Returns:
        An instance of the Pydantic model `schema`. In 'tolerant' mode, if
        validation fails, the returned instance is created via
        `model_construct` and may not fully conform to the schema.

    Raises:
        FileNotFoundError: If the file at `path` does not exist.
        json.JSONDecodeError: If the file's content is not valid JSON.
        pydantic.ValidationError: If `mode` is 'strict' and the JSON data fails
            schema validation.
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
        # Initially, perform strict validation to enforce data integrity under nominal conditions.
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

        # If strict validation fails, proceed with a resilient construction of the model, bypassing validation to provide a best-effort instance.
        #
        # Use `model_construct` to create a model instance without re-validating, trusting the input data types. This is the core mechanism for the resilient loading strategy.
        # This resilience pattern allows downstream processes to continue, while logged validation errors provide observability into data quality degradation.
        return schema.model_construct(**data)
    except Exception as e:
        logger.error(f"❌ Error inesperado validando {artifact_name}: {e}")
        if mode == "strict":
            raise
        return schema.model_construct(**data)


def save_versioned_payload(path: Path, payload: BaseModel, artifact_type: str):
    """Serializes a Pydantic model to a versioned JSON file on the filesystem.

    This function ensures the payload includes versioning information before
    serialization. If the `payload` object has a `generation_metadata`
    attribute that is `None`, this function injects a `VersionMetadata`
    instance in-place. The injected metadata uses the provided `artifact_type`
    and a hardcoded artifact version of "1.0.0".

    The Pydantic model is serialized to a dictionary using `model_dump` with
    `by_alias=True` and `exclude_none=False`. The resulting data is then
    written to the specified path as a JSON file, formatted with a 2-space
    indent, encoded in UTF-8, and with `ensure_ascii=False`.

    Args:
        path: The destination file system path for the output JSON file.
        payload: The Pydantic model instance to serialize. This object is
            mutated in-place if its `generation_metadata` attribute is `None`.
        artifact_type: A string identifying the type of artifact, used to
            populate `VersionMetadata` if it is missing from the payload.

    Raises:
        IOError: If an error occurs while writing the file to the specified
            path, such as a permissions error or a non-existent directory.
        TypeError: If the payload contains data that cannot be serialized to
            JSON by the standard `json` library.
        ImportError: If the internal `VersionMetadata` dependency cannot be
            imported from `.common`, which is attempted only when version
            metadata needs to be injected.
    """
    # If the model instance lacks version metadata, inject the current system and contract versions to ensure all serialized outputs are versioned.
    if hasattr(payload, "generation_metadata") and payload.generation_metadata is None:
        from .common import VersionMetadata

        payload.generation_metadata = VersionMetadata(
            artifact_type=artifact_type, artifact_version="1.0.0"
        )

    data = payload.model_dump(by_alias=True, exclude_none=False)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"✅ Artefacto {artifact_type} guardado en: {path}")
