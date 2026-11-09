"""Applies Phase 2 definitive sanitization to engine_config/locales.json.

Remediates:
1. default_primary_workloads: Purges plant dispatch telemetry.
2. tower_p90_triggers.T5: Purges fieldbus and PLC lockout.
3. ch3_scorecard_by_tower.T6: Replaces unvaulted shared credentials accusation with balanced zero trust text.
4. ch4_sec1_domain_context.SECURITY_GOVERNANCE: Purges storage array corruption from security domain.
5. maturity_scale_legend: Synchronizes legend to canonical CMMI scale intervals.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = ROOT / "engine_config" / "locales.json"


def sanitize() -> None:
    data = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))

    workloads_en = "mission-critical customer-facing workloads, real-time transaction pipelines, and core enterprise digital services"
    workloads_es = "cargas de misión crítica de producción, procesamiento transaccional en tiempo real y servicios digitales corporativos"

    p90_trigger_t5_en = "systemic active-active multi-region partition and automated failover orchestration collapse"
    p90_trigger_t5_es = "partición sistémica multirregional activo-activo y caída de la orquestación de conmutación automatizada"

    scorecard_t6_en = (
        "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), cybersecurity governance operates under structured operational controls across {client_name}. "
        "While perimeter and telemetry defenses demonstrate verified maturity ({strongest_pillar_name}, {strongest_pillar_score}/5.0), "
        "continuous privileged access governance and secrets automation ({weakest_pillar_name}, {weakest_pillar_score}/5.0) remain critical priorities to sustain regulatory compliance."
    )
    scorecard_t6_es = (
        "Con una madurez evaluada de {score_val} sobre 5.0 ({maturity_tier_label}), la ciberseguridad opera bajo controles estructurados en {client_name}. "
        "Mientras las defensas perimetrales y de telemetría muestran solidez verificada ({strongest_pillar_name}, {strongest_pillar_score}/5.0), "
        "la consolidación de accesos privilegiados y la rotación automatizada de secretos ({weakest_pillar_name}, {weakest_pillar_score}/5.0) constituyen prioridades clave para mantener el cumplimiento regulatorio."
    )

    sec_context_en = (
        "Within {tower_name}, a critical security compromise or privileged identity lockout disrupts core authentication and transactional pipelines, "
        "forcing operational suspension to verify authorization integrity at an estimated rate of {hourly_rate_est}."
    )
    sec_context_es = (
        "En {tower_name}, un compromiso de seguridad crítico o bloqueo de identidades privilegiadas interrumpe los flujos de autenticación y transacción, "
        "forzando la suspensión operativa para verificar la integridad a un coste estimado de {hourly_rate_est}."
    )

    legend_en = "CMMI Scale: Level 1 - Initial (1.00-1.59) | Level 2 - Managed (1.60-2.59) | Level 3 - Defined (2.60-3.59) | Level 4 - Quantitatively Managed (3.60-4.59) | Level 5 - Optimized (4.60-5.00)"
    legend_es = "Escala CMMI: Nivel 1 - Inicial (1,00-1,59) | Nivel 2 - Gestionado (1,60-2,59) | Nivel 3 - Definido (2,60-3,59) | Nivel 4 - Medido Cuantitativamente (3,60-4,59) | Nivel 5 - Optimizado (4,60-5,00)"

    for lang, lang_data in data.items():
        is_es = (lang == "es")

        # 1. default_primary_workloads
        lang_data["default_primary_workloads"] = workloads_es if is_es else workloads_en

        # 2. maturity_scale_legend
        lang_data["maturity_scale_legend"] = legend_es if is_es else legend_en

        # 3. tower_p90_triggers
        if "tower_p90_triggers" in lang_data:
            lang_data["tower_p90_triggers"]["T5"] = p90_trigger_t5_es if is_es else p90_trigger_t5_en

        # 4. ch3_scorecard_by_tower.T6
        if "ch3_scorecard_by_tower" in lang_data:
            lang_data["ch3_scorecard_by_tower"]["T6"] = scorecard_t6_es if is_es else scorecard_t6_en

        # 5. ch4_sec1_domain_context.SECURITY_GOVERNANCE
        if "ch4_sec1_domain_context" in lang_data:
            lang_data["ch4_sec1_domain_context"]["SECURITY_GOVERNANCE"] = sec_context_es if is_es else sec_context_en

    # Universal string replacements across the entire catalog
    replacements = {
        "Disruption of Plant dispatch system and Dispatch Systems": "Disruption of Core Transactional Processing Platforms",
        "Disruption of plant dispatch": "Disruption of core transaction processing",
        "Halted physical plant dispatch": "Halted operational transaction processing",
        "Plant dispatch system terminals validate dispatch slips against the central ERP": "Core transactional terminals validate settlement records against central enterprise systems",
        "plant dispatch": "core transaction processing",
        "Plant dispatch": "Core transaction processing",
    }

    def walk_and_replace(obj: any) -> any:
        if isinstance(obj, dict):
            return {k: walk_and_replace(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [walk_and_replace(item) for item in obj]
        elif isinstance(obj, str):
            res = obj
            for old_s, new_s in replacements.items():
                res = res.replace(old_s, new_s)
            return res
        return obj

    data = walk_and_replace(data)
    LOCALES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Phase 2 Sanitization applied successfully across all languages in: {LOCALES_PATH}")


if __name__ == "__main__":
    sanitize()
