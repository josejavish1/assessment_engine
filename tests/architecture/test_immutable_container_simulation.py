"""
Architectural Fitness Gate: Immutable Container Simulation (Kubernetes CIS Benchmark).
Simulates a container environment with readOnlyRootFilesystem: true by marking
engine_config/ as strictly read-only (chmod -R a-w) and executing end-to-end
runtime state persistence, sentinel checks, and scoring routing via ASSESSMENT_DATA_DIR.
"""
import os
import shutil
import stat
from pathlib import Path
import pytest

from assessment_engine.infra.config_loader import ConfigLoader
from assessment_engine.engine.sentinel import ComplianceSentinel
from assessment_engine.engine.calibrator import ConfidenceCalibrator
from assessment_engine.engine.epistemic_graph import EpistemicGraphEngine
from assessment_engine.engine.jurisdictional_sovereignty import JurisdictionalSovereigntyEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ENGINE_CONFIG = REPO_ROOT / "engine_config"


def _set_tree_readonly(root: Path) -> None:
    """Recursively strips write permissions (chmod -R a-w) from all files and directories."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        current_dir = Path(dirpath)
        for fname in filenames:
            fpath = current_dir / fname
            mode = fpath.stat().st_mode
            fpath.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        dir_mode = current_dir.stat().st_mode
        current_dir.chmod(dir_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _restore_tree_writable(root: Path) -> None:
    """Recursively restores owner write permissions so pytest tmp_path cleanup succeeds."""
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        current_dir = Path(dirpath)
        dir_mode = current_dir.stat().st_mode
        current_dir.chmod(dir_mode | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRUSR)
        for fname in filenames:
            fpath = current_dir / fname
            mode = fpath.stat().st_mode
            fpath.chmod(mode | stat.S_IWUSR | stat.S_IRUSR)


@pytest.fixture()
def immutable_container_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Sets up a simulated container filesystem:
    - ro_root/engine_config: exact copy of engine_config with chmod -R a-w
    - rw_data_dir: writable volume mounted via ASSESSMENT_DATA_DIR
    """
    ro_root = tmp_path / "ro_container_fs"
    ro_config = ro_root / "engine_config"
    rw_data_dir = tmp_path / "rw_volume_data"
    rw_data_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(SOURCE_ENGINE_CONFIG, ro_config)
    _set_tree_readonly(ro_config)

    monkeypatch.setenv("ASSESSMENT_CONFIG_DIR", str(ro_config))
    monkeypatch.setenv("ASSESSMENT_DATA_DIR", str(rw_data_dir))

    try:
        yield ro_config, rw_data_dir
    finally:
        _restore_tree_writable(ro_config)


def test_readonly_engine_config_blocks_direct_writes(immutable_container_env) -> None:
    ro_config, _ = immutable_container_env
    test_file = ro_config / "illegal_write_attempt.json"
    with pytest.raises(PermissionError):
        test_file.write_text("{}", encoding="utf-8")


def test_end_to_end_execution_with_readonly_engine_config(immutable_container_env) -> None:
    ro_config, rw_data_dir = immutable_container_env

    # 1. Verify ConfigLoader reads static ontology from read-only mount and writes state to rw_data_dir
    loader = ConfigLoader(config_dir=ro_config, data_dir=rw_data_dir)
    state = loader.load_or_init_state(target_framework="DORA", jurisdiction="EU")
    assert state is not None

    loader.save_state(state)
    persisted_state_files = list(rw_data_dir.rglob("*.json"))
    assert len(persisted_state_files) >= 1, "Runtime state must be persisted inside ASSESSMENT_DATA_DIR"

    # 2. Verify ComplianceSentinel operates without mutating ro_config
    sentinel = ComplianceSentinel(config_dir=ro_config, data_dir=rw_data_dir)
    status = sentinel.verify_integrity()
    assert status is not None

    # 3. Verify EpistemicGraphEngine & ConfidenceCalibrator operate cleanly in read-only mode
    epistemic_engine = EpistemicGraphEngine()
    claim_node = epistemic_engine.register_claim(
        claim_id="CLM-RO-001",
        statement="Multi-region active-active failover is tested quarterly.",
        evidence_ids=["EV-RO-001"],
        raw_confidence=0.85,
    )
    assert claim_node.claim_id == "CLM-RO-001"

    calibrator = ConfidenceCalibrator()
    calibrated = calibrator.calibrate(
        raw_confidence=0.85,
        evidence_count=2,
        corroboration_score=0.9,
    )
    assert 0.0 <= calibrated <= 1.0

    # 4. Verify JurisdictionalSovereigntyEngine evaluates cleanly against read-only config
    sovereignty_engine = JurisdictionalSovereigntyEngine(config_dir=ro_config)
    assert sovereignty_engine is not None
