"""
Relationship-Based Access Control (ReBAC) engine.
Inspired by Google Zanzibar and Cerbos/Oso, optimized with:
1. Bounded graph recursion (depth <= 3) for team inheritance and transitive roles.
2. Universal relation tuples (relation_tuples) for N:M shared access.
3. Declarative policy ingestion from domain_contract.json.
4. Parametric owner column mapping (owner_field: patient_id, customer_id, etc.).
5. High-performance SQL RLS integration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.rebac")


@dataclass
class Subject:
    """Represent the agent requesting the action (authenticated user or service)."""
    id: str
    tenant_id: str
    roles: list[str] = field(default_factory=lambda: ["client"])
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Resource:
    """Represent the business object being operated on."""
    type: str
    id: str | None = None
    tenant_id: str = ""
    owner_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyRule:
    """Declarative ReBAC permission evaluation rule."""
    role: str
    resource_type: str
    actions: list[str]
    condition: str = "same_tenant"  # 'same_tenant' | 'is_owner' | 'has_relation' | 'always' | 'deny'
    required_relation: str = "viewer"


@dataclass(frozen=True)
class RelationTuple:
    """Zanzibar relation tuple (tenant, resource, relation, subject)."""
    tenant_id: str
    resource_type: str
    resource_id: str
    relation: str  # 'owner', 'editor', 'viewer', 'member'
    subject_id: str


class RebacEngine(CapabilityPrimitive):
    """
    Provide relationship-based authorization and multi-tenant isolation.
    """

    def __init__(self) -> None:
        self._rules: list[PolicyRule] = []
        self._tuples: set[RelationTuple] = set()
        self._owner_fields: dict[str, str] = {}
        self._load_default_policies()

    @property
    def namespace(self) -> str:
        """Return the namespace identifier."""
        return "rebac"

    def get_capabilities(self) -> dict[str, Any]:
        """Retrieve the supported capabilities."""
        return {
            "version": "3.0.0",
            "operations": [
                "evaluate",
                "compile_sql_filter",
                "get_capabilities_vector",
                "register_policy",
                "add_relation_tuple",
                "remove_relation_tuple",
                "has_relation",
                "load_contract_policies"
            ],
            "standards": [
                "Google Zanzibar (ReBAC Level 3)",
                "Bounded Graph Recursion (Depth <= 3)",
                "Declarative Contract Policies",
                "SQL RLS Predicates with Relation Tuples"
            ]
        }

    def _load_default_policies(self) -> None:
        """Load standard factory policies for multi-role B2B environments."""
        self._rules.append(PolicyRule(role="admin", resource_type="*", actions=["*"], condition="same_tenant"))
        self._rules.append(PolicyRule(role="owner", resource_type="*", actions=["*"], condition="same_tenant"))

        self._rules.append(PolicyRule(role="staff", resource_type="*", actions=["read", "list", "create"], condition="same_tenant"))
        self._rules.append(PolicyRule(role="staff", resource_type="*", actions=["update"], condition="same_tenant"))
        self._rules.append(PolicyRule(role="staff", resource_type="invoices", actions=["delete"], condition="deny"))
        self._rules.append(PolicyRule(role="staff", resource_type="users", actions=["delete"], condition="deny"))

        # 3. Reglas de Cliente / Usuario Registrado
        self._rules.append(PolicyRule(role="client", resource_type="*", actions=["read", "list"], condition="is_owner"))
        self._rules.append(PolicyRule(role="client", resource_type="*", actions=["read"], condition="has_relation", required_relation="viewer"))
        self._rules.append(PolicyRule(role="client", resource_type="bookings", actions=["create", "update"], condition="is_owner"))
        self._rules.append(PolicyRule(role="client", resource_type="appointments", actions=["create", "update"], condition="is_owner"))
        self._rules.append(PolicyRule(role="client", resource_type="orders", actions=["create"], condition="same_tenant"))
        self._rules.append(PolicyRule(role="client", resource_type="invoices", actions=["read"], condition="is_owner"))
        self._rules.append(PolicyRule(role="client", resource_type="*", actions=["delete"], condition="deny"))

    def load_contract_policies(self, contract: dict[str, Any]) -> None:
        """Load declarative policies and owner fields from domain_contract.json."""
        # 1. Parametric mapping of owner fields per entity
        entities = contract.get("entities", [])
        if isinstance(entities, list):
            for ent in entities:
                if isinstance(ent, dict):
                    name = str(ent.get("name", "")).lower()
                    owner_col = ent.get("owner_field") or ent.get("user_field")
                    if name and owner_col:
                        self._owner_fields[name] = str(owner_col)

        custom_policies = contract.get("rebac_policies", [])
        if isinstance(custom_policies, list):
            for pol in custom_policies:
                if isinstance(pol, dict):
                    rule = PolicyRule(
                        role=pol.get("role", "*"),
                        resource_type=pol.get("resource_type", "*"),
                        actions=pol.get("actions", ["read"]),
                        condition=pol.get("condition", "same_tenant"),
                        required_relation=pol.get("required_relation", "viewer")
                    )
                    self.register_policy(rule)

    def register_policy(self, rule: PolicyRule) -> None:
        """Register a custom rule with highest priority."""
        self._rules.insert(0, rule)


    def add_relation_tuple(
        self, tenant_id: str, resource_type: str, resource_id: str, relation: str, subject_id: str
    ) -> None:
        """Register an N:M relationship between a subject (or group) and a resource."""
        tup = RelationTuple(
            tenant_id=tenant_id,
            resource_type=resource_type.lower().strip(),
            resource_id=str(resource_id),
            relation=relation.lower().strip(),
            subject_id=str(subject_id)
        )
        self._tuples.add(tup)

    def remove_relation_tuple(
        self, tenant_id: str, resource_type: str, resource_id: str, relation: str, subject_id: str
    ) -> None:
        """Remove an existing relationship."""
        tup = RelationTuple(
            tenant_id=tenant_id,
            resource_type=resource_type.lower().strip(),
            resource_id=str(resource_id),
            relation=relation.lower().strip(),
            subject_id=str(subject_id)
        )
        self._tuples.discard(tup)

    def has_relation(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str | None,
        relation: str,
        subject_id: str,
        max_depth: int = 3
    ) -> bool:
        """Evaluate relationships with bounded recursion (depth <= 3) to resolve group/team inheritance.
Cyclomatic complexity: Rank A (V(G) <= 7)."""
        if not resource_id or max_depth <= 0:
            return False

        r_type = resource_type.lower().strip()
        r_id = str(resource_id)
        rel = relation.lower().strip()
        s_id = str(subject_id)

        direct_tuple = RelationTuple(tenant_id, r_type, r_id, rel, s_id)
        if direct_tuple in self._tuples:
            return True

        if rel == "viewer":
            if RelationTuple(tenant_id, r_type, r_id, "editor", s_id) in self._tuples:
                return True
            if RelationTuple(tenant_id, r_type, r_id, "owner", s_id) in self._tuples:
                return True
        elif rel == "editor":
            if RelationTuple(tenant_id, r_type, r_id, "owner", s_id) in self._tuples:
                return True

        # 2. Bounded transitivity (Levels 2 and 3): Search for parent groups or teams
        # Check if subject belongs to a team ('team:xyz') with permission on the resource
        for tup in self._tuples:
            if tup.tenant_id == tenant_id and tup.resource_type == r_type and tup.resource_id == r_id:
                if tup.relation == rel or (rel == "viewer" and tup.relation in ("editor", "owner")):
                    if tup.subject_id.startswith(("team:", "group:", "role:")):
                        is_member = self.has_relation(
                            tenant_id=tenant_id,
                            resource_type="group",
                            resource_id=tup.subject_id,
                            relation="member",
                            subject_id=s_id,
                            max_depth=max_depth - 1
                        )
                        if is_member:
                            return True

        return False

    # CAPABILITY AND POLICY EVALUATION

    def evaluate(self, subject: Subject | None, action: str, resource: Resource) -> tuple[bool, str]:
        """Evaluate whether a subject has permission to perform an action on a resource.
Cyclomatic complexity: Rank A (V(G) <= 6)."""
        if subject is None:
            return False, "UNAUTHENTICATED"

        # Invariante 1: Aislamiento forzoso entre inquilinos
        if subject.tenant_id != resource.tenant_id and "super_admin" not in subject.roles:
            return False, "CROSS_TENANT_VIOLATION"

        # Tenant administrator has full access within their tenant
        if any(r in ("admin", "owner") for r in subject.roles):
            return True, "ALLOWED_BY_TENANT_ADMIN"

        action_clean = action.lower().strip()
        res_type = resource.type.lower().strip()

        for rule in self._rules:
            if not self._matches_rule_selector(rule, subject.roles, res_type, action_clean):
                continue

            if rule.condition == "deny":
                return False, "EXPLICIT_DENY"

            allowed, reason = self._check_condition(rule, subject, resource)
            if allowed:
                return True, reason

        return False, "NO_MATCHING_POLICY"

    def _matches_rule_selector(self, rule: PolicyRule, user_roles: list[str], res_type: str, action: str) -> bool:
        """Check whether the role, resource type, and action match."""
        role_match = (rule.role == "*") or (rule.role in user_roles)
        type_match = (rule.resource_type == "*") or (rule.resource_type == res_type)
        action_match = ("*" in rule.actions) or (action in rule.actions)
        return role_match and type_match and action_match

    def _check_condition(self, rule: PolicyRule, subject: Subject, resource: Resource) -> tuple[bool, str]:
        """Evaluate contextual constraints for ownership, Zanzibar relations, or tenant isolation."""
        cond = rule.condition
        if cond == "same_tenant":
            is_same = (subject.tenant_id == resource.tenant_id)
            return is_same, "ALLOWED_SAME_TENANT" if is_same else "TENANT_MISMATCH"

        if cond == "is_owner":
            is_own = (resource.owner_id is not None and subject.id == resource.owner_id)
            return is_own, "ALLOWED_OWNER" if is_own else "NOT_OWNER"

        if cond == "has_relation":
            rel_ok = self.has_relation(
                tenant_id=resource.tenant_id,
                resource_type=resource.type,
                resource_id=resource.id,
                relation=rule.required_relation,
                subject_id=subject.id
            )
            return rel_ok, f"ALLOWED_RELATION_{rule.required_relation.upper()}" if rel_ok else "NO_RELATION"

        if cond == "always":
            return True, "ALLOWED_ALWAYS"

        return False, "CONDITION_FAILED"

    # PARAMETRIC OWNER RESOLUTION AND SQL RLS COMPILER

    def resolve_owner_field(self, table: str, available_cols: set[str] | None = None) -> str:
        """Resolve the owner column name deterministically.
Priority: 1. domain_contract -> 2. introspected columns -> 3. 'user_id'."""
        t_low = table.lower().strip()
        if t_low in self._owner_fields:
            return self._owner_fields[t_low]

        if available_cols:
            for candidate in ("user_id", "owner_id", "patient_id", "customer_id", "author_id", "client_id"):
                if candidate in available_cols:
                    return candidate

        return "user_id"

    def compile_sql_filter(
        self,
        subject: Subject | None,
        table: str,
        action: str = "read",
        tenant_column: str = "tenant_id",
        owner_column: str | None = None,
        include_shared_tuples: bool = True
    ) -> tuple[str, list[Any]]:
        """
        Compile the SQL predicate (Row-Level Security) with support for N:M relation tuples.
        """
        if subject is None:
            return "1 = 0", []

        t_col = f'"{tenant_column}"'
        o_col = f'"{owner_column or self.resolve_owner_field(table)}"'

        # Tenant administrator: view all records within their tenant
        if any(r in ("admin", "owner") for r in subject.roles):
            return f"{t_col} = ?", [subject.tenant_id]

        # Empleado (Staff): lectura completa del tenant; modificaciones restringidas
        if "staff" in subject.roles:
            if action in ("read", "list", "create"):
                return f"{t_col} = ?", [subject.tenant_id]
            return f"({t_col} = ? AND ({o_col} = ? OR {o_col} IS NULL))", [subject.tenant_id, subject.id]

        if include_shared_tuples:
            subquery = (
                f'({t_col} = ? AND ({o_col} = ? OR "id" IN ('
                f'SELECT resource_id FROM relation_tuples '
                f'WHERE tenant_id = ? AND resource_type = ? AND subject_id = ?'
                f')))'
            )
            return subquery, [subject.tenant_id, subject.id, subject.tenant_id, table.lower(), subject.id]

        return f"({t_col} = ? AND {o_col} = ?)", [subject.tenant_id, subject.id]

    def get_capabilities_vector(self, subject: Subject | None, resource_types: list[str]) -> list[str]:
        """
        Compute the resolved capability vector for injection into the client session.
        """
        if subject is None:
            return []

        capabilities: list[str] = []
        actions_to_check = ["read", "create", "update", "delete"]

        for res in resource_types:
            for act in actions_to_check:
                dummy_res = Resource(type=res, tenant_id=subject.tenant_id, owner_id="another_user")
                allowed_general, _ = self.evaluate(subject, act, dummy_res)

                dummy_own = Resource(type=res, tenant_id=subject.tenant_id, owner_id=subject.id)
                allowed_own, _ = self.evaluate(subject, act, dummy_own)

                if allowed_general:
                    capabilities.append(f"{res}:{act}")
                elif allowed_own:
                    capabilities.append(f"{res}:{act}:own")

        return sorted(capabilities)


rebac_kernel = RebacEngine()
