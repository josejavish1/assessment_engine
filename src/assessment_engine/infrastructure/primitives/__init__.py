"""
Autonomuos Core Capability Primitives (Tier-1 Host APIs).
Exported modular capabilities following the WASI 0.2 & MCP 2026 standard.
Full 74 Gemas Registry covering Code Intelligence, Data, Security, Growth, Operations, and DevOps.
"""

from assessment_engine.infrastructure.foundry.agentless_fixer import AgentlessFixerPrimitive, agentless_fixer
from assessment_engine.infrastructure.auditor.mutation_probe import MutationTestingProbePrimitive, mutation_probe
from assessment_engine.infrastructure.primitives.accessibility_oracle import AccessibilityOraclePrimitive, accessibility_oracle
from assessment_engine.infrastructure.primitives.admin_security_guard import AdminSecurityGuardPrimitive, admin_security_guard
from assessment_engine.infrastructure.primitives.architect_editor import ArchitectEditorPrimitive, architect_editor
from assessment_engine.infrastructure.primitives.ast_rewriter import ASTRewriterPrimitive, ast_rewriter
from assessment_engine.infrastructure.primitives.async_task_queue import AsyncTaskQueuePrimitive, async_task_queue
from assessment_engine.infrastructure.primitives.audit_trail import AuditTrailPrimitive, audit_trail
from assessment_engine.infrastructure.primitives.auth import IdentityPrimitive, auth_primitive
from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive
from assessment_engine.infrastructure.primitives.blob import BlobStoragePrimitive, blob_primitive
from assessment_engine.infrastructure.primitives.booking_slots import BookingSlotsPrimitive, booking_slots
from assessment_engine.infrastructure.primitives.communications_bus import CommunicationsBusPrimitive, communications_bus
from assessment_engine.infrastructure.primitives.inventory_allocation import InventoryAllocationPrimitive, inventory_allocation
from assessment_engine.infrastructure.primitives.pricing_rules import PricingRulesPrimitive, pricing_rules
from assessment_engine.infrastructure.primitives.spatial_geo import SpatialGeoPrimitive, spatial_geo
from assessment_engine.infrastructure.primitives.brotli_compression import BrotliCompressionPrimitive, brotli_compression
from assessment_engine.infrastructure.primitives.canonical_urls import CanonicalURLsPrimitive, canonical_urls
from assessment_engine.infrastructure.primitives.ci_cd_generator import CICDGeneratorPrimitive, ci_cd_generator
from assessment_engine.infrastructure.primitives.code_hygiene import CodeHygienePrimitive, code_hygiene
from assessment_engine.infrastructure.primitives.cognitive_ingest import CognitiveIngestPrimitive, cognitive_ingest
from assessment_engine.infrastructure.primitives.compose_orchestrator import ComposeOrchestratorPrimitive, compose_orchestrator
from assessment_engine.infrastructure.primitives.config_validator import ConfigValidatorPrimitive, config_validator
from assessment_engine.infrastructure.primitives.content_pruner import ContentPruner, content_pruner
from assessment_engine.infrastructure.primitives.context_condenser import ContextCondenser, context_condenser
from assessment_engine.infrastructure.primitives.concurrency_guard import ConcurrencyGuardPrimitive, concurrency_guard
from assessment_engine.infrastructure.primitives.csrf_hmac_guard import CSRFHMACGuardPrimitive, csrf_hmac_guard
from assessment_engine.infrastructure.primitives.cursor_paginator import CursorPaginator, KeysetPage, cursor_paginator
from assessment_engine.infrastructure.primitives.data_erasure_cascade import DataErasureCascadePrimitive, data_erasure_cascade
from assessment_engine.infrastructure.primitives.db import DynamicDatabasePrimitive, db_primitive
from assessment_engine.infrastructure.primitives.dead_letter_queue import DeadLetterQueuePrimitive, dead_letter_queue
from assessment_engine.infrastructure.primitives.dead_link_sentinel import DeadLinkSentinelPrimitive, dead_link_sentinel
from assessment_engine.infrastructure.primitives.friction_sensor import FrictionSensorPrimitive, friction_sensor
from assessment_engine.infrastructure.primitives.dependency_vulnerability_auditor import (
    DependencyVulnerabilityAuditorPrimitive,
    dependency_vulnerability_auditor,
)
from assessment_engine.infrastructure.primitives.design_system_synthesizer import (
    DesignSystemSynthesizer,
    design_system_synthesizer,
)
from assessment_engine.infrastructure.primitives.distroless_builder import DistrolessBuilderPrimitive, distroless_builder
from assessment_engine.infrastructure.primitives.dom_accessibility_serializer import (
    DOMAccessibilitySerializer,
    dom_accessibility_serializer,
)
from assessment_engine.infrastructure.primitives.email_oracle import EmailOraclePrimitive, email_oracle
from assessment_engine.infrastructure.primitives.entrypoint_orchestrator import (
    EntrypointOrchestratorPrimitive,
    entrypoint_orchestrator,
)
from assessment_engine.infrastructure.primitives.execution_guard import ExecutionGuardPrimitive, execution_guard
from assessment_engine.infrastructure.primitives.exponential_backoff_jitter import (
    ExponentialBackoffJitterPrimitive,
    exponential_backoff_jitter,
)
from assessment_engine.infrastructure.primitives.fts5_search import FTS5SearchPrimitive, fts5_search
from assessment_engine.infrastructure.primitives.geo_engine import GeoEnginePrimitive, geo_engine
from assessment_engine.infrastructure.primitives.geoip_resolver import GeoIPResolverPrimitive, geoip_resolver
from assessment_engine.infrastructure.primitives.git_worktree_runner import GitWorktreeRunnerPrimitive, git_worktree_runner
from assessment_engine.infrastructure.primitives.honeypot_antispam import HoneypotAntiSpamPrimitive, honeypot_antispam
from assessment_engine.infrastructure.primitives.html_sanitizer import HTMLSanitizerPrimitive, html_sanitizer
from assessment_engine.infrastructure.primitives.in_memory_micro_cache import InMemoryMicroCachePrimitive, in_memory_micro_cache
from assessment_engine.infrastructure.primitives.intl_formatter import IntlFormatterPrimitive, intl_formatter
from assessment_engine.infrastructure.primitives.legal_engine import LegalEnginePrimitive, legal_engine
from assessment_engine.infrastructure.primitives.litestream_replication import (
    LitestreamReplicationPrimitive,
    litestream_replication,
)
from assessment_engine.infrastructure.primitives.may_impact_planner import MayImpactPlannerPrimitive, may_impact_planner
from assessment_engine.infrastructure.primitives.media_forge import MediaForgePrimitive, media_forge
from assessment_engine.infrastructure.primitives.multimodal_ux_oracle import MultimodalUXOraclePrimitive, multimodal_ux_oracle
from assessment_engine.infrastructure.primitives.network import NetworkEgressPrimitive, network_primitive
from assessment_engine.infrastructure.primitives.openmetrics_exporter import OpenMetricsExporterPrimitive, openmetrics_exporter
from assessment_engine.infrastructure.primitives.optimistic_ui import OptimisticUIPrimitive, optimistic_ui
from assessment_engine.infrastructure.primitives.passkeys_webauthn import PasskeysWebAuthnPrimitive, passkeys_webauthn
from assessment_engine.infrastructure.primitives.payments import PaymentsPrimitive, payments_primitive
from assessment_engine.infrastructure.primitives.pdf_document_assembler import (
    PDFDocumentAssemblerPrimitive,
    pdf_document_assembler,
)
from assessment_engine.infrastructure.primitives.print_stylesheet import PrintStylesheetPrimitive, print_stylesheet
from assessment_engine.infrastructure.primitives.pwa_generator import PWAGeneratorPrimitive, pwa_generator
from assessment_engine.infrastructure.primitives.rate_limiter import RateLimiterPrimitive, rate_limiter
from assessment_engine.infrastructure.primitives.rebac_engine import RebacEngine, Subject, Resource, rebac_kernel
from assessment_engine.infrastructure.primitives.realtime_sse import RealtimeSSEBus, realtime_sse
from assessment_engine.infrastructure.primitives.repomap import RepoMapPrimitive, repomap
from assessment_engine.infrastructure.primitives.saliency_oracle import SaliencyOraclePrimitive, saliency_oracle
from assessment_engine.infrastructure.primitives.scalar_docs import ScalarDocsPrimitive, scalar_docs
from assessment_engine.infrastructure.primitives.schema_engine import SchemaEngine, EntitySchema, FieldDefinition, schema_engine
from assessment_engine.infrastructure.primitives.schema_migrator import SchemaMigratorPrimitive, schema_migrator
from assessment_engine.infrastructure.primitives.schema_org_injector import SchemaOrgInjectorPrimitive, schema_org_injector
from assessment_engine.infrastructure.primitives.secret_leak_sentinel import SecretLeakSentinelPrimitive, secret_leak_sentinel
from assessment_engine.infrastructure.primitives.security_gate import SecurityGatePrimitive, security_gate
from assessment_engine.infrastructure.primitives.sitemap_generator import SitemapGeneratorPrimitive, sitemap_generator
from assessment_engine.infrastructure.primitives.skeleton_shimmer import SkeletonShimmerPrimitive, skeleton_shimmer
from assessment_engine.infrastructure.primitives.slow_query_sentinel import SlowQuerySentinelPrimitive, slow_query_sentinel
from assessment_engine.infrastructure.primitives.social_card_generator import SocialCardGeneratorPrimitive, social_card_generator
from assessment_engine.infrastructure.primitives.speculative_preloader import SpeculativePreloaderPrimitive, speculative_preloader
from assessment_engine.infrastructure.primitives.sqlite_maintenance import SQLiteMaintenancePrimitive, sqlite_maintenance
from assessment_engine.infrastructure.primitives.sqlite_online_backup import SQLiteOnlineBackupPrimitive, sqlite_online_backup
from assessment_engine.infrastructure.primitives.superpowers import SuperpowersProbePrimitive, superpowers_probe
from assessment_engine.infrastructure.primitives.telemetry_beacon import TelemetryBeaconPrimitive, telemetry_beacon
from assessment_engine.infrastructure.primitives.thompson_router import ThompsonRouterPrimitive, thompson_router
from assessment_engine.infrastructure.primitives.trusted_host_guard import TrustedHostGuardPrimitive, trusted_host_guard
from assessment_engine.infrastructure.primitives.upload_streaming_guard import (
    UploadStreamingGuardPrimitive,
    upload_streaming_guard,
)
from assessment_engine.infrastructure.primitives.web_push_vapid import WebPushVAPIDPrimitive, web_push_vapid
from assessment_engine.infrastructure.primitives.web_vitals_gate import WebVitalsGatePrimitive, web_vitals_gate
from assessment_engine.infrastructure.primitives.workflow import DurableWorkflowPrimitive, workflow_primitive
from assessment_engine.infrastructure.primitives.zero_cookie_analytics import (
    ZeroCookieAnalyticsPrimitive,
    zero_cookie_analytics,
)
from assessment_engine.infrastructure.primitives.zero_fouc_theme import ZeroFOUCThemePrimitive, zero_fouc_theme

PRIMITIVES_REGISTRY = {
    "db": db_primitive,
    "auth": auth_primitive,
    "payments": payments_primitive,
    "booking_slots": booking_slots,
    "pricing_rules": pricing_rules,
    "inventory_allocation": inventory_allocation,
    "spatial_geo": spatial_geo,
    "communications_bus": communications_bus,
    "net": network_primitive,
    "blob": blob_primitive,
    "workflow": workflow_primitive,
    "content_pruner": content_pruner,
    "context_condenser": context_condenser,
    "dom_serializer": dom_accessibility_serializer,
    "cognitive": cognitive_ingest,
    "design_system": design_system_synthesizer,
    "realtime_sse": realtime_sse,
    "pwa": pwa_generator,
    "fts5_search": fts5_search,
    "legal": legal_engine,
    "pdf": pdf_document_assembler,
    "geo": geo_engine,
    "sqlite_maintenance": sqlite_maintenance,
    "sqlite_backup": sqlite_online_backup,
    "slow_query": slow_query_sentinel,
    "brotli": brotli_compression,
    "schema_migrator": schema_migrator,
    "micro_cache": in_memory_micro_cache,
    "config_validator": config_validator,
    "rate_limiter": rate_limiter,
    "telemetry": telemetry_beacon,
    "honeypot": honeypot_antispam,
    "audit_trail": audit_trail,
    "upload_guard": upload_streaming_guard,
    "html_sanitizer": html_sanitizer,
    "trusted_host": trusted_host_guard,
    "csrf": csrf_hmac_guard,
    "schema_org": schema_org_injector,
    "social_cards": social_card_generator,
    "sitemap": sitemap_generator,
    "zero_fouc": zero_fouc_theme,
    "intl": intl_formatter,
    "optimistic_ui": optimistic_ui,
    "speculative_preloader": speculative_preloader,
    "zero_cookie_analytics": zero_cookie_analytics,
    "repomap": repomap,
    "accessibility_oracle": accessibility_oracle,
    "web_vitals": web_vitals_gate,
    "dead_link_sentinel": dead_link_sentinel,
    "distroless": distroless_builder,
    "ci_cd": ci_cd_generator,
    "secret_sentinel": secret_leak_sentinel,
    "ast_rewriter": ast_rewriter,
    "may_impact_planner": may_impact_planner,
    "code_hygiene": code_hygiene,
    "litestream": litestream_replication,
    "email_oracle": email_oracle,
    "passkeys": passkeys_webauthn,
    "scalar_docs": scalar_docs,
    "async_queue": async_task_queue,
    "geoip": geoip_resolver,
    "compose_orchestrator": compose_orchestrator,
    "git_worktree": git_worktree_runner,
    "data_erasure": data_erasure_cascade,
    "web_push": web_push_vapid,
    "canonical_urls": canonical_urls,
    "skeleton_shimmer": skeleton_shimmer,
    "exponential_backoff": exponential_backoff_jitter,
    "dlq": dead_letter_queue,
    "openmetrics": openmetrics_exporter,
    "dependency_auditor": dependency_vulnerability_auditor,
    "entrypoint_orchestrator": entrypoint_orchestrator,
    "agentless": agentless_fixer,
    "mutation_probe": mutation_probe,
    "architect_editor": architect_editor,
    "security_gate": security_gate,
    "admin_security_guard": admin_security_guard,
    "media_forge": media_forge,
    "superpowers": superpowers_probe,
    "execution_guard": execution_guard,
}

from assessment_engine.infrastructure.primitives.db import db_engine
from assessment_engine.infrastructure.primitives.security import security_engine
from assessment_engine.infrastructure.primitives.booking import booking_engine
from assessment_engine.infrastructure.primitives.inventory import inventory_engine
from assessment_engine.infrastructure.primitives.realtime import realtime_engine
from assessment_engine.infrastructure.primitives.comms import comms_engine
from assessment_engine.infrastructure.primitives.spatial import spatial_engine
from assessment_engine.infrastructure.primitives.documents import document_engine, legal_suite
from assessment_engine.infrastructure.primitives.media import media_engine, image_pipeline
from assessment_engine.infrastructure.primitives.growth import growth_engine, geo_engine_suite
from assessment_engine.infrastructure.primitives.devops import devops_engine, vulnerability_auditor
from assessment_engine.infrastructure.primitives.telemetry import telemetry_engine, health_suite

CANONICAL_14_SYSTEMS = {
    "1_database": db_engine,
    "2_identity_rbac": auth_primitive,
    "3_security_defense": security_engine,
    "4_commerce_payments": payments_primitive,
    "5_scheduling_booking": booking_engine,
    "6_capacity_inventory": inventory_engine,
    "7_realtime_events": realtime_engine,
    "8_communications_bus": comms_engine,
    "9_spatial_geolocation": spatial_engine,
    "10_documents_legaltech": document_engine,
    "11_media_assets": media_engine,
    "12_growth_seo_pwa": growth_engine,
    "13_devops_containers": devops_engine,
    "14_telemetry_sre": telemetry_engine,
}
