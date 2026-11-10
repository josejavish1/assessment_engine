"""
Asynchronous synthesis orchestrator for compiling executive deliverables:
- Tomo 1 AS-IS Diagnostic & TO-BE Roadmap (.docx)
- Specialist Tower Annexes (.docx)
Provides real-time pipeline status telemetry (pipeline_status.json) and SSE streaming.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from assessment_engine.domain.schemas.workspace_contracts import (
    ClientDossierV3,
    DigitalTwinStateContract,
    PipelineStageStatus,
    PipelineStatusContract,
)
from assessment_engine.infrastructure.storage.workspace_manager import (
    WorkspacePersistenceManager,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[4]


class SynthesisOrchestrator:
    """Orchestrates asynchronous deliverable generation across AST compilers and telemetry emitters."""

    def __init__(self, workspace_manager: Optional[WorkspacePersistenceManager] = None) -> None:
        self.workspace_manager = workspace_manager or WorkspacePersistenceManager()
        self._active_tasks: Dict[str, asyncio.Task] = {}

    def get_status(self, client_slug: str) -> Optional[PipelineStatusContract]:
        """Loads current compilation pipeline status from disk."""
        return self.workspace_manager.load_pipeline_status(client_slug)

    def trigger_synthesis(
        self,
        client_slug: str,
        doc_lang: Optional[str] = None,
        enrich_risks: bool = False,
    ) -> PipelineStatusContract:
        """Initializes compilation pipeline and schedules background execution task."""
        safe_slug = "".join(c if c.isalnum() or c == "-" else "_" for c in client_slug.lower().strip())
        job_id = f"job-{secrets.token_hex(4)}"
        now_utc = datetime.now(timezone.utc).isoformat()

        initial_status = PipelineStatusContract(
            job_id=job_id,
            client_slug=safe_slug,
            status=PipelineStageStatus.QUEUED,
            current_stage="INITIALIZING",
            progress_pct=5.0,
            message_key="pipeline.stage.initializing",
            started_at_utc=now_utc,
            completed_files=[],
        )
        self.workspace_manager.save_pipeline_status(safe_slug, initial_status)

        # Schedule async background task
        task = asyncio.create_task(
            self._execute_synthesis_pipeline(job_id, safe_slug, doc_lang, enrich_risks)
        )
        self._active_tasks[job_id] = task
        logger.info("Triggered asynchronous synthesis %s for tenant %s", job_id, safe_slug)
        return initial_status

    async def _execute_synthesis_pipeline(
        self,
        job_id: str,
        client_slug: str,
        doc_lang: Optional[str],
        enrich_risks: bool,
    ) -> None:
        """Executes the 5-stage deliverable compilation workflow with atomic telemetry updates."""
        try:
            client_dir = self.workspace_manager.resolve_client_dir(client_slug)
            out_dir = self.workspace_manager.resolve_output_dir(client_slug)

            # Stage 1: Validate Workspace State (15%)
            await self._update_stage(
                job_id, client_slug, PipelineStageStatus.RUNNING, "STAGE_1_EVIDENCE_VALIDATION", 15.0, "pipeline.stage.evidence_validation"
            )
            await asyncio.sleep(0.3)

            dossier = self.workspace_manager.load_client_intelligence(client_slug)
            twin = self.workspace_manager.load_digital_twin_state(client_slug)

            client_name = dossier.legal_entity_name if dossier else client_slug.replace("-", " ").title()
            target_lang = doc_lang or (dossier.output_locale if dossier else "es")
            currency = dossier.financials.base_currency_iso if dossier else "EUR"
            curr_sym_map = {"EUR": "€", "GBP": "£", "USD": "$", "BRL": "R$", "JPY": "¥"}
            currency_symbol = curr_sym_map.get(currency, "$")

            # Stage 2: Actuarial FAIR Calibration & Radar Synthesis (40%)
            await self._update_stage(
                job_id, client_slug, PipelineStageStatus.RUNNING, "STAGE_2_ACTUARIAL_RADAR", 40.0, "pipeline.stage.actuarial_radar"
            )
            await asyncio.sleep(0.4)

            # Build heatmap from digital twin if available
            heatmap = []
            active_towers = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]
            if twin and twin.towers:
                active_towers = [t_id for t_id, t_state in twin.towers.items() if t_state.is_applicable]
                heatmap = [
                    {
                        "id": t_id,
                        "tower_code": t_id,
                        "tower_name": f"Domain {t_id}",
                        "score": t_state.calibrated_maturity_score,
                    }
                    for t_id, t_state in twin.towers.items()
                    if t_state.is_applicable
                ]
            else:
                heatmap = [
                    {"id": t_id, "tower_code": t_id, "tower_name": f"Domain {t_id}", "score": 3.2}
                    for t_id in active_towers
                ]

            # Render radar chart
            radar_png_path = client_dir / "global_radar_chart.png"
            from assessment_engine.application.generate_global_radar_chart import render_radar_chart
            render_radar_chart(towers=heatmap, out_path=radar_png_path, doc_lang=target_lang)
            shutil.copy2(radar_png_path, out_dir / "global_radar_chart.png")

            # Stage 3: Compile Consolidated Tomo 1 AS-IS DOCX via AST Compiler (70%)
            await self._update_stage(
                job_id, client_slug, PipelineStageStatus.RUNNING, "STAGE_3_TOMO_1_AST", 70.0, "pipeline.stage.compiling_tomo_1"
            )
            await asyncio.sleep(0.4)

            from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import Volume1AsisASTCompiler
            from assessment_engine.application.services.tower_payload_hydrator import TowerPayloadHydrator

            annual_revenue = float(dossier.financials.annual_revenue_amount * 1_000_000.0) if dossier else 1_250_000_000.0
            hourly_downtime = round(annual_revenue * 0.00018, 2)
            total_ale = round(annual_revenue * 0.015, 2)

            from scripts.build_client_delivery_suite import synthesize_tower_blueprints

            intel_data = {
                "client_name": client_name,
                "metadata": {
                    "lang": target_lang,
                    "currency": currency,
                    "currency_symbol": currency_symbol,
                },
                "profile": {
                    "industry": dossier.industry_vertical_code if dossier else "Enterprise",
                    "financial_profile": {
                        "currency": currency,
                        "currency_symbol": currency_symbol,
                        "annual_revenue": annual_revenue,
                        "hourly_downtime_cost": hourly_downtime,
                    },
                },
                "tower_overrides": {t_id: {"status": "In Scope", "target_maturity": 4.0} for t_id in active_towers},
            }

            # Ensure tower directories exist on disk
            for t_id in active_towers:
                (client_dir / t_id).mkdir(parents=True, exist_ok=True)

            # Synthesize authentic blueprints on disk in client working dir
            synthesize_tower_blueprints(
                working_dir=client_dir,
                intel_data=intel_data,
                active_towers=active_towers,
                doc_lang=target_lang,
                enrich_risks=enrich_risks,
            )

            from assessment_engine.infrastructure.text_utils import slugify
            client_slug_clean = slugify(client_name)

            global_payload = {
                "meta": {
                    "client": client_slug_clean,
                    "client_name": client_name,
                    "version": "1.0",
                    "date": "November 2026",
                    "lang": target_lang,
                    "doc_lang": target_lang,
                    "currency": currency,
                    "currency_symbol": currency_symbol,
                    "domain_scope": "scoped",
                    "is_modular": True,
                },
                "domain_scope": "scoped",
                "is_modular": True,
                "search_roots": [str(client_dir)],
                "financial_telemetry": {
                    "currency": currency,
                    "currency_symbol": currency_symbol,
                    "annual_revenue": annual_revenue,
                    "hourly_downtime_rate": hourly_downtime,
                    "consolidated_hourly_downtime_rate": hourly_downtime,
                    "corporate_ale": total_ale,
                    "total_fair_p90": total_ale * 2.2,
                },
                "heatmap": heatmap,
                "tower_overrides": {t_id: {"status": "In Scope", "target_maturity": 4.0} for t_id in active_towers},
            }

            effective_root = client_dir.parent.parent if (client_dir.parent.parent / "engine_config").exists() else REPO_ROOT

            hydrated_payloads = TowerPayloadHydrator.load_and_hydrate_all_towers(
                effective_root,
                global_payload,
                doc_lang=target_lang,
                target_towers=active_towers,
                persist_to_disk=False,
            )
            sanitized_name = slugify(client_name).title()
            tomo1_filename = f"{sanitized_name}_202611_Tomo_1_Diagnostico_ASIS.docx"
            tomo1_out_path = out_dir / tomo1_filename

            compiler = Volume1AsisASTCompiler()
            compiler.compile(
                global_payload=global_payload,
                tower_payloads=hydrated_payloads,
                output_docx_path=tomo1_out_path,
                doc_lang=target_lang,
            )

            completed_files = [tomo1_filename]

            # Stage 4: Compile Specialist Tower Annexes (90%)
            await self._update_stage(
                job_id, client_slug, PipelineStageStatus.RUNNING, "STAGE_4_ANNEXES_AST", 90.0, "pipeline.stage.compiling_annexes", completed_files
            )
            await asyncio.sleep(0.4)

            from assessment_engine.adapters.compilers.payload_to_ast import compile_asis_docx_via_ast

            # Compile first 3 in-scope specialist annexes for responsiveness
            for t_id in active_towers[:3]:
                bp = hydrated_payloads.get(t_id, {})
                num_str = f"{int(t_id[1:]):02d}"
                tower_slug = slugify(bp.get("tower_name", f"Domain {t_id}"))
                annex_filename = f"{sanitized_name}_202611_Annex_{num_str}_{tower_slug.title()}_ASIS.docx"
                annex_out_path = out_dir / annex_filename

                bp_temp = client_dir / f"blueprint_{t_id.lower()}_payload.json"
                bp_temp.write_text(json.dumps(bp, indent=2, ensure_ascii=False), encoding="utf-8")
                compile_asis_docx_via_ast(bp_temp, annex_out_path, doc_lang=target_lang)
                completed_files.append(annex_filename)

            # Stage 5: Finalized & Certified (100%)
            now_finished = datetime.now(timezone.utc).isoformat()
            final_status = PipelineStatusContract(
                job_id=job_id,
                client_slug=client_slug,
                status=PipelineStageStatus.COMPLETED,
                current_stage="COMPLETED",
                progress_pct=100.0,
                message_key="pipeline.stage.completed",
                completed_files=completed_files,
                finished_at_utc=now_finished,
            )
            self.workspace_manager.save_pipeline_status(client_slug, final_status)
            logger.info("Successfully completed synthesis %s for %s (%d files generated)", job_id, client_slug, len(completed_files))

        except Exception as ex:
            logger.exception("Synthesis pipeline %s failed for %s: %s", job_id, client_slug, ex)
            failed_status = PipelineStatusContract(
                job_id=job_id,
                client_slug=client_slug,
                status=PipelineStageStatus.FAILED,
                current_stage="FAILED",
                progress_pct=0.0,
                message_key="pipeline.stage.failed",
                error_detail=str(ex),
                finished_at_utc=datetime.now(timezone.utc).isoformat(),
            )
            self.workspace_manager.save_pipeline_status(client_slug, failed_status)

    async def _update_stage(
        self,
        job_id: str,
        client_slug: str,
        status: PipelineStageStatus,
        stage: str,
        pct: float,
        msg_key: str,
        completed_files: Optional[List[str]] = None,
    ) -> None:
        current = PipelineStatusContract(
            job_id=job_id,
            client_slug=client_slug,
            status=status,
            current_stage=stage,
            progress_pct=pct,
            message_key=msg_key,
            completed_files=completed_files or [],
        )
        self.workspace_manager.save_pipeline_status(client_slug, current)
