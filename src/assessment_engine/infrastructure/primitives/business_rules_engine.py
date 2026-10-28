# core/primitives/business_rules_engine.py

import dataclasses
from datetime import datetime, timezone
from typing import List, Dict, Any


@dataclasses.dataclass(frozen=True)
class BusinessRuleViolation:
    rule_id: str
    category: str
    message: str
    severity: str
    remediation_hint: str


@dataclasses.dataclass(frozen=True)
class BusinessRulesReport:
    passed: bool
    violations: List[BusinessRuleViolation]
    rules_checked: int
    timestamp_utc: str


class BusinessRulesEngine:
    """
    Engine to audit automated legal compliance (GDPR/LSSI), fiscal rules (VAT/IVA),
    and public endpoint hygiene.
    """

    def _create_report(self, violations: List[BusinessRuleViolation], rules_checked: int) -> BusinessRulesReport:
        """Helper to create a deterministic report."""
        passed = sum(1 for v in violations if v.severity == "CRITICAL") == 0
        return BusinessRulesReport(
            passed=passed,
            violations=violations,
            rules_checked=rules_checked,
            timestamp_utc=datetime.now(timezone.utc).isoformat()
        )

    def audit_form_schema(self, schema: Dict[str, Any]) -> BusinessRulesReport:
        """Audits a form schema for GDPR compliance."""
        violations: List[BusinessRuleViolation] = []
        rules_checked = 1

        fields = schema.get("fields", [])
        if not fields:
            return self._create_report(violations, rules_checked)

        pii_fields = {"email", "phone", "tax_id", "full_name", "address"}
        has_pii = any(f in pii_fields for f in fields)

        if has_pii:
            has_consent = any("consent" in str(f).lower() for f in fields)
            if not has_consent:
                violations.append(
                    BusinessRuleViolation(
                        rule_id="RULE-RGPD-001",
                        category="privacy",
                        message="Falta campo de consentimiento RGPD para datos PII.",
                        severity="CRITICAL",
                        remediation_hint="Añade un campo 'consent_rgpd_accepted' al formulario."
                    )
                )

        return self._create_report(violations, rules_checked)

    def audit_pricing_contract(self, pricing: Dict[str, Any]) -> BusinessRulesReport:
        """Audits a pricing contract for fiscal compliance."""
        violations: List[BusinessRuleViolation] = []
        rules_checked = 1

        if not pricing:
            return self._create_report(violations, rules_checked)

        has_tax = "tax_rate_percent" in pricing or "tax_amount" in pricing

        if not has_tax:
            violations.append(
                BusinessRuleViolation(
                    rule_id="RULE-TAX-001",
                    category="fiscal",
                    message="El contrato de precio no desglosa el IVA/Impuesto.",
                    severity="CRITICAL",
                    remediation_hint="Añade 'tax_rate_percent' y 'tax_amount' al contrato."
                )
            )

        return self._create_report(violations, rules_checked)

    def audit_endpoint_security(self, endpoint_meta: Dict[str, Any]) -> BusinessRulesReport:
        """Audits an endpoint metadata for security and rate limiting."""
        violations: List[BusinessRuleViolation] = []
        rules_checked = 1

        if not endpoint_meta:
            return self._create_report(violations, rules_checked)

        is_public = endpoint_meta.get("is_public", False)
        method = str(endpoint_meta.get("method", "")).upper()
        rate_limited = endpoint_meta.get("rate_limited", False)

        if is_public and method in {"POST", "PUT", "PATCH", "DELETE"} and not rate_limited:
            violations.append(
                BusinessRuleViolation(
                    rule_id="RULE-SEC-001",
                    category="security",
                    message="Endpoint público de mutación sin rate limiting.",
                    severity="WARNING",
                    remediation_hint="Habilita rate_limited=True en la configuración del endpoint."
                )
            )

        return self._create_report(violations, rules_checked)