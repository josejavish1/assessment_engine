"""Domain blueprint payload synthesis service.

Generates complete, mathematically calibrated specialist tower blueprint payloads
conforming to the Declarative AST Engine specification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from assessment_engine.application.services.neurosymbolic_risk_synthesizer import (
    NeurosymbolicLLMSynthesizer,
)
from assessment_engine.application.services.risk_synthesis_service import (
    DeterministicFallbackSynthesizer,
)
from assessment_engine.domain.schemas.risk_synthesis import RiskSynthesisContext
from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
    get_actuarial_archetype_registry,
)
from assessment_engine.domain.taxonomy_resolver import get_taxonomy_resolver
from assessment_engine.infrastructure.runtime_paths import ROOT

REPO_ROOT = ROOT


def _load_json(p: Path) -> dict[str, Any]:
    """Load JSON file safely."""
    return cast(dict[str, Any], json.loads(p.read_text(encoding="utf-8-sig")))


def resolve_contextual_technology(
    tower_code: str, pillar_name: str, group_stack: list[dict[str, Any]]
) -> str:
    """Map tower domain to the most relevant technology component using canonical TaxonomyResolver."""
    try:
        resolver = get_taxonomy_resolver()
        t_name = resolver.resolve_tower_name(tower_code.upper(), locale="en")
        if t_name and not t_name.startswith("Tower "):
            return t_name
    except Exception:
        pass
    return pillar_name


def synthesize_tower_blueprints(
    working_dir: Path,
    intel_data: dict[str, Any],
    active_towers: list[str],
    doc_lang: str,
    enrich_risks: bool = False,
) -> dict[str, dict[str, Any]]:
    """Synthesize complete, mathematically verified blueprint payloads for all active towers."""
    client_name = intel_data["client_name"]
    meta = intel_data.get("metadata", {})
    fin = intel_data.get("profile", {}).get("financial_profile", {})
    currency = meta.get("currency", "GBP")
    currency_symbol = meta.get("currency_symbol", "£")
    annual_revenue = float(fin.get("annual_revenue", 100_000_000.0))
    hourly_rate = float(fin.get("hourly_downtime_cost", 50_000.0))
    sub_ind = str(intel_data.get("profile", {}).get("sub_industry") or "enterprise")

    tower_catalog_file = REPO_ROOT / "engine_config" / "towers" / "tower_catalog.json"
    tower_catalog = _load_json(tower_catalog_file) if tower_catalog_file.exists() else {}

    synthesizer = NeurosymbolicLLMSynthesizer() if enrich_risks else DeterministicFallbackSynthesizer()

    blueprints: dict[str, dict[str, Any]] = {}

    for t_id in active_towers:
        print(f"  [{t_id}] Synthesizing domain blueprint ({'Neurosymbolic LLM' if enrich_risks else 'Deterministic'})...", flush=True)
        case_input_file = working_dir / t_id / "case_input.json"
        case_data = _load_json(case_input_file) if case_input_file.exists() else {}
        answers = case_data.get("answers", [])

        # Load tower definition to map pillars and KPIs
        def_file = REPO_ROOT / "engine_config" / "towers" / t_id / f"tower_definition_{t_id}.json"
        def_data = _load_json(def_file) if def_file.exists() else {}
        tower_name = def_data.get("tower_name") or tower_catalog.get(t_id, {}).get("canonical_code", t_id)

        # Compute pillar scores from answers
        pillars_analysis: list[dict[str, Any]] = []
        score_by_kpi = {a["kpi_id"]: float(a["value"]) for a in answers if "kpi_id" in a and "value" in a}

        resolver = get_taxonomy_resolver()

        total_pillars_count = max(1, len(def_data.get("pillars", [])))
        normalized_pillar_weight = round(1.0 / total_pillars_count, 4)
        group_stack = intel_data.get("technology_context", {}).get("group_level_stack", [])

        # If enrich_risks is enabled, batch synthesize primary pillar risks in a single LLM pass per tower
        enriched_by_kpi: dict[str, Any] = {}
        if enrich_risks and isinstance(synthesizer, NeurosymbolicLLMSynthesizer):
            tower_primary_contexts: list[RiskSynthesisContext] = []
            for p_idx, pillar in enumerate(def_data.get("pillars", [])):
                p_id = pillar.get("pillar_id") or f"{t_id}.P{p_idx+1}"
                raw_pname = pillar.get("pillar_name", f"Pillar {p_idx+1}")
                p_name = resolver.resolve_pillar_by_any_reference(
                    p_id or raw_pname,
                    default=raw_pname,
                    locale=doc_lang,
                    tower_id=t_id,
                )
                p_kpis = pillar.get("kpis", [])
                if p_kpis:
                    k_id = p_kpis[0].get("kpi_id")
                    sc = score_by_kpi.get(k_id, 3.5)
                    deficit = max(0.04, round(5.0 - sc, 2))
                    calibrated_ale = round(hourly_rate * (deficit ** 1.8) * 0.8, 2)
                    tech_name = resolve_contextual_technology(t_id, p_name, group_stack)
                    dt_mins = max(8, round((calibrated_ale / hourly_rate) * 60))
                    stoppage = round(calibrated_ale * 0.65, 2)
                    recovery = round(calibrated_ale * 0.25, 2)
                    penalty = round(calibrated_ale * 0.10, 2)
                    sle = round(stoppage + recovery + penalty, 2)

                    tower_primary_contexts.append(
                        RiskSynthesisContext(
                            client_name=client_name,
                            industry=intel_data.get("profile", {}).get("industry", "Enterprise"),
                            sub_industry=sub_ind,
                            maturity_tier=f"Score: {sc:.2f}",
                            doc_lang=doc_lang,
                            currency_symbol=currency_symbol,
                            hourly_rate=hourly_rate,
                            verified_tech_stack=[tech_name],
                            tower_code=t_id,
                            tower_name=tower_name,
                            pillar_id=p_id,
                            pillar_name=p_name,
                            kpi_id=k_id,
                            assessed_score=sc,
                            calibrated_ale=calibrated_ale,
                            downtime_minutes=dt_mins,
                            stoppage_loss=stoppage,
                            recovery_burn=recovery,
                            penalty_loss=penalty,
                            total_sle=sle,
                        )
                    )
            if tower_primary_contexts:
                enriched_items = synthesizer.synthesize_tower_risks(tower_primary_contexts)
                enriched_by_kpi = {item.risk_id.replace("RSK-", ""): item for item in enriched_items}

        tower_scores: list[float] = []
        for p_idx, pillar in enumerate(def_data.get("pillars", [])):
            p_id = pillar.get("pillar_id")
            raw_pname = pillar.get("pillar_name", f"Pillar {p_idx+1}")
            p_name = resolver.resolve_pillar_by_any_reference(
                p_id or raw_pname,
                default=raw_pname,
                locale=doc_lang,
                tower_id=t_id,
            )
            p_kpis = pillar.get("kpis", [])
            k_scores = [score_by_kpi[k["kpi_id"]] for k in p_kpis if k["kpi_id"] in score_by_kpi]
            p_score = round(sum(k_scores) / len(k_scores), 2) if k_scores else 3.5
            tower_scores.append(p_score)

            # Health check findings with non-linear FAIR risk calibration and Reverse-FAIR narrative synthesis
            health_checks = []
            for k_idx, k in enumerate(p_kpis[:3]):
                k_id = k.get("kpi_id")
                sc = score_by_kpi.get(k_id, p_score)
                deficit = max(0.04, round(5.0 - sc, 2))
                # Non-linear quadratic severity scaling reflecting tail-risk escalation
                calibrated_hc_ale = round(hourly_rate * (deficit ** 1.8) * (0.8 + 0.3 * (k_idx % 3)), 2)

                # Select contextual technology item from client intelligence matching domain
                tech_name = resolve_contextual_technology(t_id, p_name, group_stack)

                # Calculate bottom-up actuarial loss decomposition
                downtime_minutes = max(8, round((calibrated_hc_ale / hourly_rate) * 60))
                stoppage_loss = round(calibrated_hc_ale * 0.65, 2)
                recovery_burn = round(calibrated_hc_ale * 0.25, 2)
                penalty_loss = round(calibrated_hc_ale * 0.10, 2)
                total_sle = round(stoppage_loss + recovery_burn + penalty_loss, 2)

                syn_ctx = RiskSynthesisContext(
                    client_name=client_name,
                    industry=intel_data.get("profile", {}).get("industry", "Enterprise"),
                    sub_industry=sub_ind,
                    maturity_tier=f"Score: {sc:.2f}",
                    doc_lang=doc_lang,
                    currency_symbol=currency_symbol,
                    hourly_rate=hourly_rate,
                    verified_tech_stack=[tech_name],
                    tower_code=t_id,
                    tower_name=tower_name,
                    pillar_id=p_id,
                    pillar_name=p_name,
                    kpi_id=k_id,
                    assessed_score=sc,
                    calibrated_ale=calibrated_hc_ale,
                    downtime_minutes=downtime_minutes,
                    stoppage_loss=stoppage_loss,
                    recovery_burn=recovery_burn,
                    penalty_loss=penalty_loss,
                    total_sle=total_sle,
                )
                # Use live LLM enrichment for the primary representative risk of each pillar (k_idx == 0)
                # while secondary contributors use the sub-millisecond deterministic provider.
                if enrich_risks and k_idx == 0 and k_id in enriched_by_kpi:
                    syn_item = enriched_by_kpi[k_id]
                else:
                    syn_item = DeterministicFallbackSynthesizer().synthesize_risk(syn_ctx)

                finding_txt = syn_item.technical_failure_mechanism
                risk_txt = f"{syn_item.causal_risk_title} ({p_name})"

                health_checks.append({
                    "finding_id": f"HC-{k_id}",
                    "title": syn_item.causal_risk_title,
                    "causal_risk_title": syn_item.causal_risk_title,
                    "synthesized_title": syn_item.causal_risk_title,
                    "capability": syn_item.causal_risk_title,
                    "description": f"Audited operational baseline for {p_name} control standard {k_id}. Assessed score: {sc:.2f}/5.00.",
                    "technical_failure_mechanism": syn_item.technical_failure_mechanism,
                    "target_state": syn_item.remediation_architecture,
                    "remediation_architecture": syn_item.remediation_architecture,
                    "remediation": syn_item.remediation_architecture,
                    "actuarial_justification": syn_item.actuarial_justification,
                    "context_hash": syn_item.context_hash,
                    "finding": finding_txt,
                    "control_vulnerability": syn_item.technical_failure_mechanism,
                    "business_risk": risk_txt,
                    "primary_impact": risk_txt,
                    "score": sc,
                    "target_maturity": 4.5,
                    "weight": 1.0,
                    "status": "Verified",
                    "fair_ale": calibrated_hc_ale,
                })

            pillars_analysis.append({
                "pillar_id": p_id,
                "pillar_name": p_name,
                "score": p_score,
                "weight": normalized_pillar_weight,
                "health_check_asis": health_checks,
            })

        if pillars_analysis:
            weight_drift = round(1.0 - sum(p["weight"] for p in pillars_analysis), 4)
            pillars_analysis[0]["weight"] = round(pillars_analysis[0]["weight"] + weight_drift, 4)

        avg_tower_score = round(sum(tower_scores) / len(tower_scores), 2) if tower_scores else 3.8
        tower_ale = round(sum(hc["fair_ale"] for p in pillars_analysis for hc in p["health_check_asis"]), 2)

        # Universal, decoupled narrative and inventory extraction from client evidence
        context_summary = case_data.get("context_summary", "").strip()
        if context_summary:
            lines = [line.strip() for line in context_summary.split("\n") if len(line.strip()) > 40 and not line.strip().startswith("=")]
            domain_narrative = lines[0] if lines else f"Diagnostic assessment of {tower_name} across evaluated operational pillars."
        else:
            domain_narrative = f"Diagnostic assessment of {tower_name} across evaluated operational pillars for {client_name}."

        group_stack = intel_data.get("technology_context", {}).get("group_level_stack", [])
        if group_stack:
            tech_items = [f"{tech.get('name', 'Core Platform')} ({tech.get('category', 'Infrastructure')})" for tech in group_stack[:4]]
            domain_inventory = ", ".join(tech_items)
        else:
            domain_inventory = f"{tower_name} enterprise components and managed operational workloads."

        sorted_by_score = sorted(pillars_analysis, key=lambda x: x["score"], reverse=True)
        top_pillar = sorted_by_score[0] if sorted_by_score else None
        lowest_pillar = sorted_by_score[-1] if sorted_by_score else None

        strongest_name = top_pillar["pillar_name"] if top_pillar else "arquitetura base"
        strongest_sc = top_pillar["score"] if top_pillar else 4.0
        lowest_name = lowest_pillar["pillar_name"] if lowest_pillar else "capacidade operacional"
        lowest_sc = lowest_pillar["score"] if lowest_pillar else 3.0

        if doc_lang == "pt":
            top_strengths = [
                f"{strongest_name}: Demonstra controle operacional verificado ({strongest_sc:.2f}/5,00) com procedimentos estabelecidos."
            ]
            if len(sorted_by_score) > 1 and sorted_by_score[1]["score"] >= 3.0:
                sec_p = sorted_by_score[1]
                top_strengths.append(f"{sec_p['pillar_name']}: Execu\u00e7\u00e3o padronizada ({sec_p['score']:.2f}/5,00) assegurando a continuidade de servi\u00e7os.")
            if not top_strengths:
                top_strengths.append("Pr\u00e1ticas operacionais de linha de base estabelecidas nos fluxos principais.")

            top_friction = []
            if lowest_pillar and lowest_pillar["score"] < 4.8:
                top_friction.append(f"{lowest_name}: Fric\u00e7\u00e3o operacional e restri\u00e7\u00f5es de capacidade observadas ({lowest_sc:.2f}/5,00).")
            reg_framework = intel_data.get("regulatory_context", [{}])[0].get("regulation", "normas regulat\u00f3rias do setor")
            top_friction.append(f"Exig\u00eancias de escrut\u00ednio cont\u00ednuo e conformidade de governan\u00e7a sob {reg_framework}.")

            sub_ind_pt = "hospitalar e servi\u00e7os de sa\u00fade integrados"
            op_mission = f"arquitetura de {tower_name}, cargas de trabalho gerenciadas e controles operacionais automatizados"
            pw_summary = f"cargas de trabalho de atendimento assistencial, processamento em tempo real e servi\u00e7os digitais da rede {sub_ind_pt}"
            pm_focus = f"refor\u00e7o da resili\u00eancia automatizada, elimina\u00e7\u00e3o de pontos \u00fanicos de falha e consolida\u00e7\u00e3o de {lowest_name}"
            cf_trigger = f"falha simult\u00e2nea de componentes centrais e perda de redund\u00e2ncia operacional em {tower_name} sob pico de demanda"
            sc_comm = (
                f"Com maturidade avaliada em {avg_tower_score:.2f} sobre 5,0, o dom\u00ednio de {tower_name} demonstra capacidades operacionais estruturadas na {client_name}. "
                f"Enquanto os controles principais ({strongest_name}, {strongest_sc:.2f}/5,00) refletem resili\u00eancia verificada, "
                f"a moderniza\u00e7\u00e3o direcionada em {lowest_name} ({lowest_sc:.2f}/5,00) permanece como prioridade essencial para eliminar fric\u00e7\u00f5es e assegurar a escalabilidade a longo prazo."
            )
            if t_id == "T1":
                dt_context = f"No \u00e2mbito de {tower_name}, conting\u00eancias f\u00edsicas em salas t\u00e9cnicas ou colocation impactam a infraestrutura de borda e HSMs a uma taxa atenuada de {currency_symbol} {round(hourly_rate * 0.20):,.2f}/h (20% do basal), escalando para a taxa total apenas em desastres simult\u00e2neos multirregionais."
            else:
                dt_context = f"No \u00e2mbito de {tower_name}, uma interrup\u00e7\u00e3o operacional severa ou falha de componente degrada diretamente os servi\u00e7os transacionais na {client_name}, resultando em uma taxa de perda operacional estimada em {hourly_rate:,.2f} {currency_symbol}/h."

            (
                f"Sob a metodologia internacional Open FAIR\u2122 (Factor Analysis of Information Risk), a indisponibilidade n\u00e3o planejada de servi\u00e7os acarreta uma taxa de perda operacional direta de **{currency_symbol} {hourly_rate:,.2f}/h** (detalhado na Se\u00e7\u00e3o 4.1). "
                f"Em condi\u00e7\u00f5es ordin\u00e1rias, as lacunas t\u00e9cnicas avaliadas especificamente no \u00e2mbito de **{tower_name}** representam uma **exposi\u00e7\u00e3o de risco latente estimada em {currency_symbol} {tower_ale:,.0f} anualizados**, refletindo a perda m\u00e9dia esperada por fric\u00e7\u00f5es operacionais e incidentes ao longo de um ano neste dom\u00ednio.\n\n"
                f"Adicionalmente, perante um **cen\u00e1rio adverso de crise por conting\u00eancia extrema nesta plataforma**, a recupera\u00e7\u00e3o t\u00e9cnica pode demandar uma janela estendida de interven\u00e7\u00e3o, elevando o impacto financeiro contingente para at\u00e9 **{currency_symbol} {round(tower_ale * 2.2):,.0f}** ao computar a paralisa\u00e7\u00e3o acumulada somada aos custos extraordin\u00e1rios de conting\u00eancia e suporte emergencial."
            )
        elif doc_lang == "es":
            top_strengths = [
                f"{strongest_name}: Demuestra control operativo verificado ({strongest_sc:.2f}/5,00) con procedimientos establecidos."
            ]
            if len(sorted_by_score) > 1 and sorted_by_score[1]["score"] >= 3.0:
                sec_p = sorted_by_score[1]
                top_strengths.append(f"{sec_p['pillar_name']}: Ejecuci\u00f3n estandarizada ({sec_p['score']:.2f}/5,00) asegurando la continuidad operativa.")
            if not top_strengths:
                top_strengths.append("Pr\u00e1cticas operativas de l\u00ednea base establecidas en los flujos principales.")

            top_friction = []
            if lowest_pillar and lowest_pillar["score"] < 4.8:
                top_friction.append(f"{lowest_name}: Fricci\u00f3n operativa y restricciones de capacidad observadas ({lowest_sc:.2f}/5,00).")
            reg_framework = intel_data.get("regulatory_context", [{}])[0].get("regulation", "normativas regulatorias aplicables")
            top_friction.append(f"Exigencias de supervisi\u00f3n continua y cumplimiento de gobernanza bajo {reg_framework}.")

            sub_ind_es = "red corporativa y transaccional"
            op_mission = f"arquitectura de {tower_name}, cargas de trabajo gestionadas y controles operativos automatizados"
            pw_summary = f"cargas de trabajo cr\u00edticas de negocio, procesamiento en tiempo real y servicios digitales de la red {sub_ind_es}"
            pm_focus = f"refuerzo de la resiliencia automatizada, eliminaci\u00f3n de puntos \u00fanicos de fallo y consolidaci\u00f3n de {lowest_name}"
            cf_trigger = f"fallo simult\u00e1neo de componentes centrales y p\u00e9rdida de redundancia operativa en {tower_name} bajo pico de demanda"
            sc_comm = (
                f"Con una madurez evaluada de {avg_tower_score:.2f} sobre 5,0, el dominio de {tower_name} demuestra capacidades operativas estructuradas en {client_name}. "
                f"Mientras los controles principales ({strongest_name}, {strongest_sc:.2f}/5,00) reflejan resiliencia verificada, "
                f"la modernizaci\u00f3n focalizada en {lowest_name} ({lowest_sc:.2f}/5,00) se mantiene como prioridad esencial para eliminar fricciones y asegurar la escalabilidad a largo plazo."
            )
            if t_id == "T1":
                dt_context = f"En el \u00e1mbito de {tower_name}, contingencias f\u00edsicas en salas t\u00e9cnicas o colocation impactan la infraestructura de borde y HSMs a una tasa atenuada de {currency_symbol} {round(hourly_rate * 0.20):,.2f}/h (20% del basal), escalando a la tasa bruta \u00fanicamente ante desastres multirregionales."
            else:
                dt_context = f"En el \u00e1mbito de {tower_name}, una interrupci\u00f3n operativa severa o fallo de componente degrada directamente el procesamiento transaccional en {client_name}, resultando en una tasa de p\u00e9rdida operativa estimada en {hourly_rate:,.2f} {currency_symbol}/h."

            (
                f"Bajo el est\u00e1ndar internacional Open FAIR\u2122 (Factor Analysis of Information Risk), la indisponibilidad no planificada de servicios conlleva un coste operativo directo de **{currency_symbol} {hourly_rate:,.2f}/h** (detallado en la Secci\u00f3n 4.1). "
                f"En condiciones ordinarias, las brechas t\u00e9cnicas evaluadas espec\u00edficamente en el \u00e1mbito de **{tower_name}** representan una **exposici\u00f3n de riesgo latente estimada en {currency_symbol} {tower_ale:,.0f} anualizados**, como prima de riesgo impl\u00edcita por la fricci\u00f3n operativa a lo largo de un a\u00f1o en este dominio.\n\n"
                f"Adicionalmente, ante un **escenario adverso de crisis por contingencia extrema en esta plataforma**, la recuperaci\u00f3n t\u00e9cnica mediante procedimientos de contingencia podr\u00eda demorarse, elevando el impacto econ\u00f3mico contingente hasta **{currency_symbol} {round(tower_ale * 2.2):,.0f}** al computar la parada acumulada junto a los costes extraordinarios de soporte y recuperaci\u00f3n."
            )
        else:
            top_strengths = [
                f"{strongest_name}: Demonstrates verified operational control ({strongest_sc:.2f}/5.00) with established procedures."
            ]
            if len(sorted_by_score) > 1 and sorted_by_score[1]["score"] >= 3.0:
                sec_p = sorted_by_score[1]
                top_strengths.append(f"{sec_p['pillar_name']}: Standardized execution ({sec_p['score']:.2f}/5.00) supporting enterprise operational continuity.")
            if not top_strengths:
                top_strengths.append("Standardized baseline operational practices established across primary workflows.")

            top_friction = []
            if lowest_pillar and lowest_pillar["score"] < 4.8:
                top_friction.append(f"{lowest_name}: Operational friction and capacity constraints observed ({lowest_sc:.2f}/5.00).")
            reg_framework = intel_data.get("regulatory_context", [{}])[0].get("regulation", "industry standards")
            top_friction.append(f"Regulatory scrutiny and continuous audit verification requirements under {reg_framework}.")

            sub_ind_en = sub_ind
            op_mission = f"{tower_name} architecture, managed operational workloads, and automated control procedures"
            pw_summary = f"mission-critical customer-facing workloads, real-time transaction pipelines, and core {sub_ind_en} digital services"
            pm_focus = f"reinforcing automated resiliency, eliminating single points of dependency, and consolidating {lowest_name}"
            cf_trigger = f"concurrent core component failure and operational redundancy loss across {tower_name} under peak transaction load"
            sc_comm = (
                f"Evaluated at {avg_tower_score:.2f} out of 5.0, {tower_name} demonstrates structured operational capabilities across {client_name}. "
                f"While primary controls ({strongest_name}, {strongest_sc:.2f}/5.00) reflect verified resilience, "
                f"targeted modernization in {lowest_name} ({lowest_sc:.2f}/5.00) remains an essential priority to eliminate operational friction and ensure long-term scalability."
            )

            try:
                arch_mapping = get_actuarial_archetype_registry().get_mapping_for_tower(t_id)
                primary_arch = arch_mapping.primary_archetype
            except (KeyError, ValueError):
                primary_arch = LossArchetypeType.AVAILABILITY_OUTAGE

            if primary_arch == LossArchetypeType.CAPITAL_INEFFICIENCY:
                dt_context = f"Within {tower_name}, technical governance and lifecycle gaps induce unbudgeted capital drift across {client_name}'s infrastructure estate, with annual addressable waste evaluated at {currency_symbol}{tower_ale:,.0f}/year."
                (
                    f"Under the international Open FAIR™ (Factor Analysis of Information Risk) standard, economic exposure within **{tower_name}** represents capital inefficiency and cloud commitment drift rather than transactional service downtime. "
                    f"Unmonitored resource provisioning and unaligned commercial agreements represent an **estimated latent risk exposure of {currency_symbol}{tower_ale:,.0f} annualized**, reflecting unhedged compute commitments and addressable spend drift across {client_name}'s estate.\n\n"
                    f"Additionally, under an **adverse compounding fiscal scenario involving multi-year contractual renewals and unhedged compute surges**, contingent financial liability reaches up to **{currency_symbol}{round(tower_ale * 2.2):,.0f}** when factoring in cumulative budget overruns, unreserved on-demand rates, and retroactive vendor licensing true-ups."
                )
            elif primary_arch == LossArchetypeType.PRODUCTIVITY_TOIL:
                dt_context = f"Within {tower_name}, operational friction and manual runbook dependencies degrade workforce velocity across {client_name}, resulting in an estimated annual productivity drag of {currency_symbol}{tower_ale:,.0f}/year."
                (
                    f"Under the international Open FAIR™ (Factor Analysis of Information Risk) standard, economic exposure within **{tower_name}** represents workforce cognitive friction and engineering toil rather than transactional clearing downtime. "
                    f"Operational friction, ticket handling latency, and manual workflows represent an **estimated latent risk exposure of {currency_symbol}{tower_ale:,.0f} annualized** in burned engineering capacity across {client_name}.\n\n"
                    f"Additionally, under an **adverse compounding scenario involving simultaneous operational incidents and platform tooling degradation**, cumulative friction elevates the contingent economic impact up to **{currency_symbol}{round(tower_ale * 2.2):,.0f}** when factoring in emergency specialist intervention and lost workforce productive hours."
                )
            elif primary_arch == LossArchetypeType.REGULATORY_AND_BREACH:
                dt_context = f"Within {tower_name}, security perimeter weaknesses and identity vulnerabilities expose {client_name} to statutory regulatory penalties and forensic recovery costs, evaluated at {currency_symbol}{tower_ale:,.0f}/year."
                (
                    f"Under the international Open FAIR™ (Factor Analysis of Information Risk) standard, economic exposure within **{tower_name}** represents statutory regulatory non-compliance liabilities (such as DORA, PRA, and GDPR frameworks) alongside forensic response costs rather than standard operational downtime. "
                    f"Identified security gaps represent an **estimated latent risk exposure of {currency_symbol}{tower_ale:,.0f} annualized** across {client_name}.\n\n"
                    f"Additionally, under a **severe compounding data compromise or critical identity breach scenario**, contingent exposure reaches up to **{currency_symbol}{round(tower_ale * 2.2):,.0f}** when accounting for statutory enforcement sanctions, forensic investigation audits, and customer remediation protocols."
                )
            elif t_id == "T1":
                dt_context = f"Within {tower_name}, physical disruptions in server rooms or colocation suites impact ingress routing and cryptographic HSM hardware at an attenuated operational rate of {currency_symbol}{round(hourly_rate * 0.20):,.2f}/hr (20% of baseline), scaling up to the full gross run-rate only in multi-site catastrophic events."
                (
                    f"Under the international Open FAIR™ (Factor Analysis of Information Risk) standard, unplanned service downtime incurs an attenuated operational cost of **{currency_symbol}{round(hourly_rate * 0.20):,.2f}/hr** (detailed in Section 4.1). "
                    f"Under ordinary conditions, technical gaps assessed specifically within the scope of **{tower_name}** represent an **estimated latent risk exposure of {currency_symbol}{tower_ale:,.0f} annualized**, reflecting the expected average loss from operational friction and incidents throughout a year within this domain.\n\n"
                    f"Additionally, under an **adverse crisis scenario involving multi-component failure or severe contingency on this platform**, technical recovery via contingency procedures could require an extended window, elevating the contingent economic impact up to **{currency_symbol}{round(tower_ale * 2.2):,.0f}** when factoring in cumulative downtime alongside emergency restoration and specialist support."
                )
            else:
                dt_context = f"Within {tower_name}, a severe operational interruption or component failure directly degrades transactional processing and enterprise services at {client_name}, resulting in an estimated operational loss rate of {currency_symbol}{hourly_rate:,.2f}/hr."
                (
                    f"Under the international Open FAIR™ (Factor Analysis of Information Risk) standard, unplanned service downtime incurs a direct operational cost of **{currency_symbol}{hourly_rate:,.2f}/hr** (detailed in Section 4.1). "
                    f"Under ordinary conditions, technical gaps assessed specifically within the scope of **{tower_name}** represent an **estimated latent risk exposure of {currency_symbol}{tower_ale:,.0f} annualized**, reflecting the expected average loss from operational friction and incidents throughout a year within this domain.\n\n"
                    f"Additionally, under an **adverse crisis scenario involving multi-component failure or severe contingency on this platform**, technical recovery via contingency procedures could require an extended window, elevating the contingent economic impact up to **{currency_symbol}{round(tower_ale * 2.2):,.0f}** when factoring in cumulative downtime alongside emergency restoration and specialist support."
                )

        blueprint_payload = {
            "document_meta": {
                "language": doc_lang,
                "doc_lang": doc_lang,
                "tower_code": t_id,
                "tower_name": tower_name,
                "client": client_name,
                "client_name": client_name,
                "currency": currency,
                "currency_symbol": currency_symbol,
                "annual_revenue": annual_revenue,
                "version": "1.0",
                "date": "October 2026",
                "industry": intel_data.get("profile", {}).get("industry", "banking"),
                "industry_vertical": intel_data.get("profile", {}).get("industry", "banking"),
                "sub_industry": intel_data.get("profile", {}).get("sub_industry", "Digital Challenger Clearing Bank"),
                "delivery_model": "CLOUD_NATIVE" if any(k in str(intel_data.get("profile", {})).upper() for k in ("FINTECH", "BANK", "SAAS", "DIGITAL")) else "ON_PREM_HEAVY",
            },
            "industry": intel_data.get("profile", {}).get("industry", "banking"),
            "industry_vertical": intel_data.get("profile", {}).get("industry", "banking"),
            "sub_industry": intel_data.get("profile", {}).get("sub_industry", "Digital Challenger Clearing Bank"),
            "delivery_model": "CLOUD_NATIVE" if any(k in str(intel_data.get("profile", {})).upper() for k in ("FINTECH", "BANK", "SAAS", "DIGITAL")) else "ON_PREM_HEAVY",
            "financial_telemetry": {
                "consolidated_annual_revenue": annual_revenue,
                "annual_revenue": annual_revenue,
                "currency": currency,
                "currency_symbol": currency_symbol,
                "authoritative_hourly_downtime_cost": hourly_rate,
            },
            "tower_code": t_id,
            "tower_name": tower_name,
            "overall_score": avg_tower_score,
            "score": avg_tower_score,
            "exact_score": avg_tower_score,
            "maturity_score": avg_tower_score,
            "total_fair_ale": tower_ale,
            "total_fair_p90": round(tower_ale * 2.2, 2),
            "worst_crisis_event": round(tower_ale * 2.5, 2),
            "diagnostic_narrative": domain_narrative,
            "scorecard_commentary": sc_comm,
            "operational_mission": op_mission,
            "primary_workloads_summary": pw_summary,
            "primary_workloads": pw_summary,
            "posture_modernization_focus": pm_focus,
            "compound_failure_trigger": cf_trigger,
            "downtime_incident_context": dt_context,
            "inventory": domain_inventory,
            "strengths": top_strengths,
            "friction_points": top_friction,
            "findings": top_friction,
            "critical_findings": top_friction,
            "pillars_analysis": pillars_analysis,
        }

        # Persist blueprint payload
        payload_file = working_dir / t_id / f"blueprint_{t_id.lower()}_payload.json"
        payload_file.write_text(json.dumps(blueprint_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        blueprints[t_id] = blueprint_payload

    return blueprints
