"""Remediation of all defect classes identified in Argon's code and catalog audit.

1. Eradicates quarry, cement, plant, weighbridge (pesaje/báscula), 500m radius, and expedición from locales.json.
2. Neutralizes hardcoded vendor names (HPE, Cohesity, Fortinet, Mayo 2027) in catalog presets.
3. Generalizes European NIS2 references to global regulatory frameworks (DORA, ISO 27001, NIS2).
4. Reconciles Chapter 4 three-vector formula block with narrative.
5. Harmonizes tomo_ch1_p1 placeholder contracts and enforces decimal commas in Spanish.
6. Adds accented 'aún así' to adversative_connective_prefixes.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = ROOT / "engine_config" / "locales.json"


def remediate() -> None:
    data = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))

    # 1. Global text replacements for industry, client, and vendor hardcoding
    replacements = {
        "Conectividad de Plantas y Canteras (T3)": "Conectividad de Sedes Distribuidas y Enlaces Remotos (T3)",
        "Switches de acceso en canteras y plantas con ciclos de vida próximos al fin de soporte": "Switches de acceso en sedes operativas y centros distribuidos con ciclos de vida próximos al fin de soporte",
        "plantas industriales, canteras y sedes internacionales": "sedes operativas, oficinas regionales y centros corporativos",
        "Dispositivos en plantas y canteras gestionados de forma local sin enrolamiento homogéneo en la plataforma central.": "Dispositivos en sedes operativas y centros remotos gestionados de forma local sin enrolamiento homogéneo en la plataforma central.",
        "doble acometida en canteras clave": "doble acometida en sedes críticas",
        "Puestos de Control de Pesaje en Fábrica (T10)": "Puestos de Control y Terminales de Operación Core (T10)",
        "Interrupción del Pesaje y Expedición en Planta Fabril": "Interrupción del Procesamiento Transaccional y Operaciones Core",
        "Las estaciones de pesaje de fábrica validan los despachos contra el sistema central": "Las terminales transaccionales de operación validan los registros contra el sistema central",
        "Concentración de la resiliencia en un radio geográfico de 500 metros, actuando como punto único de fallo ante catástrofes de zona.": "Concentración de la resiliencia en una misma zona geográfica sin suficiente dispersión, actuando como punto único de fallo ante catástrofes regionales.",
        "Concentración de la resiliencia en un radio geográfico de 500 metros, actuando como punto único de fallo (SPOF) catastrófico ante contingencias ambientales o de suministro eléctrico": "Concentración de la resiliencia en una misma zona geográfica sin suficiente dispersión, actuando como punto único de fallo ante contingencias regionales o de suministro eléctrico",
        "Plataforma de backup Cohesity, réplicas asíncronas entre CPDs, sistemas de control industrial (MES/SCADA) y estaciones de sistemas de expedición en plantas.": "Plataforma de backup empresarial con almacenamiento inmutable, réplicas asíncronas entre centros de datos y sistemas transaccionales core de ejecución operativa.",
        "Saturación de Cómputo y Shock Contractual Mayo 2027": "Saturación de Capacidad de Cómputo y Vencimiento de Licenciamiento Core",
        "H1 (Mayo 2027)": "H1 (Meses 1-6)",
        "6 nodos hiperconvergentes HPE Hiperconvergente, hipervisor VMware ESXi, clústeres locales en CPD 1 y CPD 2, huella multicloud en GCP, Azure y OCI.": "Nodos hiperconvergentes de alta densidad, hipervisores empresariales virtualizados, clústeres locales de alta disponibilidad y presencia multicloud gestionada.",
        "Cabinas de almacenamiento unificado SAN/NAS FAS/AFF bajo protocolos NFS y Fibre Channel, almacenamiento secundario de copias Cohesity.": "Cabinas de almacenamiento unificado SAN/NAS bajo protocolos de bloque y archivo de alto rendimiento, con repositorios secundarios inmutables de copia.",
        "cargas críticas (SAP S/4HANA) sobre infraestructura cloud de primer nivel (GCP/Azure)": "cargas críticas transaccionales sobre infraestructura cloud de primer nivel",
        "firewalls perimetrales Fortinet, autenticación Microsoft Entra ID": "firewalls perimetrales de última generación (NGFW), federación de identidades centralizada",
        "4.10. Sistemas Críticos de Expedición y Operaciones Locales (T10)": "4.10. Sistemas Transaccionales Core y Plataformas Críticas (T10)",
        "4.10. Expedición y Sistemas de Planta (T10)": "4.10. Sistemas Transaccionales Core y Plataformas Críticas (T10)",
        "simulacros periódicos de recuperación ante desastres (game days)": "simulacros periódicos de recuperación ante desastres y pruebas de contingencia",
        "Adecuación a la Directiva Europea NIS2: Los nuevos estándares regulatorios de ciberresiliencia exigirán a Molins una acreditación formal": "Adecuación a Marcos Regulatorios Internacionales: Las normativas globales de ciberresiliencia (ej. NIS2, DORA, ISO 27001) exigen una acreditación formal",
        "políticas de seguridad y service mesh": "políticas de seguridad y malla de servicios (service mesh)",
        "guardrails de gobierno": "salvaguardas preventivas de gobierno",
        "guardrails automatizados": "salvaguardas automatizadas",
        "Guardrails Automatizados": "Salvaguardas Automatizadas",
        "Quality of Service (QoS)": "Calidad de Servicio (QoS)",
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

    # 2. Formula block reconciliation: restore 3 vectors in Chapter 4 formula
    for lang, lang_branch in data.items():
        if isinstance(lang_branch, dict):
            if "ch4_sec1_formula_block" in lang_branch:
                # Formula with 3 vectors: direct operational stoppage + SLA penalty + emergency recovery labor
                lang_branch["ch4_sec1_formula_block"] = (
                    "R_{hourly, est} = C_{op, est} + C_{sla, est} + C_{rec, est}"
                )

            # 3. Add accented 'aún así' to adversative_connective_prefixes
            prefixes = lang_branch.get("adversative_connective_prefixes", [])
            if isinstance(prefixes, list):
                if "aún así" not in prefixes:
                    prefixes.append("aún así")
                if "Aún así" not in prefixes:
                    prefixes.append("Aún así")
                lang_branch["adversative_connective_prefixes"] = prefixes

    # 4. Clean Spanish T10 commentary to eliminate básculas and camiones
    if "es" in data and "ch3_scorecard_by_tower" in data["es"]:
        data["es"]["ch3_scorecard_by_tower"]["T10"] = (
            "Evaluados en {score_val} sobre 5,0 ({maturity_tier_label}), las plataformas transaccionales core representan "
            "un componente crítico para {client_name}. La estabilidad de las integraciones principales ({strongest_pillar_name}, {strongest_pillar_score}/5,0) "
            "contrasta con las oportunidades de modernización identificadas en {weakest_pillar_name} ({weakest_pillar_score}/5,0), "
            "donde consolidar la resiliencia operativa y la automatización resulta esencial para prevenir tiempos de inactividad no planificados "
            "y soportar la escalabilidad a largo plazo."
        )

    # 5. Reconcile tomo_ch1_p1 in Spanish: accept standard parameters and enforce decimal comma
    if "es" in data:
        data["es"]["tomo_ch1_p1"] = (
            "La evaluación integral del portafolio tecnológico de {client_name} abarca {domain_count} dominios operativos "
            "y arroja un Índice Global de Madurez de {global_score} sobre 5,00 ({maturity_tier_label}), situando la infraestructura "
            "en un estadio de madurez operativa definido. Este resultado refleja una base tecnológica capaz de sustentar las operaciones actuales, "
            "pero sujeta a fricciones de escalabilidad y dependencias operativas que justifican la ejecución del plan director de modernización."
        )

    # 5. Enforce comma decimals in Spanish and Portuguese subpillars
    for lang in ["es", "pt"]:
        if lang in data:
            cat = data[lang].get("tomo_tower_forensic_catalog", {})
            for t_id, t_info in cat.items():
                subp = t_info.get("subpillars", [])
                for s in subp:
                    if isinstance(s, list) and len(s) > 1:
                        s[1] = str(s[1]).replace(".", ",")

    LOCALES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Remediation script executed successfully. Updated: {LOCALES_PATH}")


if __name__ == "__main__":
    remediate()
