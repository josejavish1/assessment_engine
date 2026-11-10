"""Remediate the 3 core flaws identified in the Argon 12-Enterprise Universality Audit."""

import json
from pathlib import Path

LOCALES_PATH = Path("engine_config/locales.json")
data = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))

# 1. Update ch4_lineage_col_rate across all 6 languages
LINEAGE_COL_TITLES = {
    "es": "Exposición Anualizada Estimada (ALE)",
    "en": "Estimated Annualized Exposure (ALE)",
    "pt": "Exposição Anualizada Estimada (ALE)",
    "fr": "Exposition Annualisée Estimée (ALE)",
    "de": "Geschätzte jährliche Exposition (ALE)",
    "ja": "推定年間エクスポージャー（ALE）"
}

for lang, title in LINEAGE_COL_TITLES.items():
    if lang in data:
        data[lang]["ch4_lineage_col_rate"] = title
        data[lang]["ch4_lineage_col_hourly"] = title

# 2. Add CAPITAL_INEFFICIENCY and PRODUCTIVITY_TOIL to executive_summary_narrative.archetypes
exec_archetypes = data.setdefault("executive_summary_narrative", {}).setdefault("archetypes", {})

exec_archetypes["CAPITAL_INEFFICIENCY"] = {
    "es": {
        "p1_operational_posture": "La evaluación estratégica de **{tower_name}** en {client_name} ({operational_mission}) sitúa su madurez estimada en **{maturity_score} sobre 5,0 ({maturity_tier_label})**. El modelo de gobierno actual coordina las operaciones cotidianas de {primary_workloads_summary}. No obstante, se identifican oportunidades para **{posture_modernization_focus}** optimizando el retorno de la inversión tecnológica.",
        "findings_lead_in": "La auditoría fiduciaria destaca las siguientes áreas prioritarias para optimizar el gasto y la gobernanza:",
        "p3_financial_exposure": "Bajo el estándar internacional Open FAIR™ (Factor Analysis of Information Risk), las ineficiencias fiduciarias evaluadas en **{tower_name}** representan una **exposición de riesgo latente estimada en {annual_loss_expectancy_fmt} anualizados**, cifra que refleja el sobrecoste acumulado por infraestructuras no optimizadas, desvío presupuestario y pasivos de licenciamiento.\n\nAdicionalmente, ante un **escenario adverso de contingencia por regularización de licencias o desalineación contractual grave**, el proceso de auditoría y renegociación con proveedores requeriría una ventana de estabilización prolongada, elevando el impacto contingente extraordinario hasta **{p90_var_exposure_fmt}** al computar ajustes retroactivos de licenciamiento y consultoría especializada de FinOps.",
        "p4_modernization_mandate": "En conclusión, el diagnóstico del estado actual demuestra una base operativa consolidada sobre la cual evolucionar hacia la madurez financiera. Mientras {strongest_dim_name} lidera con {strongest_dim_score} sobre 5,0, el desempeño global ({maturity_score} sobre 5,0) presenta su mayor margen de avance en {weakest_dim_name} ({weakest_dim_score} sobre 5,0). Implantar prácticas de optimización continua permitirá contener la deuda técnica y liberar capital operativo para el negocio."
    },
    "en": {
        "p1_operational_posture": "The strategic assessment of **{tower_name}** at {client_name} ({operational_mission}) establishes an estimated architectural maturity score of **{maturity_score} out of 5.0 ({maturity_tier_label})**. The current governance framework sustains daily operations across {primary_workloads_summary}. However, strategic opportunities exist to **{posture_modernization_focus}** to optimize technology investment return.",
        "findings_lead_in": "Fiduciary analysis highlights the following priority areas to optimize expenditure and contract governance:",
        "p3_financial_exposure": "Under the international Open FAIR™ (Factor Analysis of Information Risk) standard, fiduciary inefficiencies assessed within **{tower_name}** represent an **estimated latent risk exposure of {annual_loss_expectancy_fmt} annualized**, reflecting unhedged value leakage from unoptimized resources, cloud drift, and software licensing true-up liabilities.\n\nAdditionally, under an **adverse vendor compliance audit or severe contractual commitment drift scenario**, stabilizing expenditure and negotiating true-ups would require a multi-quarter remediation window, elevating the single extreme impact up to **{p90_var_exposure_fmt}** when factoring in retroactive licensing adjustments and specialized FinOps advisory.",
        "p4_modernization_mandate": "In conclusion, the current diagnostic demonstrates a solid operational baseline upon which to advance toward financial maturity. While {strongest_dim_name} leads at {strongest_dim_score} out of 5.0, overall maturity ({maturity_score} out of 5.0) exhibits its primary opportunity for advancement in {weakest_dim_name} ({weakest_dim_score} out of 5.0). Establishing continuous cost governance will contain technical debt and unlock capital for core strategic priorities."
    }
}

exec_archetypes["PRODUCTIVITY_TOIL"] = {
    "es": {
        "p1_operational_posture": "La evaluación técnica de **{tower_name}** en {client_name} ({operational_mission}) sitúa su madurez estimada en **{maturity_score} sobre 5,0 ({maturity_tier_label})**. Los servicios actuales facilitan la operativa diaria de {primary_workloads_summary}. Sin embargo, se detectan fricciones para **{posture_modernization_focus}** que consumen capacidad de los equipos.",
        "findings_lead_in": "El diagnóstico operativo identifica las siguientes áreas prioritarias para eliminar fricciones y trabajo repetitivo:",
        "p3_financial_exposure": "Bajo el estándar internacional Open FAIR™ (Factor Analysis of Information Risk), la fricción operativa y el trabajo manual repetitivo evaluados en **{tower_name}** suponen una **exposición de riesgo latente estimada en {annual_loss_expectancy_fmt} anualizados**, cuantificando la pérdida de productividad, tiempos de espera e ineficiencias de soporte a lo largo de un año.\n\nAdicionalmente, ante un **escenario adverso de crisis por acumulación de incidencias o fallo masivo en herramientas de usuario**, el restablecimiento operativo y la resolución del atasco de peticiones requeriría un esfuerzo extraordinario prolongado, elevando el coste derivado de horas improductivas y soporte extraordinario hasta **{p90_var_exposure_fmt}**.",
        "p4_modernization_mandate": "En conclusión, el entorno cuenta con capacidades operativas estables pero con margen para automatizar tareas repetitivas. Mientras {strongest_dim_name} destaca con {strongest_dim_score} sobre 5,0, la madurez global ({maturity_score} sobre 5,0) presenta su mayor potencial de avance en {weakest_dim_name} ({weakest_dim_score} sobre 5,0). Automatizar estos flujos permitirá reducir el toil y potenciar el rendimiento de los equipos."
    },
    "en": {
        "p1_operational_posture": "The technical assessment of **{tower_name}** at {client_name} ({operational_mission}) reflects an estimated maturity score of **{maturity_score} out of 5.0 ({maturity_tier_label})**. Baseline operations effectively support {primary_workloads_summary}. However, operational friction exists to **{posture_modernization_focus}** consuming team bandwidth.",
        "findings_lead_in": "Operational analysis identifies the following priority areas to eliminate toil and friction:",
        "p3_financial_exposure": "Under the international Open FAIR™ (Factor Analysis of Information Risk) standard, operational toil and repetitive manual overhead assessed within **{tower_name}** represent an **estimated latent risk exposure of {annual_loss_expectancy_fmt} annualized**, quantifying lost engineering productivity, support delays, and context-switching overhead.\n\nAdditionally, under an **adverse service incident backlog or widespread collaboration tool outage scenario**, clearing ticket queues and manual triage would require extensive emergency effort, driving single-event lost productivity impact up to **{p90_var_exposure_fmt}**.",
        "p4_modernization_mandate": "In conclusion, the operational baseline is stable but exhibits clear opportunities to automate manual workflows. While {strongest_dim_name} leads at {strongest_dim_score} out of 5.0, overall maturity ({maturity_score} out of 5.0) exhibits its primary opportunity for advancement in {weakest_dim_name} ({weakest_dim_score} out of 5.0). Eliminating toil through workflow automation will directly enhance enterprise workforce agility."
    }
}

LOCALES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("✓ Successfully remediated ch4_lineage_col_rate and executive summary archetypes.")
