"""Sanitizes engine_config/locales.json by purging all cement/quarry/weighbridge tenant contamination.

Replaces specific heavy manufacturing references with universal enterprise architecture terminology across all languages.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = ROOT / "engine_config" / "locales.json"


def sanitize() -> None:
    data = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))

    # Universal replacements map
    replacements = {
        # English
        "Factory and Quarry Connectivity (T3)": "Remote Facilities & Branch Connectivity (T3)",
        "Plant and quarry endpoint devices administered locally without centralized modern management.": (
            "Operational and remote facility endpoint devices administered locally without centralized modern management."
        ),
        "Industrial weighbridge systems, automated barrier controls, and cement dispatch software at manufacturing facilities.": (
            "Mission-critical core processing engines, enterprise clearing interfaces, and operational transactional platforms."
        ),
        "Industrial weighbridge control terminals operating on outdated hardware configurations and obsolete operating systems.": (
            "Core transactional terminals and processing engines operating on outdated hardware configurations and legacy operating systems."
        ),
        "Industrial weighbridge scales subjected to regular metrological calibration and preventive maintenance.": (
            "Core transactional processing engines maintained with verified operational stability and scheduled maintenance."
        ),
        "Transactional synchronization interface transferring weighbridge dispatch tickets to central SAP ERP.": (
            "Automated transactional synchronization interfaces transferring event logs and clearing records to central enterprise ERP."
        ),
        "weighbridge edge equipment fragility": "legacy operational interface fragility",
        "truck gridlock at factory gates": "operational bottlenecks and transaction processing delays",

        # Spanish
        "Conectividad de Fábrica y Cantera (T3)": "Conectividad de Sedes Remotas y Plantas (T3)",
        "Dispositivos de puesto de trabajo en planta y cantera administrados localmente sin gestión centralizada moderna.": (
            "Dispositivos de puesto de trabajo en plantas y sedes remotas administrados localmente sin gestión centralizada moderna."
        ),
        "Puestos de pesaje en estaciones de carga y entrega, software de expedición industrial, interfaces de pesaje industrial y comunicación con SAP.": (
            "Plataformas transaccionales de misión crítica, motores de liquidación e interfaces de comunicación con sistemas centrales ERP."
        ),
        "Puestos de control de pesaje en plantas operando sobre estaciones de trabajo con hardware desfasado y sistemas operativos obsoletos.": (
            "Puestos de control transaccional operando sobre estaciones de trabajo con hardware desfasado y sistemas operativos obsoletos."
        ),
        "Equipos de pesaje industrial con calibración metrológica periódica y mantenimiento regular en todas las básculas.": (
            "Motores transaccionales de misión crítica con estabilidad operativa verificada y mantenimiento preventivo periódico."
        ),
        "Mecanismo de sincronización de albaranes de pesaje hacia el sistema central de facturación ERP.": (
            "Mecanismos de sincronización transaccional continua hacia el sistema central corporativo ERP."
        ),
        "fragilidad de los equipos de pesaje en báscula": "fragilidad de las interfaces transaccionales heredadas",
        "colapsos de camiones en fábrica": "bloqueos operativos y demoras en el procesamiento de transacciones",
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

    sanitized = walk_and_replace(data)

    LOCALES_PATH.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Sanitized: {LOCALES_PATH}")


if __name__ == "__main__":
    sanitize()
