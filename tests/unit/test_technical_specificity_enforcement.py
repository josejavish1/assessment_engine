"""
Phase D Characterization and Regression Test Suite: Technical Specificity Enforcement.

Enforces the core invariant: CAPABILITY_MATURITY != IMPLEMENTATION_DETAIL.
1. High capability maturity scores cannot generate unverified commercial product
   features or proprietary architectures in the AS-IS operational diagnostic.
2. T4 (Data & Storage) must not assert ungrounded NetApp CSI, WORM, Volume Encryption,
   VAAI, SVM, or Round Robin/PSP without empirical evidence.
3. T6 (Security & Identity) must not assert centralized PAM vaults, 100% credential
   coverage, session recording, or command logging from generic 5/5/5/3 survey scores.
4. T9 (Digital Workplace) must not assert RODC, SAML 2.0, OpenID Connect, or Windows 10/11 Enterprise.
5. T3 (Network) must not assert physical pathway diversity or conduit segregation for point-to-point links.
"""

from pathlib import Path
import pytest

from assessment_engine.domain.validation.technical_specificity_guard import (
    TechnicalSpecificityGuard,
)
from assessment_engine.infrastructure.runtime_paths import ROOT


def _get_payload_text(tower_id: str) -> str:
    bp_path = ROOT / "working" / "molins_fresh_e2e" / tower_id / f"blueprint_{tower_id.lower()}_payload.json"
    if not bp_path.exists():
        pytest.skip(f"Payload for {tower_id} not found at {bp_path}")
    return bp_path.read_text(encoding="utf-8-sig").lower()


def test_technical_specificity_guard_abstraction():
    """1. TechnicalSpecificityGuard abstracts ungrounded proprietary entities into generic capabilities."""
    raw_text = "Se propone una solución con bóveda PAM centralizada y políticas WORM en almacenamiento."
    sanitized, entities = TechnicalSpecificityGuard.sanitize_draft_entities(
        raw_text, accredited_evidence_corpus=""
    )
    assert "bóveda pam" not in sanitized.lower()
    assert "worm" not in sanitized.lower()
    assert len(entities) >= 2


def test_tower_4_storage_specificity_cleanliness():
    """2. Tower T4 must be free of ungrounded storage features (CSI, WORM, VAAI, SVM, Round Robin)."""
    text = _get_payload_text("T4")
    forbidden = [
        "csi de netapp",
        "netapp csi",
        "worm",
        "volume encryption",
        "vaai",
        "round robin/psp",
    ]
    violations = [f for f in forbidden if f in text]
    assert not violations, f"Tower T4 contains ungrounded storage implementation specifics:\n{violations}"


def test_tower_6_identity_pam_specificity_cleanliness():
    """3. Tower T6 must not assert centralized PAM vaults, 100% coverage, or session recording from survey scores."""
    text = _get_payload_text("T6")
    forbidden = [
        "bóveda pam centralizada",
        "boveda pam centralizada",
        "cobertura del 100% de las cuentas administrativas",
        "grabación de sesión",
        "grabacion de sesion",
        "registro de comandos",
    ]
    violations = [f for f in forbidden if f in text]
    assert not violations, f"Tower T6 contains ungrounded PAM implementation specifics:\n{violations}"


def test_tower_9_workplace_specificity_cleanliness():
    """4. Tower T9 must not assert RODC, SAML 2.0, OpenID Connect, or Windows 10/11 Enterprise."""
    text = _get_payload_text("T9")
    forbidden = [
        "rodc",
        "saml 2.0",
        "saml 2",
        "openid connect",
        "windows 10/11 enterprise",
        "csat/nps",
    ]
    violations = [f for f in forbidden if f in text]
    assert not violations, f"Tower T9 contains ungrounded workplace implementation specifics:\n{violations}"


def test_tower_3_network_conduit_diversity_cleanliness():
    """5. Tower T3 must not assert physical pathway diversity or conduit segregation."""
    text = _get_payload_text("T3")
    forbidden = [
        "diversidad física de trazado",
        "diversidad fisica de trazado",
        "segregación de canalizaciones",
        "segregacion de canalizaciones",
    ]
    violations = [f for f in forbidden if f in text]
    assert not violations, f"Tower T3 asserts unaccredited pathway diversity:\n{violations}"
