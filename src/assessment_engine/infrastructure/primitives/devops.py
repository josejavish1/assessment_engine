"""
Canonical Packaging, CI/CD & Supply Chain Engine — System 13 (Google Distroless / OSV SOTA 2026).
Consolidated containerization and automated verification suite:
1. Google Distroless multi-stage Containerfile generator (<60MB, nonroot, zero bash shell).
2. Production docker-compose.yml orchestrator with healthchecks and restart policies.
3. GitHub Actions CI/CD matrix generator (lint, typecheck, pytest, distroless build).
4. Google OSV (api.osv.dev) supply-chain vulnerability auditor for Python dependencies.
5. Strict environment and configuration validator (Pydantic / JSON Schema).
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.distroless_builder import DistrolessBuilderPrimitive, distroless_builder
from assessment_engine.infrastructure.primitives.compose_orchestrator import ComposeOrchestratorPrimitive, compose_orchestrator
from assessment_engine.infrastructure.primitives.ci_cd_generator import CICDGeneratorPrimitive, ci_cd_generator
from assessment_engine.infrastructure.primitives.dependency_vulnerability_auditor import (
    DependencyVulnerabilityAuditorPrimitive,
    dependency_vulnerability_auditor
)
from assessment_engine.infrastructure.primitives.config_validator import ConfigValidatorPrimitive, config_validator

devops_engine = distroless_builder
vulnerability_auditor = dependency_vulnerability_auditor
