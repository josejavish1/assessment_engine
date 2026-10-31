"""Unit tests for FrameworkURN and FrameworkAliasRegistry."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from assessment_engine.domain.framework_urn import (
    FrameworkAliasRegistry,
    FrameworkURN,
    normalize_framework_list,
    normalize_framework_urn,
)


class DummyModel(BaseModel):
    framework: FrameworkURN


class TestFrameworkURNResolution:
    """Verify deterministic alias resolution and canonical URN invariants."""

    @pytest.mark.parametrize(
        "raw_alias,expected_urn",
        [
            ("ISO27001", FrameworkAliasRegistry.ISO_27001_2022),
            ("ISO-27001", FrameworkAliasRegistry.ISO_27001_2022),
            ("ISO/IEC 27001:2022", FrameworkAliasRegistry.ISO_27001_2022),
            ("  iso_iec_27001_2022  ", FrameworkAliasRegistry.ISO_27001_2022),
            (FrameworkAliasRegistry.ISO_27001_2022, FrameworkAliasRegistry.ISO_27001_2022),
            ("ISO/IEC 27001:2013", FrameworkAliasRegistry.ISO_27001_2013),
            ("NIST CSF", FrameworkAliasRegistry.NIST_CSF_2_0),
            ("NIST-CSF-2.0", FrameworkAliasRegistry.NIST_CSF_2_0),
            ("NIST CSF 1.1", FrameworkAliasRegistry.NIST_CSF_1_1),
            ("SOC 2", FrameworkAliasRegistry.SOC2_2017),
            ("SOC2", FrameworkAliasRegistry.SOC2_2017),
            ("CIS Controls v8", FrameworkAliasRegistry.CIS_CONTROLS_V8),
            ("GDPR", FrameworkAliasRegistry.EU_GDPR_2016),
            ("HIPAA", FrameworkAliasRegistry.US_HIPAA_2013),
            ("PCI DSS 4.0", FrameworkAliasRegistry.PCI_DSS_4_0),
            ("DORA", FrameworkAliasRegistry.EU_DORA_2022),
            ("FedRAMP", FrameworkAliasRegistry.US_FEDRAMP_R5),
        ],
    )
    def test_canonical_alias_resolution(self, raw_alias: str, expected_urn: str) -> None:
        urn = FrameworkURN(raw_alias)
        assert str(urn) == expected_urn
        assert urn == expected_urn
        assert hash(urn) == hash(FrameworkURN(expected_urn))

    def test_immutable_properties(self) -> None:
        urn = FrameworkURN("ISO/IEC 27001:2022")
        assert urn.authority == "iso-iec"
        assert urn.identifier == "27001"
        assert urn.version == "2022"
        assert urn.urn == "urn:lex:standard:iso-iec:27001:2022"

    def test_equality_with_different_aliases(self) -> None:
        urn1 = FrameworkURN("ISO27001")
        urn2 = FrameworkURN("ISO/IEC 27001:2022")
        assert urn1 == urn2
        assert urn1 == "ISO-27001"

    def test_normalize_framework_list(self) -> None:
        raw_list = ["ISO27001", "ISO-27001", "NIST CSF", "NIST-CSF-2.0"]
        normalized = normalize_framework_list(raw_list)
        assert len(normalized) == 2
        assert normalized[0] == FrameworkURN("ISO/IEC 27001:2022")
        assert normalized[1] == FrameworkURN("NIST CSF")

    def test_custom_alias_registration(self) -> None:
        target = "urn:lex:standard:internal-sec:cloud-baseline:2025"
        FrameworkAliasRegistry.register_alias("INTERNAL-CLOUD-2025", target)
        resolved = FrameworkURN("internal_cloud_2025")
        assert str(resolved) == target
        assert resolved.authority == "internal-sec"
        assert resolved.identifier == "cloud-baseline"
        assert resolved.version == "2025"

    def test_pydantic_validation(self) -> None:
        model = DummyModel(framework="ISO27001")
        assert isinstance(model.framework, FrameworkURN)
        assert model.framework == "urn:lex:standard:iso-iec:27001:2022"
