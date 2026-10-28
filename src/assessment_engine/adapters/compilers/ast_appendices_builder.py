from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, List

from assessment_engine.adapters.compilers.ast_table_builders import (
    build_lm_scale_table,
    build_tef_scale_table,
)
from assessment_engine.domain.schemas.ast import (
    CellNode,
    HeadingNode,
    ParagraphNode,
    SpacerNode,
    TableNode,
    TableRowNode,
)

logger = logging.getLogger(__name__)


def build_appendix_a_glossary(
    ctx: dict[str, Any], nodes: List[Any], primary_color_rgb: Any
) -> None:
    """Builds Appendix A: Glossary and List of Abbreviations."""
    vocab = ctx["vocab"]
    case_dir = ctx["case_dir"]
    meta_lang = ctx["meta_lang"]

    app_a_title = re.sub(
        r"^(Apéndice|Appendix)\s+[A-Z]:\s*",
        "",
        vocab.get("appendix_a_title", "Lista de Abreviaturas"),
    )
    nodes.append(
        HeadingNode(text=app_a_title, level=1, primary_color_rgb=primary_color_rgb)
    )
    nodes.append(
        ParagraphNode(
            text=vocab.get(
                "appendix_a_intro",
                "A continuación se definen los términos técnicos utilizados:",
            )
        )
    )

    from assessment_engine.infrastructure.config_loader import (
        load_abbreviations_glossary,
    )

    try:
        full_glossary = load_abbreviations_glossary()
        client_glossary_path = case_dir / "client_abbreviations_glossary.json"
        if client_glossary_path.exists():
            try:
                with open(client_glossary_path, "r", encoding="utf-8-sig") as cgf:
                    client_glossary = json.load(cgf)
                    for lang, terms in client_glossary.items():
                        if lang in full_glossary:
                            full_glossary[lang].update(terms)
                        else:
                            full_glossary[lang] = terms
            except (OSError, ValueError, KeyError, AttributeError) as ex:
                logger.debug(f"[Fallback] Excepción controlada: {ex}")

        lang_key = "en" if meta_lang.startswith("en") else "es"
        glossary = full_glossary.get(lang_key, full_glossary.get("es", {}))

        headers = vocab.get("appendix_a_headers", ["Término", "Definición"])
        rows = [
            TableRowNode(
                cells=[
                    CellNode(
                        text=h,
                        bold=True,
                        bg_color="0072BC",
                        text_color_rgb=[255, 255, 255],
                        align="CENTER",
                    )
                    for h in headers
                ],
                is_header=True,
            )
        ]
        for term, definition in sorted(glossary.items()):
            rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=term, bold=True, align="CENTER"),
                        CellNode(text=definition),
                    ]
                )
            )
        nodes.append(TableNode(rows=rows))
    except Exception as ex:
        logger.warning(f"Error loading glossary: {ex}")


def build_appendix_b_disclaimer(
    ctx: dict[str, Any], nodes: List[Any], primary_color_rgb: Any
) -> None:
    """Builds Appendix B: Regulatory & Liability Disclaimer."""
    vocab = ctx["vocab"]
    app_b_title = re.sub(
        r"^(Apéndice|Appendix)\s+[A-Z]:\s*",
        "",
        vocab.get(
            "appendix_b_title", "Cláusula de Limitación de Responsabilidad"
        ),
    )
    nodes.append(
        HeadingNode(text=app_b_title, level=1, primary_color_rgb=primary_color_rgb)
    )
    for i in range(1, 6):
        disc_text = vocab.get(f"disclaimer_text_{i}", "")
        if disc_text:
            nodes.append(ParagraphNode(text=disc_text))
            nodes.append(SpacerNode(points=8))


def build_appendix_c_custody(
    ctx: dict[str, Any], nodes: List[Any], primary_color_rgb: Any
) -> None:
    """Builds Appendix C: Chain of Custody & Document Provenance Registry."""
    vocab = ctx["vocab"]
    app_c_title = re.sub(
        r"^(Apéndice|Appendix)\s+[A-Z]:\s*",
        "",
        vocab.get(
            "appendix_c_title", "Registro de Custodia de Fuentes de Información"
        ),
    )
    nodes.append(
        HeadingNode(text=app_c_title, level=1, primary_color_rgb=primary_color_rgb)
    )
    nodes.append(
        ParagraphNode(
            text=vocab.get(
                "appendix_c_intro",
                "Registro formal de trazabilidad e inmutabilidad de fuentes de evidencia.",
            )
        )
    )


def build_appendix_d_methodology(
    ctx: dict[str, Any],
    nodes: List[Any],
    primary_color_rgb: Any,
    brand_data: dict[str, Any],
    alt_row_hex: str,
) -> None:
    """Builds Appendix D: Assessment Methodology (Maturity Models & Open FAIR Standards)."""
    vocab = ctx["vocab"]
    meta_lang = ctx["meta_lang"]
    currency = ctx["currency"]
    tower_id = ctx["tower_id"]
    blueprint_data = ctx["blueprint_data"]

    app_d_title = re.sub(
        r"^(Apéndice|Appendix)\s+[A-Z]:\s*",
        "",
        vocab.get(
            "methodology_chapter_title",
            "Objetivo, Alcance y Marco Metodológico",
        ),
    )
    nodes.append(
        HeadingNode(text=app_d_title, level=1, primary_color_rgb=primary_color_rgb)
    )

    nodes.append(
        HeadingNode(
            text="Metodología de Valoración de Madurez",
            level=2,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        ParagraphNode(
            text="La madurez se califica en una escala analítica del 1,00 al 5,00, donde cada nivel determina un estadio de control:"
        )
    )
    levels = [
        "**Nivel 1 - Inicial (1.0-1.8):** Prácticas ad-hoc, inestables o dependientes del esfuerzo heroico de personas clave.",
        "**Nivel 2 - Básico (1.8-2.6):** Prácticas funcionales de manera parcial o irregular, sin consistencia organizativa.",
        "**Nivel 3 - Estandarizado (2.6-3.4):** Procesos formalizados e implantados de manera coherente en toda la organización.",
        "**Nivel 4 - Optimizado (3.4-4.2):** Capacidades industrializadas, gobernadas predictivamente y sustentadas en métricas.",
        "**Nivel 5 - Avanzado (4.2-5.0):** Procesos dinámicos impulsados por automatización inteligente y mejora continua.",
    ]
    for lvl in levels:
        nodes.append(ParagraphNode(text=lvl, style="List Bullet"))

    nodes.append(SpacerNode(points=10))
    nodes.append(
        HeadingNode(
            text="Capacidades Evaluadas y Cálculo del Score",
            level=2,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        ParagraphNode(
            text="El nivel de madurez técnica y el score global de la torre se consolidan mediante el promedio ponderado de las calificaciones obtenidas en las siguientes dimensiones y KPIs evaluados:"
        )
    )

    tower_def_file = (
        Path("engine_config/towers")
        / tower_id
        / f"tower_definition_{tower_id.lower()}.json"
    )
    if not tower_def_file.exists():
        tower_def_file = (
            Path("engine_config/towers")
            / tower_id
            / f"tower_definition_{tower_id}.json"
        )

    t_def = {}
    if tower_def_file.exists():
        try:
            with open(tower_def_file, "r", encoding="utf-8-sig") as tdf:
                t_def = json.load(tdf)
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug(f"[Fallback] Excepción controlada: {ex}")

    pillars_list = t_def.get("pillars", []) if isinstance(t_def, dict) else []
    if not pillars_list:
        pillars_list = blueprint_data.get("pillars_analysis", [])

    for p in pillars_list:
        p_name = p.get("pillar_name", p.get("pilar_name", "Pilar"))
        p_weight = int(p.get("weight_pct", p.get("weight", 20)))
        kpi_names = []
        for kpi in p.get("kpis", []):
            k_name = kpi.get("kpi_name", "KPI").strip()
            if k_name and not k_name.isupper() and len(k_name) > 4:
                k_name = k_name[0].lower() + k_name[1:]
            kpi_names.append(k_name)

        if len(kpi_names) > 1:
            kpi_str = ", ".join(kpi_names[:-1]) + " y " + kpi_names[-1]
        elif kpi_names:
            kpi_str = kpi_names[0]
        else:
            kpi_str = "las capacidades operativas del pilar"

        p_bullet_text = (
            f"**{p_name} (Peso: {p_weight}%)**: Evalúa de manera integral la madurez operativa "
            f"y los baselines técnicos de la infraestructura, analizando críticamente factores clave como {kpi_str}."
        )
        nodes.append(ParagraphNode(text=p_bullet_text, style="List Bullet"))

    # D.2 Quantitative Risk Methodology (FAIR)
    nodes.append(SpacerNode(points=15))
    nodes.append(
        HeadingNode(
            text="Metodología Cuantitativa de Riesgos (FAIR)",
            level=2,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        ParagraphNode(
            text="Este diagnóstico técnico aplica el estándar internacional **O-FAIR (Factor Analysis of Information Risk)** de *The Open Group* para modelar, cuantificar y priorizar la exposición al riesgo de infraestructura en términos financieros reales."
        )
    )
    nodes.append(
        ParagraphNode(
            text='Para evitar la "Falacia de los Promedios" (donde las estimaciones fijas e individuales distorsionan el riesgo real), el motor de la plataforma aplica un algoritmo de simulación actuarial de Monte Carlo de 10.000 iteraciones para cada hallazgo detectado, basado en los siguientes principios científicos:'
        )
    )

    is_critical = brand_data.get("styling", {}).get("is_critical", None)
    if is_critical is None:
        is_critical = (
            blueprint_data.get("document_meta", {}).get(
                "enterprise_scale_critical", False
            )
            if isinstance(blueprint_data, dict)
            else False
        )

    nodes.append(
        HeadingNode(
            text="Criterios de Frecuencia de Amenazas (TEF)",
            level=3,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(build_tef_scale_table(vocab, meta_lang, alt_row_hex))

    nodes.append(SpacerNode(points=10))
    nodes.append(
        HeadingNode(
            text="Criterios de Magnitud de Pérdida Financiera (LM)",
            level=3,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        build_lm_scale_table(
            vocab, meta_lang, currency, is_critical, alt_row_hex
        )
    )

    nodes.append(SpacerNode(points=10))
    nodes.append(
        HeadingNode(
            text="Indicadores Avanzados de Resiliencia Sistémica",
            level=3,
            primary_color_rgb=primary_color_rgb,
        )
    )
    nodes.append(
        ParagraphNode(
            text="Para medir la resiliencia cruzada de la plataforma e identificar riesgos que trascienden el perímetro de una única torre, el motor de la plataforma calcula y califica los siguientes indicadores decisionales avanzados utilizando modelos de decisión multicriterio y propagación en red:"
        )
    )
    indicators = [
        "1. **Criticidad de Negocio (MCDA) [Rango 0% a 100%]:** Un valor superior al 80% (Extrema - Pilar Crítico) indica que el dominio tecnológico soporta directamente un servicio esencial de alta criticidad para la organización. Calificaciones de 50% a 79% representan un impacto alto pero de carácter secundario o diferido en el tiempo, y valores menores al 50% corresponden a un impacto medio de soporte operacional estándar.",
        "2. **Presión Regulatoria (MCDA) [Rango 0% a 100%]:** Un valor mayor al 80% (Crítica) determina que la infraestructura está sujeta a normativas y regulaciones obligatorias severas (como la directiva europea NIS2, DORA o normativas sectoriales aplicables) con alto impacto penal o financiero ante incumplimientos. Rangos de 50% a 79% indican presiones sectoriales moderadas, y valores inferiores al 50% corresponden a regulaciones básicas.",
        "3. **Viabilidad Operativa (MCDA) [Rango 0% a 100%]:** Mide la facilidad técnica y humana para ejecutar los proyectos propuestos (a mayor porcentaje, mayor facilidad). Un porcentaje superior al 60% representa proyectos viables y estándar. Valores inferiores al 60% indican una alta complejidad operacional, fuerte herencia de plataformas obsoletas (legacy), ventanas de mantenimiento críticas o falta de perfiles especializados.",
        "4. **Índice de Consistencia del Diagnóstico (DII) [Rango 0% a 100%]:** Cuantifica la volatilidad o sensibilidad del diagnóstico ante variaciones en las evidencias documentales recopiladas (a menor porcentaje, mayor robustez). Un valor por debajo del 15% (Estable - Diagnóstico Robusto) garantiza que la calificación es sólida matemáticamente y representativa frente a discrepancias técnicas. Rangos de 15% a 30% reflejan una consistencia moderada, y superiores al 30% representan una alta volatilidad.",
        "5. **Índice de Propagación de Fallos en Cascada (ERC) [Rango: 0,000 a 1,000]:** Utiliza un algoritmo de centralidad en red tipo PageRank para medir la capacidad de la torre de actuar como difusor de fallos técnicos hacia el resto de la plataforma corporativa. Valores mayores a 0,500 indican una Alta Influencia, donde cualquier incidente arrastrará de forma inmediata al resto de torres de TI. Rangos de 0,200 a 0,499 indican una influencia media, e inferiores a 0,200 representan componentes aislados con bajo riesgo de afectación colateral.",
        "6. **Punto Único de Fallo (SPOF) [SÍ / NO]:** Clasificación lógica de redundancia estructural. La condición 'SÍ' alerta sobre la presencia de activos o procesos de infraestructura críticos que carecen de balanceo activo, redundancia geográfica o alternativas operativas de respaldo, representando un riesgo material directo de interrupción total ante fallos individuales.",
    ]
    for ind in indicators:
        nodes.append(ParagraphNode(text=ind, style="List Bullet"))
