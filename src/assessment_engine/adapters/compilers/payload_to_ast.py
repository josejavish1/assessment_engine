import logging
logger = logging.getLogger(__name__)
import csv
import html
import json
import re
from pathlib import Path
from typing import Any, List

from assessment_engine.infrastructure.localization import (
    format_date_localized,
)

from assessment_engine.domain.schemas.ast import (
    CellNode,
    DocumentAST,
    HeadingNode,
    PageBreakNode,
    ParagraphNode,
    PictureNode,
    SpacerNode,
    TableNode,
    TableRowNode,
)


def clean_client_name(client_name: str) -> str:
    """Cleans a raw client name (which might be a slug or directory name) for reporting.

    Removes version tags (e.g. _v3, _v2, -v4), replaces underscores/hyphens with spaces,
    strips trailing whitespace, and ensures Proper Noun Title Case capitalization.
    """
    if not client_name:
        return "Cliente"
    import re
    # Remove version endings like _v3, _V2, -v4, etc.
    cleaned = re.sub(r'[_-][vV]\d+\b', '', client_name)
    # Replace underscores/hyphens with spaces
    cleaned = cleaned.replace('_', ' ').replace('-', ' ')
    cleaned = cleaned.strip()
    
    # Elite Capitalization: Ensure it is a Proper Noun (Title Case)
    # If the cleaned string is all lowercase, convert it to Title Case (e.g., 'cliente' -> 'Cliente')
    # If it has uppercase, preserve the client's custom branding (e.g., 'CLIENTE' stays 'CLIENTE')
    if cleaned.islower():
        return cleaned.title()
    return cleaned


from assessment_engine.adapters.compilers.ast_appendices_builder import (
    build_appendix_a_glossary as _build_appendix_a_glossary_fn,
    build_appendix_b_disclaimer as _build_appendix_b_disclaimer_fn,
    build_appendix_c_custody as _build_appendix_c_custody_fn,
    build_appendix_d_methodology as _build_appendix_d_methodology_fn,
)
from assessment_engine.adapters.compilers.ast_table_builders import (
    TEF_SCALE_DEFINITIONS,
    build_criticality_bullet as _build_criticality_bullet,
    build_dii_bullet as _build_dii_bullet,
    build_erc_bullet as _build_erc_bullet,
    build_feasibility_bullet as _build_feasibility_bullet,
    build_heatmap_mosaic as _build_heatmap_mosaic,
    build_lm_scale_table as _build_lm_scale_table,
    build_regulatory_bullet as _build_regulatory_bullet,
    build_spof_bullet as _build_spof_bullet,
    build_tef_scale_table as _build_tef_scale_table,
)


class PayloadToASTBridge:
    """Translates structured JSON payloads and associated markdown modules into a unified Document Abstract Syntax Tree (AST).
    This process maintains semantic identity and structural alignment with the source content."""

    def __init__(
        self,
        brand_profile_path: str = "engine_config/brand_profile.json",
        locales_path: str = "engine_config/locales.json",
    ):
        self.brand_profile_path = Path(brand_profile_path)
        self.locales_path = Path(locales_path)
        self.meta_lang = "es"

        # Load brand profiles, using fallback values to ensure required assets are present.
        self.company_name = "Consultora"
        self.classification = "Confidencial"
        self.disclaimer = ""
        self.primary_color_rgb = [0, 114, 188]  # Primary corporate brand color code.
        self.alt_row_hex = "F2F2F2"

        self.brand_data = {}
        from assessment_engine.infrastructure.config_loader import load_brand_profile

        self.meta_lang = "es"
        try:
            brand = load_brand_profile()
            self.brand_data = brand
            self.company_name = brand.get("company_name", self.company_name)
            self.classification = brand.get(
                "default_classification", self.classification
            )
            self.disclaimer = brand.get("disclaimer_text", self.disclaimer)
            styling = brand.get("styling", {})
            p_hex = styling.get("primary_color_hex", "0072BC")
            self.alt_row_hex = styling.get("alternate_row_color_hex", self.alt_row_hex)

            #
            r = int(p_hex[0:2], 16)
            g = int(p_hex[2:4], 16)
            b = int(p_hex[4:6], 16)
            self.primary_color_rgb = [r, g, b]
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")


    def convert(
        self, blueprint_payload_path: str, approved_annex_path: str
    ) -> DocumentAST:
        """Consolidates information from input JSON files and associated Markdown/CSV modules
        to generate a complete Document Abstract Syntax Tree (AST)."""
        ctx = self._extract_conversion_context(blueprint_payload_path, approved_annex_path)
        self.meta_lang = ctx.get("meta_lang", "es")

        nodes: List[Any] = []
        self._build_cover_and_toc(ctx, nodes)
        self._build_executive_summary_and_scope(ctx, nodes)
        self._build_systemic_risk_section(ctx, nodes)
        risks_data_list, fair_lookup = self._build_maturity_and_benchmarks(ctx, nodes)
        self._build_fair_risk_analysis(ctx, nodes, risks_data_list)
        self._build_detailed_findings_log(ctx, nodes, risks_data_list, fair_lookup)
        self._build_conclusions_and_appendices(ctx, nodes)

        return DocumentAST(
            title=f"Technical Annex - Tower {ctx['tower_id']}",
            metadata=ctx["tower_meta"],
            nodes=nodes,
        )

    def _extract_conversion_context(
        self, blueprint_payload_path: str, approved_annex_path: str
    ) -> dict[str, Any]:
        """Extract and prepare all context variables needed for DocumentAST compilation."""
        blueprint_file = Path(blueprint_payload_path)
        annex_file = Path(approved_annex_path)
        case_dir = blueprint_file.parent
        modules_dir = case_dir / "asis_modules"

        #
        with open(blueprint_file, "r", encoding="utf-8-sig") as f:
            blueprint_data = json.load(f)

        client_intel_file = case_dir.parent / "client_intelligence.json"
        intel_data = {}
        if client_intel_file.exists():
            try:
                with open(client_intel_file, "r", encoding="utf-8-sig") as cif:
                    intel_data = json.load(cif)
            except Exception as e:
                logger.info(f"⚠️ Error loading client_intelligence in AST Bridge: {e}")

        if annex_file.exists():
            try:
                with open(annex_file, "r", encoding="utf-8-sig") as f:
                    json.load(f)
            except (OSError, ValueError, KeyError, AttributeError) as ex:

                logger.debug(f"[Fallback] Excepción controlada: {ex}")

        tower_meta = blueprint_data.get("document_meta", {})
        meta_lang = tower_meta.get("language", "es").lower()
        from assessment_engine.infrastructure.config_loader import (
            resolve_localized_vocabulary,
        )

        vocab = resolve_localized_vocabulary(meta_lang)

        # Resolve localized brand attributes from canonical vocabulary
        self.classification = vocab.get(
            "default_classification", self.classification
        )
        self.disclaimer = vocab.get("disclaimer_text", self.disclaimer)

        tower_name = tower_meta.get("tower_name", "Desconocida")
        tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
        client_name = clean_client_name(tower_meta.get("client_name", "Cliente"))
        version = tower_meta.get("version", "1.0")
        date_str = format_date_localized(
            tower_meta.get("date"), locale=meta_lang
        )
        currency = tower_meta.get("currency", "€")

        # Dynamically detect organizational scale to apply customized calibration.
        is_critical = self.brand_data.get("styling", {}).get("is_critical", None)
        if is_critical is None:
            is_critical = False # default fallback

        # Load scoring and global ALE data for interpolation.
        total_fair_ale = blueprint_data.get("total_fair_ale", 0.0)

        # Load scoring output to get exact score and band deterministically
        scoring_file = case_dir / "scoring_output.json"
        exact_score = None
        exact_band = None
        if scoring_file.exists():
            try:
                with open(scoring_file, "r", encoding="utf-8-sig") as sf:
                    score_data = json.load(sf)
                    exact_score = score_data.get("tower_score_exact")
                    exact_band = score_data.get("maturity_band_from_exact", {}).get("label")
            except Exception as e:
                logger.info(f"⚠️ Error loading scoring_output in AST Bridge: {e}")

        global_score = str(exact_score) if exact_score is not None else (
            blueprint_data.get("executive_summary", {})
            .get("global_score", "3.0")
            .split()[0]
        )
        global_band = exact_band if exact_band is not None else blueprint_data.get("executive_summary", {}).get(
            "global_band", "Definido"
        )
        global_reading = (
            blueprint_data.get("pillar_score_profile", {})
            .get("pillars", [{}])[0]
            .get("executive_reading", "Gobernanza estándar.")
        )

        try:
            gs_val = float(global_score)
        except Exception:
            gs_val = 3.0

        formatted_global_score = (
            f"{gs_val:.2f}".replace(".", ",") if meta_lang == "es" else f"{gs_val:.2f}"
        )
        display_score_str = (
            f"{formatted_global_score} / 5,00"
            if meta_lang == "es"
            else f"{formatted_global_score} / 5.00"
        )

        nodes: List[Any] = []

        return {
            "blueprint_file": blueprint_file,
            "annex_file": annex_file,
            "case_dir": case_dir,
            "modules_dir": modules_dir,
            "blueprint_data": blueprint_data,
            "intel_data": intel_data,
            "tower_meta": tower_meta,
            "meta_lang": meta_lang,
            "vocab": vocab,
            "tower_name": tower_name,
            "tower_id": tower_id,
            "client_name": client_name,
            "version": version,
            "date_str": date_str,
            "currency": currency,
            "is_critical": is_critical,
            "total_fair_ale": total_fair_ale,
            "exact_score": exact_score,
            "exact_band": exact_band,
            "global_score": global_score,
            "global_band": global_band,
            "global_reading": global_reading,
            "gs_val": gs_val,
            "formatted_global_score": formatted_global_score,
            "display_score_str": display_score_str,
        }

    def _build_cover_and_toc(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        vocab = ctx["vocab"]
        gs_val = ctx["gs_val"]
        tower_name = ctx["tower_name"]
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        client_name = ctx["client_name"]
        date_str = ctx["date_str"]
        version = ctx["version"]
        meta_lang = ctx["meta_lang"]
        # 1. Corporate Cover Page
        #
        nodes.append(SpacerNode(points=120))

        # Title and Subtitle
        title_text = vocab.get("title", "Informe de Situación Actual (AS-IS)")
        nodes.append(ParagraphNode(text=title_text, bold=True, space_after=12))
        nodes.append(
            HeadingNode(
                text=f"Anexo Técnico: {tower_name}",
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        nodes.append(SpacerNode(points=120))

        # Client (Project info is removed)
        client_lbl = vocab.get("client_lbl", "Cliente:\n")
        nodes.append(
            ParagraphNode(
                text=f"{client_lbl}{client_name.upper()}", bold=True, space_after=120
            )
        )

        classification_clean = self.classification.replace(" (Tier-1 Assessment)", "")

        # Date and classification
        nodes.append(
            ParagraphNode(
                text=f"{date_str} | Versión {version} | {classification_clean}",
                italic=True,
                text_color_rgb=[150, 150, 150],
            )
        )
        nodes.append(PageBreakNode())

        #
        # CHAPTER 2: INDEX / TABLE OF CONTENTS
        #
        nodes.append(
            HeadingNode(
                text=vocab.get("toc_title", "Contenido"),
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(SpacerNode(points=10))
        
        # Build an elegant, highly polished, static-rendered executive Table of Contents
        if meta_lang == "es":
            nodes.append(ParagraphNode(text="**1. Resumen Ejecutivo** .................................................................................................... **Pág. 3**"))
            nodes.append(ParagraphNode(text="**2. Objetivo, Alcance y Marco Metodológico** ........................................................................ **Pág. 4**"))
            nodes.append(ParagraphNode(text="**3. Evaluación y Madurez Tecnológica** ............................................................................................ **Pág. 5**"))
            nodes.append(ParagraphNode(text="**4. Riesgos** ............................................................................................................ **Pág. 10**"))
            nodes.append(ParagraphNode(text="**Conclusiones y Coste de Inacción** ............................................................................ **Pág. 12**"))
            nodes.append(ParagraphNode(text="**6. Registro de Custodia de Fuentes de Información** .................................................................. **Pág. 14**"))
            nodes.append(ParagraphNode(text="**Metodología Cuantitativa de Riesgos (O-FAIR)** ............................................................................ **Pág. 15**"))
        else:
            nodes.append(ParagraphNode(text="**1. Executive Summary** .................................................................................................... **Pág. 3**"))
            nodes.append(ParagraphNode(text="**2. Objective and Scope of the Assessment** ................................................................................ **Pág. 4**"))
            nodes.append(ParagraphNode(text="**3. Technology Maturity and Evaluation** ............................................................ **Pág. 6**"))
            nodes.append(ParagraphNode(text="**4. Risks** ............................................................................................................ **Pág. 10**"))
            nodes.append(ParagraphNode(text="**Conclusions and Cost of Inaction** ............................................................................ **Pág. 12**"))
            nodes.append(ParagraphNode(text="**6. Custody Register of Information Sources** .......................................................................... **Pág. 14**"))
            nodes.append(ParagraphNode(text="**Quantitative Risk Methodology (O-FAIR)** ............................................................................ **Pág. 15**"))
        
        nodes.append(PageBreakNode())

        #

    def _build_executive_summary_and_scope(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        modules_dir = ctx["modules_dir"]
        meta_lang = ctx["meta_lang"]
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        global_band = ctx["global_band"]
        display_score_str = ctx["display_score_str"]
        global_reading = ctx["global_reading"]
        vocab = ctx["vocab"]
        gs_val = ctx["gs_val"]
        # 3. CHAPTER 1: EXECUTIVE SUMMARY
        #
        resumen_path = modules_dir / "02_resumen_ejecutivo.md"
        if resumen_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(resumen_path))
        else:
            nodes.append(
                HeadingNode(
                    text="1. Resumen Ejecutivo" if meta_lang == "es" else "1. Executive Summary",
                    level=1,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )
            nodes.append(
                ParagraphNode(text="Módulo de resumen ejecutivo no disponible.")
            )

        #
        # CHAPTER 2: ASSESSMENT OBJECTIVE AND SCOPE
        #
        nodes.append(
            HeadingNode(
                text="2. Objetivo, Alcance y Marco Metodológico" if meta_lang == "es" else "2. Objective, Scope, and Methodological Framework",
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        intro_path = modules_dir / "01_introduccion.md"
        if intro_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(intro_path, skip_level_1=True))
        else:
            nodes.append(
                ParagraphNode(text="Módulo de introducción y alcance no disponible.")
            )

        # Section 2.3 (Strategic Business Context) has been symmetrically removed from tower-specific reports, as strategic alignment and traceability registry belong exclusively in the Global Consolidated Report, per Gartner standards.

        #
        # CHAPTER 3: TECHNOLOGICAL DIAGNOSIS AND PLATFORM ANALYSIS
        #
        nodes.append(
            HeadingNode(
                text="3. Diagnóstico Técnico y Análisis Transversal" if meta_lang == "es" else "3. Technical Diagnosis and Cross-Cutting Analysis",
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        # 3.0 Direct Introduction (Consulting-grade synthesis)
        if meta_lang == "es":
            intro_ch3 = "El siguiente diagnóstico técnico desglosa los hallazgos operativos de la plataforma, contraponiendo las capacidades funcionales establecidas frente a las brechas estructurales que limitan el estado objetivo de la organización:"
        else:
            intro_ch3 = "The following technical diagnosis breaks down the operational findings of the platform, contrasting the established functional capabilities against the structural gaps limiting the organization's target state:"
        nodes.append(ParagraphNode(text=intro_ch3))
        nodes.append(SpacerNode(points=10))

        # We completely bypass dumping 03_descripcion_plataforma.md to prevent repetitive walls of text.

        nodes.append(PageBreakNode())

        #
        # CHAPTER 4: MATURITY PROFILE AND GENERAL EVALUATION
        #
        nodes.append(
            HeadingNode(
                text="Evaluación y Madurez Tecnológica" if meta_lang == "es" else "Technology Maturity and Evaluation",
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        # 4.1 Global Dashboard
        nodes.append(
            HeadingNode(
                text=vocab.get("dashboard_title", "Cuadro de Mando de Madurez"),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(
            ParagraphNode(
                text=vocab.get(
                    "dashboard_intro",
                    "La evaluación integral del estado actual consolida una valoración cuantitativa:",
                )
            )
        )

        #
        nodes.append(
            TableNode(
                rows=[
                    TableRowNode(
                        cells=[
                            CellNode(
                                text=vocab.get("score_lbl", "PUNTUACIÓN AS-IS"),
                                bold=True,
                                bg_color="0072BC",
                                text_color_rgb=[255, 255, 255],
                                align="CENTER",
                            ),
                            CellNode(
                                text=vocab.get("maturity_lbl", "NIVEL DE MADUREZ"),
                                bold=True,
                                bg_color="0072BC",
                                text_color_rgb=[255, 255, 255],
                                align="CENTER",
                            ),
                        ],
                        is_header=True,
                    ),
                    TableRowNode(
                        cells=[
                            CellNode(
                                text=display_score_str,
                                bold=True,
                                font_size=16,
                                bg_color="FFF3CD" if gs_val < 3.4 else "D9F2D9",
                                align="CENTER",
                            ),
                            CellNode(
                                text=global_band,
                                bold=True,
                                font_size=12,
                                bg_color="FFF3CD" if gs_val < 3.4 else "D9F2D9",
                                align="CENTER",
                            ),
                        ]
                    ),
                ]
            )
        )
        nodes.append(SpacerNode(points=5))
        nodes.append(
            ParagraphNode(
                text="*Escala de Madurez: 1-Inicial | 2-Repetible | 3-Definido | 4-Gestionado | 5-Optimizado*",
                align="CENTER",
                italic=True,
            )
        )
        nodes.append(SpacerNode(points=10))

        # Read resilience data.
        res_reading = vocab.get("resilience_reading", "Lectura de Resiliencia:")
        nodes.append(ParagraphNode(text=f"**{res_reading}** {global_reading}"))
        nodes.append(SpacerNode(points=15))

        health_title = "Matriz de Diagnóstico y Desempeño por Dominio Tecnológico" if meta_lang == "es" else "Diagnosis and Performance Matrix by Technology Domain"
        nodes.append(
            HeadingNode(
                text=health_title,
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(
            ParagraphNode(
                text="A continuación, se detalla el perfil de desempeño operativo y de gobierno para cada uno de los sub-dominios técnicos evaluados dentro de esta torre:",
                italic=True,
            )
        )
        nodes.append(SpacerNode(points=10))

        health_rows = [
            TableRowNode(
                cells=[
                    CellNode(text="Pilar / Capacidad Tecnológica Evaluada", bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255]),
                    CellNode(text="Score AS-IS", bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                    CellNode(text="Estado y Nivel de Desempeño" if meta_lang == "es" else "Performance State and Level", bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                ],
                is_header=True,
            )
        ]

        for s_idx, p in enumerate(sorted(blueprint_data.get("pillars_analysis", []), key=lambda item: item.get("score", 0.0))):
            bg = self.alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
            p_name = p.get("pilar_name", "Pilar")
            p_score = float(p.get("score", 3.0))
            
            score_formatted = f"{p_score:.2f}".replace(".", ",") if meta_lang == "es" else f"{p_score:.2f}"
            
            # Map score to status and color
            if p_score >= 4.20:
                p_status = "Excelente (A)"
                p_bg_color = "D9F2D9"
            elif p_score >= 3.40:
                p_status = "Estable (B)"
                p_bg_color = "E2F0D9"
            elif p_score >= 2.60:
                p_status = "Estandarizado (C)"
                p_bg_color = "FFF3CD"
            elif p_score >= 1.80:
                p_status = "Básico (D)"
                p_bg_color = "FCE4D6"
            else:
                p_status = "Crítico (F)"
                p_bg_color = "F2D9D9"

            health_rows.append(
                TableRowNode(
                    cells=[
                        CellNode(text=p_name, bold=True, bg_color=self.alt_row_hex),
                        CellNode(text=score_formatted, bg_color=bg, align="CENTER"),
                        CellNode(text=p_status, bold=True, bg_color=p_bg_color, align="CENTER"),
                    ]
                )
            )

        nodes.append(TableNode(rows=health_rows))
        nodes.append(SpacerNode(points=15))


    def _build_systemic_risk_section(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        meta_lang = ctx["meta_lang"]
        modules_dir = ctx["modules_dir"]
        intel_data = ctx["intel_data"]
        tower_id = ctx["tower_id"]
        transversal_title = "Análisis Transversal de Deuda Tecnológica y Patrones de Riesgo Estructural" if meta_lang == "es" else "Cross-Cutting Analysis of Technological Debt and Structural Risk Patterns"
        nodes.append(HeadingNode(text=transversal_title, level=2, primary_color_rgb=self.primary_color_rgb))
        trans_path = modules_dir / "05_transversal.md"
        if trans_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(trans_path, skip_level_1=True))
        nodes.append(SpacerNode(points=20))

        # 3.5 Systemic Risk Indicators and Decision Context (MCDA + Monte Carlo + LCBN)
        if intel_data:
            try:
                overrides = intel_data.get("tower_overrides", {}).get(tower_id, {})
                metrics = overrides.get("metrics", {}) if isinstance(overrides, dict) else {}
                business_criticality = metrics.get("business_criticality") if isinstance(metrics, dict) else None
                regulatory_compliance = metrics.get("regulatory_compliance") if isinstance(metrics, dict) else None
                implementation_feasibility = metrics.get("implementation_feasibility") if isinstance(metrics, dict) else None
                
                sensitivity = overrides.get("sensitivity_analysis", {}) if isinstance(overrides, dict) else {}
                dii_03 = None
                if isinstance(sensitivity, dict):
                    dii_03 = sensitivity.get("decision_instability_indices", {}).get("dii_threshold_03_pct")
                
                epistemic = intel_data.get("epistemic_graph", {}) if isinstance(intel_data, dict) else {}
                audits = epistemic.get("audits", {}) if isinstance(epistemic, dict) else {}
                erc_dict = audits.get("eigenvector_risk_centrality", {}) if isinstance(audits, dict) else {}
                erc = erc_dict.get(tower_id) if isinstance(erc_dict, dict) else None
                
                spof_by_cascade = audits.get("single_point_of_failure_by_cascade", "") if isinstance(audits, dict) else ""
                spof_by_centrality = audits.get("single_point_of_failure_by_centrality", "") if isinstance(audits, dict) else ""
                
                if business_criticality is not None:
                    # Add heading for Systemic Risk Metrics
                    nodes.append(
                        HeadingNode(
                            text="Análisis de Interdependencias Tecnológicas y Negocio" if meta_lang == "es" else "Technology and Business Interdependence Analysis",
                            level=2,
                            primary_color_rgb=self.primary_color_rgb,
                        )
                    )
                    
                    if meta_lang == "es":
                        intro_text_inter = (
                            "La infraestructura tecnológica no opera de manera aislada; un evento en un dominio específico puede "
                            "propagar riesgos y afectar la continuidad de los servicios de negocio de forma inmediata. Por ello, "
                            "esta sección conecta el diagnóstico técnico de la plataforma con su impacto estratégico real. Para lograrlo, "
                            "el motor de evaluación analiza de forma integrada tres dimensiones clave:"
                        )
                    else:
                        intro_text_inter = (
                            "Technology infrastructure does not operate in isolation; an event in a specific domain can propagate "
                            "risks and immediately impact business service continuity. Therefore, this section connects the technical "
                            "diagnosis of the platform with its real strategic impact. To achieve this, the evaluation engine integrates "
                            "three key dimensions:"
                        )

                    nodes.append(ParagraphNode(text=intro_text_inter))
                    
                    # Add three clear bullet points in AST
                    if meta_lang == "es":
                        nodes.append(ParagraphNode(text="Criticidad Operativa y Presión Regulatoria: Determina el nivel de dependencia directa de los procesos de negocio y la exigencia de conformidad legal y normativa (v.g. NIS2, DORA o ISO 27001) sobre este dominio.", style="List Bullet"))
                        nodes.append(ParagraphNode(text="Viabilidad de la Transformación: Estima la complejidad técnica y facilidad operativa para ejecutar los proyectos del plan de acción propuesto.", style="List Bullet"))
                        nodes.append(ParagraphNode(text="Propagación Topológica y SPOF: Cuantifica el riesgo de que un incidente crítico se propague en cascada a otras torres y determina si el dominio actúa como un Punto Único de Fallo.", style="List Bullet"))
                        
                        concl_text = "Estos indicadores proporcionan un contexto de decisión cuantitativo y objetivo, permitiendo priorizar las inversiones de transformación en base a su retorno estratégico y resiliencia para la organización:"
                    else:
                        nodes.append(ParagraphNode(text="Operational Criticality and Regulatory Pressure: Assesses the level of direct business process dependency and legal compliance requirements (e.g., NIS2, DORA, or ISO 27001) on this domain.", style="List Bullet"))
                        nodes.append(ParagraphNode(text="Transformation Feasibility: Estimates the technical complexity and operational ease of executing the projects in the proposed action plan.", style="List Bullet"))
                        nodes.append(ParagraphNode(text="Topological Propagation and SPOF: Quantifies the risk of critical incident cascade propagation to other towers and determines if the domain acts as a Single Point of Failure.", style="List Bullet"))
                        
                        concl_text = "These indicators provide an objective, quantitative decision context, allowing strategic investments to be prioritized based on transformation viability and overall resilience:"

                    nodes.append(ParagraphNode(text=concl_text))
                    nodes.append(SpacerNode(points=10))

                    # Build the metrics table
                    spof_status = "SÍ" if (tower_id == spof_by_cascade or tower_id == spof_by_centrality) else "NO"
                    dii_val = f"{dii_03:.1f}%" if dii_03 is not None else "0,0%"
                    erc_val = f"{erc:.3f}" if erc is not None else "0,000"
                    
                    nodes.append(
                        TableNode(
                            rows=[
                                TableRowNode(
                                    cells=[
                                        CellNode(text="Indicador Estratégico", bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255]),
                                        CellNode(text="Valor / Score", bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                                        CellNode(text="Estado y Clasificación", bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                                    ],
                                    is_header=True,
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text="Criticidad de Negocio (MCDA)"),
                                        CellNode(text=f"{business_criticality:.1f}%", align="CENTER"),
                                        CellNode(text="Extrema (Pilar Crítico)" if business_criticality >= 80.0 else "Alta" if business_criticality >= 50.0 else "Media", align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text="Presión Regulatoria (MCDA)"),
                                        CellNode(text=f"{regulatory_compliance:.1f}%", align="CENTER"),
                                        CellNode(text="Crítica (Regulación Estricta)" if regulatory_compliance >= 80.0 else "Alta" if regulatory_compliance >= 50.0 else "Estándar", align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text="Viabilidad Operativa (MCDA)"),
                                        CellNode(text=f"{implementation_feasibility:.1f}%", align="CENTER"),
                                        CellNode(text="Viable" if implementation_feasibility >= 60.0 else "Complejo (Requiere mitigación)", align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text="Consistencia del Diagnóstico (DII)"),
                                        CellNode(text=dii_val, align="CENTER"),
                                        CellNode(text="Estable (Diagnóstico Robusto)" if (dii_03 or 0) < 15.0 else "Moderado" if (dii_03 or 0) < 30.0 else "Sensible", align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text="Propagación de Fallos en Cascada (ERC)"),
                                        CellNode(text=erc_val, align="CENTER"),
                                        CellNode(text="Alta Influencia" if (erc or 0) >= 0.50 else "Media" if (erc or 0) >= 0.20 else "Baja/Aislada", align="CENTER"),
                                    ]
                                ),
                                TableRowNode(
                                    cells=[
                                        CellNode(text="Punto Único de Fallo (SPOF)"),
                                        CellNode(text=spof_status, bold=True, align="CENTER", bg_color="F2D9D9" if spof_status == "SÍ" else "D9F2D9"),
                                        CellNode(text="Cuello de Botella Estructural" if spof_status == "SÍ" else "Estable en Red Causal", align="CENTER"),
                                    ]
                                ),
                            ]
                        )
                    )
                    nodes.append(SpacerNode(points=10))

                    # Add Glossary / Legend
                    nodes.append(ParagraphNode(text="**Análisis Ejecutivo de Indicadores de Interdependencia:**", bold=True))
                    
                    nodes.append(_build_criticality_bullet(business_criticality))
                    nodes.append(_build_regulatory_bullet(regulatory_compliance))
                    nodes.append(_build_feasibility_bullet(implementation_feasibility))
                    dii_pct = dii_03 if dii_03 is not None else 0.0
                    nodes.append(_build_dii_bullet(dii_pct))
                    erc_val_num = erc if erc is not None else 0.0
                    nodes.append(_build_erc_bullet(erc_val_num))
                    nodes.append(_build_spof_bullet(spof_status))
                    nodes.append(SpacerNode(points=20))
            except Exception as e:
                logger.info(f"⚠️ Error injecting systemic risk metrics in AST Bridge: {e}")


    def _build_maturity_and_benchmarks(self, ctx: dict[str, Any], nodes: List[Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        vocab = ctx["vocab"]
        gs_val = ctx["gs_val"]
        case_dir = ctx["case_dir"]
        tower_id = ctx["tower_id"]
        modules_dir = ctx["modules_dir"]
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        total_fair_ale = ctx["total_fair_ale"]
        currency = ctx["currency"]
        client_name = ctx["client_name"]
        meta_lang = ctx["meta_lang"]
        # 4.2 Radar Chart
        nodes.append(
            HeadingNode(
                text=vocab.get("radar_title", "Análisis Comparativo de Madurez por Pilar"),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        radar_path = case_dir / "pillar_radar_chart.generated.png"
        if radar_path.exists():
            nodes.append(PictureNode(path=str(radar_path), width_inches=6.0))
            nodes.append(SpacerNode(points=15))

        # RAGE Forensic Verification Injection
        snapshot_file = case_dir / "benchmarks_snapshot.json"
        if snapshot_file.exists():
            try:
                with open(snapshot_file, "r", encoding="utf-8-sig") as sf:
                    snap_data = json.load(sf)
                snapshots = snap_data.get("snapshots", {})
                if snapshots:
                    # Silent Drop: Filter and find valid, verified benchmarks for the current tower
                    valid_snapshots = []
                    for t_id, t_snap in sorted(snapshots.items()):
                        if t_id != tower_id:
                            continue
                        verif_status = t_snap.get("verification_status", "failed")
                        quote = t_snap.get("evidence_quote", "")
                        if verif_status == "verified" and quote and "no se encontraron" not in quote.lower() and "no se ha encontrado" not in quote.lower():
                            valid_snapshots.append((t_id, t_snap))

                    if valid_snapshots:
                        nodes.append(
                            HeadingNode(
                                text="Justificación de Estándares Sectoriales (Trazabilidad RAGE)",
                                level=2,
                                primary_color_rgb=self.primary_color_rgb,
                            )
                        )
                        intro_text = (
                            "Los estándares de mercado del gráfico radial anterior se han calibrado y verificado en tiempo "
                            "de ejecución mediante el motor RAGE (Runtime Agentic Grounding & Evaluation). Cada benchmark "
                            "está respaldado por evidencias factoperativas y copias de seguridad de documentos oficiales:"
                        )
                        nodes.append(ParagraphNode(text=intro_text))
                        nodes.append(SpacerNode(points=10))

                        for t_id, t_snap in valid_snapshots:
                            framework_name = t_snap.get(
                                "framework_name", "Estándar Sectorial"
                            )
                            score = t_snap.get("dynamic_score", 4.0)
                            quote = t_snap.get("evidence_quote", "")
                            url = t_snap.get("evidence_source_url", "")
                            local_path = t_snap.get("local_snapshot_path", "")

                            header_p = f"**Torre {t_id} ({framework_name}) - Estándar: {score:,.1f}**"
                            nodes.append(ParagraphNode(text=header_p))

                            quote_p = f'*✓ Evidencia extraída:* "{quote}"'
                            nodes.append(ParagraphNode(text=quote_p))

                            source_p = f"*Referencia:* {url}"
                            if local_path:
                                    source_p += f" | *Bóveda local:* `{local_path}`"
                            nodes.append(ParagraphNode(text=source_p))
                            nodes.append(SpacerNode(points=10))
            except Exception as ex:
                logger.info(f"⚠️  [RAGE] Failed to inject RAGE report into AST: {ex}")

        # 4.3 Score Justification Matrix (from CSV) with fallback mechanism
        csv_mat_path = modules_dir / "04_matriz_madurez.csv"
        if csv_mat_path.exists():
            # Ensure header collections are not empty to prevent the generation of malformed tables.
            mat_headers = vocab.get("justification_table_headers") or [
                "Pilar / Capacidad Tecnológica Evaluada",
                "Score AS-IS",
                "Análisis de Brechas y Calibración del Diagnóstico",
            ]
            nodes.append(self._parse_csv_generic(csv_mat_path, mat_headers))

        nodes.append(PageBreakNode())

        #
        # CHAPTER 4: QUANTITATIVE RISK MATRIX (O-FAIR)
        #
        nodes.append(
            HeadingNode(
                text="4. Exposición Financiera al Riesgo y Resiliencia Operativa" if meta_lang == "es" else "4. Financial Risk Exposure and Operational Resilience",
                level=1,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        # Build a lookup map from blueprint payload findings for detailed FAIR metrics
        fair_lookup = {}
        try:
            for pillar in blueprint_data.get("pillars_analysis", []):
                for hc in pillar.get("health_check_asis", []):
                    cap_name = hc.get("capability")
                    if cap_name:
                        fair_lookup[cap_name] = {
                            "p90": hc.get("fair_p90_score", 0.0),
                            "min": hc.get("fair_min_score", 0.0),
                            "max": hc.get("fair_max_score", 0.0),
                        }
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")

        # Read the CSV risks first so we have the data for the executive overview
        csv_risks_path = modules_dir / "06_matriz_riesgos_fair.csv"
        risks_data_list = []
        if csv_risks_path.exists():
            try:
                with open(csv_risks_path, "r", encoding="utf-8-sig") as cf:
                    reader = csv.reader(cf, delimiter=";")
                    next(reader)
                    for r_idx, row_data in enumerate(reader):
                        if not row_data or len(row_data) < 6:
                            continue
                        pilar_full_name = row_data[0].split(" - ")[0]
                        finding_raw = row_data[1]
                        finding_parts = finding_raw.split("\n\nEvidencia Forense Literal (Audit RAG):\n")
                        finding = finding_parts[0]
                        evidence = finding_parts[1].strip('"') if len(finding_parts) > 1 else ""

                        r_item = {
                            "id": f"RVS{r_idx + 1:02d}",
                            "pilar": pilar_full_name,
                            "capability": row_data[0].split(" - ")[1]
                            if " - " in row_data[0]
                            else row_data[0],
                            "finding": finding,
                            "evidence": evidence,
                            "business_risk": row_data[2],
                            "tef": float(row_data[3]),
                            "lm": float(row_data[4]),
                            "ale": float(row_data[5]),
                        }
                        risks_data_list.append(r_item)
            except (OSError, ValueError, KeyError, AttributeError) as ex:

                logger.debug(f"[Fallback] Excepción controlada: {ex}")

        from assessment_engine.infrastructure.localization import (
            format_number,
        )

        formatted_ale = format_number(
            total_fair_ale, locale=meta_lang, decimals=0
        )

        # Build executive risks summary paragraph
        if risks_data_list and total_fair_ale > 0:
            pilar_sums = {}
            for r in risks_data_list:
                p_name = r["pilar"]
                pilar_sums[p_name] = pilar_sums.get(p_name, 0.0) + r["ale"]
            highest_pilar = max(pilar_sums, key=pilar_sums.get)
            highest_pilar_val = pilar_sums[highest_pilar]
            
            highest_risk = max(risks_data_list, key=lambda x: x["ale"])
            highest_risk_id = highest_risk["id"]
            highest_risk_cap = highest_risk["capability"]
            highest_risk_ale = highest_risk["ale"]
            highest_risk_pct = (highest_risk_ale / total_fair_ale) * 100.0 if total_fair_ale > 0 else 0.0
            
            # Format sub-amounts
            formatted_pilar_ale = format_number(
                highest_pilar_val, locale=meta_lang, decimals=0
            )
            formatted_risk_ale = format_number(
                highest_risk_ale, locale=meta_lang, decimals=0
            )
            
            executive_risk_summary = (
                f"**Resumen Ejecutivo de Exposición al Riesgo (FAIR):**\n"
                f"El análisis cuantitativo de riesgos de la plataforma de la torre identifica una exposición financiera agregada (Expectativa de Pérdida Anualizada - ALE) de **{formatted_ale} {currency}**. "
                f"Esta cifra representa el impacto económico estimado al que se enfrenta **{client_name}** de forma anualizada debido a ineficiencias de continuidad, dependencias de soporte manual y vulnerabilidades operativas no mitigadas exclusivamente dentro de este perímetro tecnológico.\n\n"
                f"De los **{len(risks_data_list)}** riesgos registrados, la mayor concentración de pérdidas se localiza en el pilar de **{highest_pilar}** (con una exposición de **{formatted_pilar_ale} {currency}**), impulsada principalmente por la inmadurez en **{highest_risk_cap}** (Riesgo **{highest_risk_id}** con **{formatted_risk_ale} {currency}**), la cual acumula por sí sola el **{highest_risk_pct:.1f}%** de la exposición global de la torre."
            )
        else:
            executive_risk_summary = (
                f"**Resumen Ejecutivo de Exposición al Riesgo (FAIR):**\n"
                f"La evaluación de riesgos financieros mediante simulación probabilística estima una exposición anualizada al riesgo de **{formatted_ale} {currency}** para **{client_name}**. "
                f"Esta cifra representa el impacto económico potencial por ineficiencias o brechas operativas detectadas exclusivamente en el perímetro de esta torre."
            )

        nodes.append(ParagraphNode(text=executive_risk_summary))

        # Insert an inline executive methodological note referencing Appendix D.
        nodes.append(
            ParagraphNode(
                text="**Nota Metodológica:** Para garantizar el máximo rigor directivo, la estimación del riesgo anualizado proyectado (ALE) y la priorización de vulnerabilidades técnicas en este informe se basan estrictamente en el estándar internacional **O-FAIR** y en simulaciones actuariales probabilísticas de Monte Carlo. Esto permite cuantificar con transparencia la exposición al riesgo en términos financieros reales del negocio. La explicación técnica, parámetros de calibración de pérdidas y las fórmulas estadísticas aplicadas se detallan en el **Apéndice D** de este reporte.",
                italic=True,
                space_after=12,
            )
        )

        return risks_data_list, fair_lookup

    def _build_fair_risk_analysis(self, ctx: dict[str, Any], nodes: List[Any], risks_data_list: list[dict[str, Any]]) -> None:
        if not risks_data_list:
            return

        vocab = ctx["vocab"]
        meta_lang = ctx["meta_lang"]
        currency = ctx["currency"]
        is_critical = ctx["is_critical"]

        # 5.1 Generate 5x5 Heatmap (Word-native mosaic)
        nodes.append(
            HeadingNode(
                text=vocab.get(
                    "exposure_summary_title",
                    "Exposición financiera y Mapa de Calor de Riesgo",
                ),
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(_build_heatmap_mosaic(risks_data_list))
        nodes.append(SpacerNode(points=15))

        # 5.2 Methodological Legends (TEF & LM Scales)
        nodes.append(
            HeadingNode(
                text="Leyendas Metodológicas",
                level=3,
                primary_color_rgb=self.primary_color_rgb,
            )
        )

        nodes.append(
            HeadingNode(
                text=vocab.get(
                    "tef_title", "Criterios de Frecuencia de la Amenaza (TEF)"
                ),
                level=4,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(_build_tef_scale_table(vocab, meta_lang, self.alt_row_hex))
        nodes.append(SpacerNode(points=15))

        nodes.append(
            HeadingNode(
                text=vocab.get("lm_title", "Criterios de Magnitud de Pérdidas (LM)"),
                level=4,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        nodes.append(_build_lm_scale_table(vocab, meta_lang, currency, is_critical, self.alt_row_hex))
        nodes.append(SpacerNode(points=10))

        if is_critical:
            nodes.append(
                ParagraphNode(
                    text="*Nota de Calibración de Sector:* Este rango de pérdidas (LM 5) está estrictamente alineado con el estudio de referencia mundial **ITIC Global Server Hardware Downtime Report**, el cual determina que para el 98% de los operadores de infraestructuras críticas y grandes corporaciones, el coste de una sola hora de indisponibilidad de sistemas core supera el millón de euros debido a la interrupción de procesos, penalizaciones por acuerdos de nivel de servicio (SLA) y remediación forense urgente.",
                    italic=True,
                    space_after=12,
                )
            )
            nodes.append(SpacerNode(points=10))
        else:
            nodes.append(SpacerNode(points=10))


    def _build_detailed_findings_log(self, ctx: dict[str, Any], nodes: List[Any], risks_data_list: list[dict[str, Any]], fair_lookup: dict[str, Any]) -> None:
        vocab = ctx["vocab"]
        gs_val = ctx["gs_val"]
        currency = ctx["currency"]
        meta_lang = ctx["meta_lang"]
        # 5.3 Detailed Log Segmented by Domain (in multiple independent tables)
        if risks_data_list:
            nodes.append(
                HeadingNode(
                    text=vocab.get(
                        "detailed_risks_title",
                        "Registro Detallado de Hallazgos Forenses",
                    ),
                    level=2,
                    primary_color_rgb=self.primary_color_rgb,
                )
            )

            # Group risks by pillar.
            risks_by_pilar = {}
            for r in risks_data_list:
                p_name = r["pilar"]
                if p_name not in risks_by_pilar:
                    risks_by_pilar[p_name] = []
                risks_by_pilar[p_name].append(r)

            for p_name, pilar_risks in risks_by_pilar.items():
                # Display all identified technical risks for full analytical completeness
                pilar_risks_filtered = pilar_risks
                if not pilar_risks_filtered:
                    continue

                pilar_header = (
                    vocab.get(
                        "detailed_risks_pilar_title", "Análisis de Vulnerabilidades: "
                    )
                    + p_name
                )
                nodes.append(
                    HeadingNode(
                        text=pilar_header,
                        level=3,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )

                headers_table = vocab.get("detailed_risks_headers") or [
                    "ID",
                    "Vulnerabilidad y Evidencias",
                    "Exposición y Riesgo",
                ]
                risk_rows = [
                    TableRowNode(
                        cells=[
                            CellNode(
                                text=h,
                                bold=True,
                                bg_color="0072BC",
                                text_color_rgb=[255, 255, 255],
                                align="CENTER",
                            )
                            for h in headers_table
                        ],
                        is_header=True,
                    )
                ]

                for s_idx, hc in enumerate(pilar_risks_filtered):
                    bg = self.alt_row_hex if s_idx % 2 == 1 else "FFFFFF"

                    # Deduplicate or clean up repetitive prose between finding and evidence to improve readability
                    find_clean = (hc['finding'] or "").strip()
                    ev_clean = (hc.get("evidence") or "").strip()
                    
                    # Heuristic check for high redundancy: prefix/suffix overlap or substring
                    is_redundant = False
                    if ev_clean and find_clean:
                        ev_lower = ev_clean.lower()
                        find_lower = find_clean.lower()
                        if ev_lower in find_lower or find_lower in ev_lower:
                            is_redundant = True
                        elif ev_clean[:35].lower() == find_clean[:35].lower() or ev_clean[-35:].lower() == find_clean[-35:].lower():
                            is_redundant = True

                    from assessment_engine.infrastructure.localization import (
                        apply_vocabulary_substitutions,
                        format_number,
                    )

                    desc_raw = (
                        f"**Vulnerabilidad Identificada:**\n{find_clean}\n\n"
                        f"**Impacto de TI / Operativo:**\n{hc['business_risk']}"
                    )
                    desc_text = apply_vocabulary_substitutions(
                        desc_raw, locale=meta_lang
                    )

                    #
                    tef = hc["tef"]
                    lm = hc["lm"]
                    ale = hc["ale"]
                    cap_name = hc["capability"]

                    # Fetch detailed FAIR metrics from lookup map
                    fair_metrics = fair_lookup.get(cap_name, {})
                    p90_val = fair_metrics.get("p90", 0.0) or 0.0
                    min_val = fair_metrics.get("min", 0.0) or 0.0
                    max_val = fair_metrics.get("max", 0.0) or 0.0

                    formatted_p90 = format_number(
                        p90_val, locale=meta_lang, decimals=0
                    )
                    formatted_min = format_number(
                        min_val, locale=meta_lang, decimals=0
                    )
                    formatted_max = format_number(
                        max_val, locale=meta_lang, decimals=0
                    )
                    formatted_ale_item = format_number(
                        ale, locale=meta_lang, decimals=0
                    )

                    calc_txt = "N/A"
                    bg_severe = bg
                    if ale and ale > 0:
                        calc_txt = (
                            f"**Exposición Cuantitativa (FAIR):**\n"
                            f"• Frecuencia (TEF): {tef:.1f} / 5,0\n"
                            f"• Magnitud (LM): {lm:.1f} / 5,0\n\n"
                            f"**Exposición Financiera Proyectada:**\n"
                            f"• Pérdida Anualizada (ALE): **{formatted_ale_item} {currency}**\n"
                            f"• Peor Caso (P90): {formatted_p90} {currency}\n"
                            f"• Rango Probabilístico: {formatted_min} {currency} a {formatted_max} {currency}"
                        )

                        risk_score = tef * lm
                        if risk_score >= 15 or ale >= 1000000:
                            bg_severe = "F8D7DA"  # Light Red
                        elif risk_score >= 10 or ale >= 250000:
                            bg_severe = "FFF3CD"  # Light Amber
                        elif risk_score >= 5 or ale >= 50000:
                            bg_severe = "E2E3E5"  # Light Gray

                    risk_rows.append(
                        TableRowNode(
                            cells=[
                                CellNode(
                                    text=hc["id"],
                                    bold=True,
                                    bg_color=self.alt_row_hex,
                                    align="CENTER",
                                ),
                                CellNode(text=desc_text, bg_color=bg, align="JUSTIFY"),
                                CellNode(
                                    text=calc_txt,
                                    bold=True,
                                    bg_color=bg_severe,
                                    align="RIGHT",
                                ),
                            ]
                        )
                    )

                nodes.append(TableNode(rows=risk_rows))

        nodes.append(PageBreakNode())

        #
        # CHAPTER 5: CONCLUSIONS AND COST OF INACTION
        #

    def _build_conclusions_and_appendices(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        self._build_conclusions_chapter(ctx, nodes)
        nodes.append(PageBreakNode())
        _build_appendix_a_glossary_fn(ctx, nodes, self.primary_color_rgb)
        _build_appendix_b_disclaimer_fn(ctx, nodes, self.primary_color_rgb)
        _build_appendix_c_custody_fn(ctx, nodes, self.primary_color_rgb)
        _build_appendix_d_methodology_fn(
            ctx, nodes, self.primary_color_rgb, self.brand_data, self.alt_row_hex
        )

    def _build_conclusions_chapter(self, ctx: dict[str, Any], nodes: List[Any]) -> None:
        blueprint_data = ctx["blueprint_data"]
        client_name = ctx["client_name"]
        modules_dir = ctx["modules_dir"]
        # 5.1 Transformation Paradigm (Promoted here from Chapter 4 as it represents a TO-BE vision)
        nodes.append(
            HeadingNode(
                text="El Paradigma de Transformación: Platform as a Product",
                level=2,
                primary_color_rgb=self.primary_color_rgb,
            )
        )
        cca_data = blueprint_data.get("cross_capabilities_analysis", {}) if isinstance(blueprint_data, dict) else {}
        paradigm_text = cca_data.get("transformation_paradigm", "No definido.") if isinstance(cca_data, dict) else "No definido."
        nodes.append(ParagraphNode(text=paradigm_text, italic=True))
        nodes.append(SpacerNode(points=15))

        # 5.2 Next Steps and Impact of Inaction
        concl_path = modules_dir / "07_conclusiones.md"
        if concl_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(concl_path))

        #

    def _parse_markdown_to_nodes(
        self, md_path: Path, skip_level_1: bool = False
    ) -> List[Any]:
        """Parses a Markdown file, converting its content into a sequence of Abstract Syntax Tree (AST) nodes."""
        nodes = []
        if not md_path.exists():
            return nodes

        with open(md_path, "r", encoding="utf-8") as f:
            lines = [html.unescape(line) for line in f.readlines()]

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            # Sanitization: Replace non-standard vocabulary with canonical terms
            from assessment_engine.infrastructure.localization import (
                apply_vocabulary_substitutions,
            )

            if isinstance(cleaned, str):
                cleaned = apply_vocabulary_substitutions(
                    cleaned, locale=getattr(self, "meta_lang", "es")
                )

            # Exclude special markers for table and mosaic directives from the content processing stream.
            if (
                "--- TABLA COMPARATIVA" in cleaned
                or "FORTALEZAS_CLAVE:" in cleaned
                or "BRECHAS_CLAVE:" in cleaned
                or "--- FIN TABLA" in cleaned
            ):
                continue

            #
            if cleaned.startswith("# "):
                if not skip_level_1:
                    nodes.append(
                        HeadingNode(
                            text=cleaned[2:],
                            level=1,
                            primary_color_rgb=self.primary_color_rgb,
                        )
                    )
            elif cleaned.startswith("## "):
                nodes.append(
                    HeadingNode(
                        text=cleaned[3:],
                        level=2,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )
            elif cleaned.startswith("### "):
                nodes.append(
                    HeadingNode(
                        text=cleaned[4:],
                        level=3,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )
            elif cleaned.startswith("#### "):
                nodes.append(
                    HeadingNode(
                        text=cleaned[5:],
                        level=4,
                        primary_color_rgb=self.primary_color_rgb,
                    )
                )
            #
            elif cleaned.startswith("* ") or cleaned.startswith("- "):
                nodes.append(
                    ParagraphNode(text=cleaned[2:], style="List Bullet", space_after=6)
                )
            #
            elif cleaned.startswith("> "):
                nodes.append(
                    ParagraphNode(text=cleaned[2:], italic=True, space_after=12)
                )
            #
            else:
                nodes.append(ParagraphNode(text=cleaned, space_after=8))

        return nodes

    def _extract_key_bullets_from_md(
        self, md_path: Path, section_marker: str
    ) -> List[str]:
        """Parses the conclusions file to extract identified strengths and weaknesses, structuring them for inclusion in the SWOT analysis table."""
        if not md_path.exists():
            return []
        with open(md_path, "r", encoding="utf-8") as f:
            lines = [html.unescape(line) for line in f.readlines()]
        bullets = []
        recording = False
        for line in lines:
            cleaned = line.strip()
            if section_marker in cleaned:
                recording = True
                continue
            if recording:
                if (
                    cleaned.startswith("BRECHAS_CLAVE:")
                    or cleaned.startswith("FORTALEZAS_CLAVE:")
                    or "--- FIN TABLA" in cleaned
                ):
                    break
                if cleaned.startswith("* ") or cleaned.startswith("- "):
                    bullets.append(cleaned[2:])
        return bullets

    def _parse_csv_generic(self, csv_path: Path, headers: List[str]) -> TableNode:
        rows = []
        #
        rows.append(
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
        )

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)  #
            for r_idx, row_data in enumerate(reader):
                if not row_data:
                    continue
                bg = self.alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
                cells = []
                for c_idx, val in enumerate(row_data):
                    bold = c_idx == 0
                    align = (
                        "CENTER"
                        if c_idx == 1
                        else ("JUSTIFY" if c_idx == 2 else "LEFT")
                    )
                    
                    val_str = str(val)
                    if isinstance(val_str, str):
                        from assessment_engine.infrastructure.localization import (
                            apply_vocabulary_substitutions,
                        )

                        val_str = apply_vocabulary_substitutions(
                            val_str, locale=getattr(self, "meta_lang", "es")
                        )

                    if c_idx == 2:
                        val_str = re.sub(
                            r"\*\*Justificación de la Nota\s*\(\d+[,.]\d+\):\*\*",
                            "**Justificación de la Nota:**",
                            val_str
                        )
                        val_str = re.sub(
                            r"Justificación de la Nota\s*\(\d+[,.]\d+\):",
                            "Justificación de la Nota:",
                            val_str
                        )
                        
                    cells.append(
                        CellNode(text=val_str, bold=bold, bg_color=bg, align=align)
                    )
                rows.append(TableRowNode(cells=cells))

        return TableNode(rows=rows)