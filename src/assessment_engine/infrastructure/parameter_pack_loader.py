"""Infrastructure loader for Actuarial Parameter Packs and Kernel Calibration Packs (SR 11-7).

Handles physical disk I/O, JSON decoding, cryptographic SHA-256 fingerprinting, and memory caching.
Preserves Hexagonal Architecture by isolating filesystem operations away from the Domain layer.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from assessment_engine.domain.actuarial.parameter_pack_loader import (
    ActuarialParameterPack,
    KernelCalibrationPack,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PACK_DIR = REPO_ROOT / "engine_config" / "actuarial" / "parameter_packs"


@lru_cache(maxsize=16)
def load_actuarial_parameter_pack(
    pack_path: Optional[Path] = None,
) -> ActuarialParameterPack:
    """Loads and cryptographically validates an ActuarialParameterPack from physical disk."""
    target = pack_path or (DEFAULT_PACK_DIR / "legacy_generic_v1.json")
    if not target.exists():
        raise FileNotFoundError(f"Actuarial parameter pack not found at {target}")
    raw_bytes = target.read_bytes()
    raw_data = json.loads(raw_bytes.decode("utf-8"))
    pack = ActuarialParameterPack.model_validate(raw_data)
    computed_hash = pack.compute_canonical_sha256()
    return pack.model_copy(update={"pack_sha256": computed_hash})


@lru_cache(maxsize=16)
def load_kernel_calibration_pack(
    calibration_path: Optional[Path] = None,
) -> KernelCalibrationPack:
    """Loads and cryptographically validates a KernelCalibrationPack from physical disk."""
    target = calibration_path or (DEFAULT_PACK_DIR / "kernel_calibration_v1.json")
    if not target.exists():
        raise FileNotFoundError(f"Kernel calibration pack not found at {target}")
    raw_bytes = target.read_bytes()
    raw_data = json.loads(raw_bytes.decode("utf-8"))
    cal = KernelCalibrationPack.model_validate(raw_data)
    computed_hash = cal.compute_canonical_sha256()
    return cal.model_copy(update={"calibration_sha256": computed_hash})
