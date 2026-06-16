"""
Módulo generate_smoke_data.py.
Genera inputs sintéticos y deterministas para el caso smoke_ivirma.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path
from typing import Any

from assessment_engine.scripts.lib.client_intelligence import coerce_client_dossier_v3
from assessment_engine.scripts.lib.runtime_paths import ROOT

logger = logging.getLogger(__name__)

DEFAULT_CLIENT = "smoke_ivirma"
DEFAULT_SEED = 42
DEFAULT_SCENARIO = "baseline"
DEFAULT_TOWERS = ["T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]
DEFAULT_TOWER_TARGETS: dict[str, tuple[float, float]] = {
    "T2": (2.0, 3.0),
    "T3": (1.5, 2.5),
    "T4": (2.5, 3.5),
    "T5": (1.0, 2.0),
    "T6": (1.5, 2.5),
    "T7": (2.0, 3.0),
    "T8": (3.0, 4.0),
    "T9": (2.5, 3.5),
}
DEFAULT_CONTEXT_TEXT = """
Notas de la reunión de Assessment Tecnológico de IVIRMA (Smoke Test).

Contexto de Negocio:
La compañía está en fase de expansión inorgánica internacional impulsada por KKR, con el objetivo de duplicar la facturación a 1.300M€.
La principal preocupación del CEO es asegurar la integración rápida de nuevas clínicas manteniendo el nivel de excelencia clínica y operativa.

Tecnología:
El proveedor estratégico cloud es Microsoft Azure. Sin embargo, el crecimiento ha fragmentado la red de comunicaciones.
El almacenamiento de imágenes médicas e historiales clínicos es el core absoluto del negocio, pero no existe una estrategia inmutable de recuperación (Vault).

Seguridad y Normativa:
El CISO está alarmado por el aumento de incidentes de ransomware en el sector salud. Además, son conscientes de que la inminente aplicación de la directiva NIS2 en Europa les afecta directamente como operadores esenciales de salud, y actualmente su infraestructura no garantiza el cumplimiento.

Operaciones:
El soporte a usuarios (médicos y embriólogos) es muy manual, con un ITSM básico. Faltan procesos industrializados y visibilidad de los activos (CMDB inexistente), lo que choca con la agilidad necesaria para la expansión.
"""

VODAFONE_PUBLIC_CONTEXT_TEXT = """
Workshop sintético de assessment tecnológico para un gran operador telco paneuropeo inspirado en información pública de Vodafone.

Contexto de Negocio:
La compañía opera servicios móviles, fijo, cloud, IoT y ciberseguridad para clientes residenciales, empresas y administraciones públicas.
La agenda de dirección combina simplificación operativa, monetización B2B digital, mejora del cash-flow y aceleración del crecimiento en servicios convergentes y plataformas de conectividad.

Tecnología:
La estrategia tecnológica prioriza plataformas comunes, automatización de operaciones, modernización de red, observabilidad extremo a extremo y una evolución progresiva hacia entornos híbridos consistentes.
La presión sobre T2, T3 y T5 es especialmente alta porque la experiencia de cliente depende de plataformas resilientes, conectividad estable y capacidad de recuperación demostrable ante incidencias mayores.

Seguridad y Normativa:
El contexto regulatorio está marcado por NIS2, resiliencia operativa, privacidad, continuidad de servicio y escrutinio reforzado sobre infraestructuras críticas y cadenas de suministro.
La organización necesita demostrar gobierno, trazabilidad y tiempos de recuperación alineados con servicios de misión crítica.

Operaciones:
Existen capacidades maduras en grandes dominios, pero persisten heterogeneidades por país, legado operativo, herramientas duplicadas y variabilidad en procesos de soporte, cambios y respuesta ante incidentes.
El objetivo del assessment es identificar una hoja de ruta realista para consolidar plataformas, reducir complejidad y mejorar resiliencia sin comprometer la operación diaria.
"""

SCENARIOS: dict[str, dict[str, Any]] = {
    "baseline": {
        "context_text": DEFAULT_CONTEXT_TEXT,
        "tower_targets": DEFAULT_TOWER_TARGETS,
        "client_dossier": None,
    },
    "vodafone-public": {
        "context_text": VODAFONE_PUBLIC_CONTEXT_TEXT,
        "tower_targets": {
            **DEFAULT_TOWER_TARGETS,
            "T2": (3.1, 4.0),
            "T3": (3.0, 3.9),
            "T5": (2.8, 3.7),
        },
        "client_dossier": {
            "industry": "Telecomunicaciones",
            "financial_tier": "Tier 1",
            "priority_markets": ["Alemania", "Reino Unido", "España", "Italia"],
            "business_lines": [
                "B2C convergente",
                "B2B digital",
                "IoT",
                "Cloud y ciberseguridad",
            ],
            "active_transformations": [
                "Consolidación de plataformas comunes entre países",
                "Automatización de operaciones y observabilidad extremo a extremo",
                "Programa de resiliencia para servicios críticos",
            ],
            "business_constraints": [
                "Presión de margen y disciplina de cash-flow",
                "Limitada tolerancia a interrupciones de servicio en operación 24x7",
            ],
            "regulatory_pressures": [
                "Necesidad de demostrar resiliencia y continuidad en infraestructuras críticas",
                "Mayor escrutinio sobre trazabilidad operativa y cadena de suministro",
            ],
            "regulatory_frameworks": [
                "NIS2",
                "GDPR",
                "Telecom Security Act / normativa sectorial local",
                "ISO 22301",
            ],
            "ceo_agenda": (
                "Simplificar operaciones, proteger margen, acelerar servicios B2B "
                "digitales y sostener una experiencia de cliente consistente en "
                "mercados con alta presión competitiva."
            ),
            "technological_drivers": [
                "Automatización de operaciones de red y plataforma",
                "Consolidación de tooling y observabilidad extremo a extremo",
                "Resiliencia operativa para servicios críticos",
                "Modernización híbrida de plataformas de soporte al negocio",
            ],
            "vendor_dependencies": [
                "Hyperscalers para cargas híbridas y analítica",
                "Vendors de red y seguridad en múltiples países",
            ],
            "operating_constraints": [
                "Herramientas duplicadas y legado operativo por país",
                "Ventanas de cambio restringidas para servicios de misión crítica",
            ],
            "recent_incident_signals": [
                "La resiliencia y recuperación ante incidencias mayores es un foco explícito del escenario",
                "La dependencia de continuidad de servicio eleva la sensibilidad ante outages de red y plataforma",
            ],
            "osint_footprint": (
                "Huella tecnológica distribuida, fuerte dependencia de plataformas "
                "comunes, operaciones multinacionales y necesidades elevadas de "
                "estandarización entre países y dominios."
            ),
            "transformation_horizon": (
                "Programa de transformación escalonado a 24-36 meses con quick wins "
                "operativos y consolidación estructural de plataformas."
            ),
            "target_maturity_matrix": {
                "T1": 3.4,
                "T2": 3.9,
                "T3": 3.8,
                "T4": 3.6,
                "T5": 3.7,
                "T6": 4.0,
                "T7": 3.6,
                "T8": 3.7,
                "T9": 3.5,
                "T10": 3.2,
            },
            "evidences": [
                "Caso sintético basado en señales públicas de operadores telco paneuropeos.",
                "Contexto operativo orientado a conectividad, plataformas comunes y resiliencia.",
            ],
        },
    },
}


def normalize_towers(towers: list[str] | None) -> list[str]:
    normalized: list[str] = []
    for tower in towers or DEFAULT_TOWERS:
        tower_id = tower.upper().strip()
        if tower_id and tower_id not in normalized:
            normalized.append(tower_id)
    return normalized


def resolve_scenario_config(name: str) -> dict[str, Any]:
    scenario_name = name.strip() or DEFAULT_SCENARIO
    if scenario_name not in SCENARIOS:
        available = ", ".join(sorted(SCENARIOS))
        raise ValueError(
            f"Escenario desconocido: {scenario_name}. Disponibles: {available}"
        )
    return SCENARIOS[scenario_name]


def build_responses(
    root: Path,
    towers: list[str],
    seed: int,
    tower_targets: dict[str, tuple[float, float]] | None = None,
) -> list[str]:
    rng = random.Random(seed)
    responses_lines: list[str] = []
    targets = tower_targets or DEFAULT_TOWER_TARGETS

    for tower_id in towers:
        def_file = (
            root
            / "engine_config"
            / "towers"
            / tower_id
            / f"tower_definition_{tower_id}.json"
        )
        if not def_file.exists():
            continue

        data = json.loads(def_file.read_text(encoding="utf-8"))
        min_score, max_score = targets.get(tower_id, (2.0, 3.0))
        for pillar in data.get("pillars", []):
            for kpi in pillar.get("kpis", []):
                score = round(rng.uniform(min_score, max_score), 1)
                responses_lines.append(f"{kpi['kpi_id']}.PR1: {score}")

    return responses_lines


def generate_smoke_inputs(
    client: str = DEFAULT_CLIENT,
    towers: list[str] | None = None,
    seed: int = DEFAULT_SEED,
    scenario: str = DEFAULT_SCENARIO,
    root: Path = ROOT,
    write_files: bool = True,
) -> tuple[Path, Path]:
    client_id = client.strip() or DEFAULT_CLIENT
    client_dir = root / "working" / client_id
    scenario_config = resolve_scenario_config(scenario)
    if write_files:
        client_dir.mkdir(parents=True, exist_ok=True)

    normalized_towers = normalize_towers(towers)
    responses_lines = build_responses(
        root,
        normalized_towers,
        seed,
        tower_targets=scenario_config["tower_targets"],
    )

    responses_path = client_dir / "responses.txt"
    context_path = client_dir / "context.txt"
    dossier_path = client_dir / "client_intelligence.json"
    if write_files:
        responses_path.write_text("\n".join(responses_lines) + "\n", encoding="utf-8")
        context_path.write_text(
            str(scenario_config["context_text"]).strip() + "\n",
            encoding="utf-8",
        )
        dossier_template = scenario_config.get("client_dossier")
        if dossier_template:
            dossier = coerce_client_dossier_v3(
                client_name=client_id,
                data=dossier_template,
            )
            dossier_path.write_text(
                json.dumps(dossier, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        elif dossier_path.exists():
            dossier_path.unlink()

    return context_path, responses_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default=DEFAULT_CLIENT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--towers", nargs="*", default=DEFAULT_TOWERS)
    parser.add_argument(
        "--scenario", choices=sorted(SCENARIOS), default=DEFAULT_SCENARIO
    )
    args = parser.parse_args(argv)

    context_path, responses_path = generate_smoke_inputs(
        client=args.client,
        towers=args.towers,
        seed=args.seed,
        scenario=args.scenario,
    )

    responses_count = len(responses_path.read_text(encoding="utf-8").splitlines())
    logger.info(
        f"✅ Inputs smoke generados en {context_path.parent} "
        f"(contexto + {responses_count} respuestas)."
    )
    logger.info(f"   - {context_path}")
    logger.info(f"   - {responses_path}")


if __name__ == "__main__":
    main()
