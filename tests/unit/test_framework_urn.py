"""Unit tests for FrameworkURN and FrameworkAliasRegistry."""

from __future__ import annotations

import pytest

from src.assessment_engine.domain.framework_urn import (
    FrameworkAliasRegistry,
    FrameworkURN,
    normalize_framework_list,
    normalize_framework_urn,
)


class TestFrameworkURNUnit:
    """Unit test suite verifying FrameworkURN normalization and strict URN validation."""

    @pytest.mark.parametrize(
        "alias,expected",
        [
            ("ISO27001", FrameworkAliasRegistry.ISO_27001_2022),
            ("ISO-27001", FrameworkAliasRegistry.ISO_27001_2022),
            ("ISO/IEC 27001:2022", FrameworkAliasRegistry.ISO_27001_2022),
            ("ISO/IEC 27001:2013", FrameworkAliasRegistry.ISO_27001_2013),
            ("NIST CSF 2.0", FrameworkAliasRegistry.NIST_CSF_2_0),
            ("NIST SP 800-53 Rev 5", FrameworkAliasRegistry.NIST_800_53_R5),
            ("SOC 2 Type II", FrameworkAliasRegistry.SOC2_2017),
            ("PCI-DSS v4.0", FrameworkAliasRegistry.PCI_DSS_4_0),
            ("GDPR", FrameworkAliasRegistry.EU_GDPR_2016),
            ("EU-GDPR", FrameworkAliasRegistry.EU_GDPR_2016),
            ("HIPAA", FrameworkAliasRegistry.US_HIPAA_2013),
        ],
    )
    def test_alias_resolution(self, alias: str, expected: str) -> None:
        urn = FrameworkURN.from_alias(alias)
        assert str(urn) == expected
        assert urn.urn == expected
        assert normalize_framework_urn(alias) == urn

    def test_urn_properties(self) -> None:
        urn = FrameworkURN("ISO/IEC 27001:2022")
        assert urn.authority == "iso-iec"
        assert urn.identifier == "27001"
        assert urn.version == "2022"

    def test_malformed_urn_prefixes_rejected(self) -> None:
        with pytest.raises(ValueError):
            FrameworkURN("urn:lex:invalid:iso:27001:2022")
        with pytest.raises(ValueError):
            FrameworkURN("urn:ietf:params:scim:schemas:core:2.0:User")
        with pytest.raises(ValueError):
            FrameworkURN("urn:lex:standard:only-two-segments:2022")

    def test_normalize_framework_list_deduplicates(self) -> None:
        items = ["ISO27001", "ISO-27001", "ISO/IEC 27001:2022", "SOC2"]
        result = normalize_framework_list(items)
        assert result == [
            FrameworkURN(FrameworkAliasRegistry.ISO_27001_2022),
            FrameworkURN(FrameworkAliasRegistry.SOC2_2017),
        ]
