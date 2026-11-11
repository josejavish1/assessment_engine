"""Unit tests for ActuarialParameterPack and KernelCalibrationPack loading and validation (SR 11-7)."""

from __future__ import annotations

import pytest

from assessment_engine.domain.actuarial.parameter_pack_loader import (
    ActuarialParameterPack,
    KernelCalibrationPack,
    PertDistributionSpec,
)
from assessment_engine.infrastructure.parameter_pack_loader import (
    load_actuarial_parameter_pack,
    load_kernel_calibration_pack,
)


def test_load_legacy_generic_v1_pack_succeeds_and_computes_sha256() -> None:
    """Verifies that the canonical actuarial parameter pack loads and computes a 64-char SHA-256."""
    pack = load_actuarial_parameter_pack()
    assert isinstance(pack, ActuarialParameterPack)
    assert pack.pack_id == "legacy_generic_v1"
    assert pack.schema_version == "2.0.0"
    assert len(pack.pack_sha256) == 64
    assert pack.base_currency == "EUR"

    # All canonical towers T1 through T11 must be present
    for t_idx in range(1, 12):
        t_code = f"T{t_idx}"
        assert t_code in pack.towers, f"Missing tower {t_code} in parameter pack"
        t_spec = pack.towers[t_code]
        assert t_spec.default_tef_annual > 0.0
        assert t_spec.default_rto_hours > 0.0
        assert t_spec.default_direct_replacement_cost >= 0.0


def test_load_kernel_calibration_v1_succeeds_and_computes_sha256() -> None:
    """Verifies that the kernel calibration pack loads with all 13 mathematical hyperparameters."""
    cal = load_kernel_calibration_pack()
    assert isinstance(cal, KernelCalibrationPack)
    assert cal.calibration_id == "fair_copula_kernel_std"
    assert cal.schema_version == "1.0.0"
    assert len(cal.calibration_sha256) == 64

    assert 0.0 < cal.vuln_min < cal.vuln_max <= 1.0
    assert cal.copula_df >= 3
    assert cal.gamma > 0.0
    assert cal.kappa > 0.0
    assert 0.0 <= cal.max_dependence_loading <= 1.0
    assert 0.0 < cal.max_copula_correlation < 1.0
    assert cal.baseline_horizon_years == 3


def test_pert_distribution_spec_validation() -> None:
    """Verifies that PertDistributionSpec strictly enforces min <= mode <= max."""
    valid_pert = PertDistributionSpec(min_val=1.0, mode_val=2.0, max_val=5.0)
    assert valid_pert.min_val == 1.0
    assert valid_pert.mode_val == 2.0
    assert valid_pert.max_val == 5.0

    with pytest.raises(ValueError, match="Invalid PERT ordering"):
        PertDistributionSpec(min_val=5.0, mode_val=2.0, max_val=1.0)

    with pytest.raises(ValueError, match="Invalid PERT ordering"):
        PertDistributionSpec(min_val=1.0, mode_val=6.0, max_val=5.0)


def test_kernel_calibration_bounds_validation() -> None:
    """Verifies that KernelCalibrationPack rejects vuln_min >= vuln_max."""
    with pytest.raises(
        ValueError, match="vuln_min must be strictly less than vuln_max"
    ):
        KernelCalibrationPack(
            calibration_id="invalid",
            calibration_version="v1",
            vuln_min=0.80,
            vuln_max=0.50,
            gamma=4.0,
            kappa=0.35,
            copula_df=4,
            intra_tower_boost=0.25,
            secondary_loss_cv=0.50,
            spof_cmmi_penalty=1,
            max_dependence_loading=0.35,
            max_copula_correlation=0.85,
            rto_cmmi_degradation_slope=0.15,
            rto_spof_multiplier=1.35,
            catastrophic_tail_quantile=0.95,
        )


def test_parameter_pack_sha256_canonical_and_idempotent() -> None:
    """Verifies that compute_canonical_sha256 is deterministic and ignores pack_sha256."""
    pack1 = load_actuarial_parameter_pack()
    hash1 = pack1.compute_canonical_sha256()

    pack2 = pack1.model_copy(update={"pack_sha256": "DIFFERENT_HASH"})
    hash2 = pack2.compute_canonical_sha256()

    assert hash1 == hash2
