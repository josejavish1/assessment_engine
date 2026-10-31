"""Comprehensive verification suite for Task 4.5: Canonical Framework Identifiers (FrameworkURN)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.assessment_engine.domain.framework_urn import (
    FrameworkAliasRegistry,
    FrameworkURN,
    normalize_framework_list,
    normalize_framework_urn,
)
from src.assessment_engine.engine import AssessmentEngine
from src.assessment_engine.models.schemas import (
    AssessmentRequest,
    ControlEvaluationSpec,
    EvidenceItem,
    FrameworkFilterSpec,
    GapAnalysisRequest,
)


class TestFrameworkURNResolution:
    """Verify deterministic alias resolution and canonical URN invariants."""

    @pytest.mark.parametrize(
        "raw_alias,expected_urn",
        [
            ("ISO27001", "urn:lex:standard:iso-iec:27001:2022"),
            ("ISO-27001", "urn:lex:standard:iso-iec:27001:2022"),
            ("ISO/IEC 27001:2022", "urn:lex:standard:iso-iec:27001:2022"),
            ("  iso_iec_27001_2022  ", "urn:lex:standard:iso-iec:27001:2022"),
            ("urn:lex:standard:iso-iec:27001:2022", "urn:lex:standard:iso-iec:27001:2022"),
            ("ISO/IEC 27001:2013", "urn:lex:standard:iso-iec:27001:2013"),
            ("ISO-27001-2013", "urn:lex:standard:iso-iec:27001:2013"),
            ("NIST CSF", "urn:lex:standard:nist:csf:2.0"),
            ("NIST-CSF 2.0", "urn:lex:standard:nist:csf:2.0"),
            ("NIST CSF 1.1", "urn:lex:standard:nist:csf:1.1"),
            ("NIST 800-53", "urn:lex:standard:nist:sp-800-53:r5"),
            ("NIST SP 800-53 Rev 5", "urn:lex:standard:nist:sp-800-53:r5"),
            ("SOC2", "urn:lex:standard:aicpa:soc-2:2017"),
            ("SOC 2 Type II", "urn:lex:standard:aicpa:soc-2:2017"),
            ("AICPA SOC-2", "urn:lex:standard:aicpa:soc-2:2017"),
            ("PCI-DSS", "urn:lex:standard:pci-ssc:pci-dss:4.0"),
            ("PCI DSS v4.0", "urn:lex:standard:pci-ssc:pci-dss:4.0"),
            ("PCI-DSS 3.2.1", "urn:lex:standard:pci-ssc:pci-dss:3.2.1"),
            ("GDPR", "urn:lex:standard:eu:gdpr:2016-679"),
            ("EU-GDPR", "urn:lex:standard:eu:gdpr:2016-679"),
            ("DORA", "urn:lex:standard:eu:dora:2022-2554"),
            ("NIS2", "urn:lex:standard:eu:nis2:2022-2555"),
            ("EU AI Act", "urn:lex:standard:eu:ai-act:2024-1689"),
            ("HIPAA", "urn:lex:standard:us-hhs:hipaa:2013"),
            ("FedRAMP", "urn:lex:standard:us-gsa:fedramp:r5"),
            ("CIS Controls v8", "urn:lex:standard:cis:controls:8.0"),
        ],
    )
    def test_canonical_alias_normalization(self, raw_alias: str, expected_urn: str) -> None:
        urn = FrameworkURN(raw_alias)
        assert str(urn) == expected_urn
        assert urn.urn == expected_urn
        assert isinstance(urn, str)
        assert isinstance(urn, FrameworkURN)

    def test_value_object_component_properties(self) -> None:
        urn = FrameworkURN("ISO/IEC 27001:2022")
        assert urn.authority == "iso-iec"
        assert urn.identifier == "27001"
        assert urn.version == "2022"
        assert repr(urn) == "FrameworkURN('urn:lex:standard:iso-iec:27001:2022')"

    def test_equality_and_hashing_across_aliases(self) -> None:
        u1 = FrameworkURN("ISO27001")
        u2 = FrameworkURN("ISO-27001")
        u3 = FrameworkURN("ISO/IEC 27001:2022")

        assert u1 == u2 == u3
        assert hash(u1) == hash(u2) == hash(u3)
        assert u1 == "ISO-27001"
        assert u1 == "urn:lex:standard:iso-iec:27001:2022"

        cache: dict[FrameworkURN, str] = {u1: "cached_policy_result"}
        assert cache[u2] == "cached_policy_result"
        assert cache[u3] == "cached_policy_result"

    def test_deduplication_helper_preserves_order(self) -> None:
        raw_list = ["ISO27001", "SOC 2 Type II", "ISO-27001", "ISO/IEC 27001:2022", "SOC2"]
        deduped = normalize_framework_list(raw_list)
        assert len(deduped) == 2
        assert deduped[0] == FrameworkURN("urn:lex:standard:iso-iec:27001:2022")
        assert deduped[1] == FrameworkURN("urn:lex:standard:aicpa:soc-2:2017")
        assert normalize_framework_urn("ISO-27001") == deduped[0]

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "",
            "   ",
            "---///___",
            "urn:lex:standard:invalid_only_two_parts:2022",
            "urn:lex:standard:::",
            "urn:lex:invalid:iso:27001:2022",
            "urn:ietf:params:scim:schemas:core:2.0:User",
        ],
    )
    def test_rejects_malformed_or_empty_identifiers(self, invalid_input: str) -> None:
        with pytest.raises(ValueError):
            FrameworkURN(invalid_input)

    def test_custom_alias_registration(self) -> None:
        target = "urn:lex:standard:internal-sec:cloud-baseline:2025"
        FrameworkAliasRegistry.register_alias("INTERNAL-CLOUD-2025", target)
        resolved = FrameworkURN("internal_cloud_2025")
        assert str(resolved) == target
        assert resolved.authority == "internal-sec"
        assert resolved.identifier == "cloud-baseline"
        assert resolved.version == "2025"


class TestIngressBoundaryAndEngineCaching:
    """Verify API ingress normalization and cache hit rate across heterogeneous aliases."""

    def test_pydantic_ingress_normalizes_and_deduplicates_frameworks(self) -> None:
        spec = FrameworkFilterSpec(
            frameworks=["ISO27001", "ISO-27001", "ISO/IEC 27001:2022", "NIST CSF"]
        )
        assert len(spec.frameworks) == 2
        assert spec.frameworks[0] == "urn:lex:standard:iso-iec:27001:2022"
        assert spec.frameworks[1] == "urn:lex:standard:nist:csf:2.0"
        assert all(isinstance(fw, FrameworkURN) for fw in spec.frameworks)

        gap_req = GapAnalysisRequest(
            tenant_id="tenant-alpha",
            target_framework="ISO/IEC 27001:2022",
            baseline_framework="ISO-27001-2013",
            observed_control_ids=["AC-1"],
        )
        assert gap_req.target_framework == "urn:lex:standard:iso-iec:27001:2022"
        assert gap_req.baseline_framework == "urn:lex:standard:iso-iec:27001:2013"

    def test_pydantic_ingress_rejects_invalid_urn(self) -> None:
        with pytest.raises(ValidationError):
            FrameworkFilterSpec(frameworks=["urn:lex:standard:malformed"])
        with pytest.raises(ValidationError):
            FrameworkFilterSpec(frameworks=["urn:lex:invalid:iso:27001:2022"])

    def test_engine_eliminates_cache_misses_across_framework_aliases(self) -> None:
        engine = AssessmentEngine()

        def make_request(fw_alias: str) -> AssessmentRequest:
            return AssessmentRequest(
                tenant_id="tenant-001",
                framework_filter=FrameworkFilterSpec(frameworks=[fw_alias]),
                controls=[
                    ControlEvaluationSpec(
                        control_id="A.5.1",
                        framework=fw_alias,
                        required_evidence_types=["policy_doc"],
                        weight=1.0,
                    )
                ],
                evidence=[
                    EvidenceItem(
                        evidence_id="ev-1",
                        control_id="A.5.1",
                        evidence_type="policy_doc",
                        confidence=0.95,
                    )
                ],
            )

        req_1 = make_request("ISO27001")
        req_2 = make_request("ISO-27001")
        req_3 = make_request("ISO/IEC 27001:2022")

        assert req_1.deterministic_digest() == req_2.deterministic_digest()
        assert req_2.deterministic_digest() == req_3.deterministic_digest()

        res_1 = engine.evaluate(req_1)
        res_2 = engine.evaluate(req_2)
        res_3 = engine.evaluate(req_3)

        assert res_1.summary.frameworks_evaluated == ["urn:lex:standard:iso-iec:27001:2022"]
        assert res_2.summary.frameworks_evaluated == ["urn:lex:standard:iso-iec:27001:2022"]
        assert res_3.summary.frameworks_evaluated == ["urn:lex:standard:iso-iec:27001:2022"]
        assert engine.cache_size == 1

    def test_engine_deduplicates_identical_controls_with_divergent_framework_aliases(self) -> None:
        engine = AssessmentEngine()
        request = AssessmentRequest(
            tenant_id="tenant-002",
            framework_filter=FrameworkFilterSpec(
                frameworks=["ISO27001", "ISO-27001", "ISO/IEC 27001:2022"]
            ),
            controls=[
                ControlEvaluationSpec(
                    control_id="A.5.1",
                    framework="ISO27001",
                    required_evidence_types=["policy_doc"],
                    weight=1.0,
                ),
                ControlEvaluationSpec(
                    control_id="A.5.1",
                    framework="ISO/IEC 27001:2022",
                    required_evidence_types=["policy_doc"],
                    weight=1.0,
                ),
            ],
            evidence=[
                EvidenceItem(
                    evidence_id="ev-1",
                    control_id="A.5.1",
                    evidence_type="policy_doc",
                    confidence=0.95,
                )
            ],
        )

        response = engine.evaluate(request)
        assert response.summary.total_controls == 1
        assert len(response.findings) == 1
        assert response.findings[0].framework == "urn:lex:standard:iso-iec:27001:2022"
