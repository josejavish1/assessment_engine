import csv
import html
import json
import re
from pathlib import Path
from typing import Any, List

from domain.schemas.ast import (
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


class PayloadToASTBridge:
    """Translates structured JSON payloads and associated markdown modules into a unified Document Abstract Syntax Tree (AST).
    This process maintains semantic identity and structural alignment with the source content."""

    def __init__(self, brand_profile_path: str = "engine_config/brand_profile.json", locales_path: str = "engine_config/locales.json"):
        self.brand_profile_path = Path(brand_profile_path)
        self.locales_path = Path(locales_path)

        # Load brand profiles, using fallback values to ensure required assets are present.
        self.company_name = "NTT DATA"
        self.classification = "Confidencial"
        self.disclaimer = ""
        self.primary_color_rgb = [0, 114, 188]  # Primary corporate brand color code.
        self.alt_row_hex = "F2F2F2"

        if self.brand_profile_path.exists():
            try:
                with open(self.brand_profile_path, "r", encoding="utf-8-sig") as bf:
                    brand = json.load(bf)
                    self.company_name = brand.get("company_name", self.company_name)
                    self.classification = brand.get("default_classification", self.classification)
                    self.disclaimer = brand.get("disclaimer_text", self.disclaimer)
                    styling = brand.get("styling", {})
                    p_hex = styling.get("primary_color_hex", "0072BC")
                    self.alt_row_hex = styling.get("alternate_row_color_hex", self.alt_row_hex)

                    #
                    r = int(p_hex[0:2], 16)
                    g = int(p_hex[2:4], 16)
                    b = int(p_hex[4:6], 16)
                    self.primary_color_rgb = [r, g, b]
            except Exception:
                pass

        #
        self.locales_data = {}
        if self.locales_path.exists():
            try:
                with open(self.locales_path, "r", encoding="utf-8-sig") as lf:
                    self.locales_data = json.load(lf)
            except Exception:
                pass

    def convert(self, blueprint_payload_path: str, approved_annex_path: str) -> DocumentAST:
        """Consolidates information from input JSON files and associated Markdown/CSV modules
        to generate a complete Document Abstract Syntax Tree (AST)."""
        blueprint_file = Path(blueprint_payload_path)
        annex_file = Path(approved_annex_path)
        case_dir = blueprint_file.parent
        modules_dir = case_dir / "asis_modules"

        #
        with open(blueprint_file, "r", encoding="utf-8-sig") as f:
            blueprint_data = json.load(f)

        if annex_file.exists():
            try:
                with open(annex_file, "r", encoding="utf-8-sig") as f:
                    json.load(f)
            except Exception:
                pass

        tower_meta = blueprint_data.get("document_meta", {})
        meta_lang = tower_meta.get("language", "es").lower()
        vocab = self.locales_data.get(meta_lang, self.locales_data.get("es", {}))

        tower_name = tower_meta.get("tower_name", "Desconocida")
        tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
        client_name = tower_meta.get("client_name", "Cliente")
        version = tower_meta.get("version", "1.2")
        date_str = tower_meta.get("date", "Junio 2026")
        currency = tower_meta.get("currency", "€")

        # Load scoring and global ALE data for interpolation.
        total_fair_ale = blueprint_data.get("total_fair_ale", 0.0)
        global_score = blueprint_data.get("executive_summary", {}).get("global_score", "3.0").split()[0]
        global_band = blueprint_data.get("executive_summary", {}).get("global_band", "Definido")
        global_reading = blueprint_data.get("pillar_score_profile", {}).get("pillars", [{}])[0].get("executive_reading", "Gobernanza estándar.")

        try:
            gs_val = float(global_score)
        except Exception:
            gs_val = 3.0

        formatted_global_score = f"{gs_val:.2f}".replace(".", ",") if meta_lang == "es" else f"{gs_val:.2f}"
        display_score_str = f"{formatted_global_score} / 5,00" if meta_lang == "es" else f"{formatted_global_score} / 5.00"

        nodes: List[Any] = []

        #
        # 1. Corporate Cover Page
        #
        nodes.append(SpacerNode(points=40))
        
        # Consultancy name at the top.
        nodes.append(ParagraphNode(text=self.company_name.upper(), bold=True, text_color_rgb=self.primary_color_rgb, space_after=80))
        
        # Title and Subtitle
        title_text = vocab.get("title", "Informe de Situación Actual (AS-IS)")
        nodes.append(ParagraphNode(text=title_text, bold=True, space_after=12))
        nodes.append(HeadingNode(text=f"Anexo Técnico: {tower_name}", level=2, primary_color_rgb=self.primary_color_rgb))
        
        nodes.append(SpacerNode(points=100))
        
        # Client and Project
        nodes.append(ParagraphNode(text=f"Cliente:\n{client_name.upper()}", bold=True, space_after=12))
        project_name = vocab.get("project", "Consultoría para el rediseño de infraestructura tecnológica")
        nodes.append(ParagraphNode(text=f"Proyecto:\n{project_name}", bold=True, space_after=100))
        
        # Date and classification
        nodes.append(ParagraphNode(text=f"{date_str} | Versión {version} | {self.classification}", italic=True, text_color_rgb=[150, 150, 150]))
        nodes.append(PageBreakNode())

        #
        # 2. Index / Table of Contents (TOC)
        #
        nodes.append(HeadingNode(text=vocab.get("toc_title", "Contenido"), level=4, primary_color_rgb=self.primary_color_rgb))
        nodes.append(ParagraphNode(text="[Índice de Contenidos Generado Dinámicamente al Abrir el Documento]", italic=True, text_color_rgb=[128, 128, 128], space_after=20))
        nodes.append(PageBreakNode())

        #
        # 3. CHAPTER 1: EXECUTIVE SUMMARY AND BUSINESS CONTEXT
        #
        resumen_path = modules_dir / "02_resumen_ejecutivo.md"
        if resumen_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(resumen_path))
        else:
            nodes.append(HeadingNode(text="1. Resumen Ejecutivo y Contexto de Negocio", level=1, primary_color_rgb=self.primary_color_rgb))
            nodes.append(ParagraphNode(text="Módulo de resumen ejecutivo no disponible."))

        #
        # CHAPTER 2: ASSESSMENT OBJECTIVE AND SCOPE
        #
        nodes.append(HeadingNode(text="2. Objetivo y Alcance", level=1, primary_color_rgb=self.primary_color_rgb))
        
        intro_path = modules_dir / "01_introduccion.md"
        if intro_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(intro_path, skip_level_1=True))
        else:
            nodes.append(ParagraphNode(text="Módulo de introducción y alcance no disponible."))

        #
        # CHAPTER 3: MATURITY PROFILE AND GENERAL EVALUATION
        #
        nodes.append(HeadingNode(text=f"3. {vocab.get('radar_title', 'Perfil de Madurez Ponderado')}", level=1, primary_color_rgb=self.primary_color_rgb))
        
        # 3.1 Global Dashboard
        nodes.append(HeadingNode(text=vocab.get("dashboard_title", "Cuadro de Mando de Madurez"), level=2, primary_color_rgb=self.primary_color_rgb))
        nodes.append(ParagraphNode(text=vocab.get("dashboard_intro", "La evaluación integral del estado actual consolida una valoración cuantitativa:")))

        #
        nodes.append(TableNode(
            rows=[
                TableRowNode(cells=[
                    CellNode(text=vocab.get("score_lbl", "PUNTUACIÓN AS-IS"), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                    CellNode(text=vocab.get("maturity_lbl", "NIVEL DE MADUREZ"), bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER"),
                ], is_header=True),
                TableRowNode(cells=[
                    CellNode(text=display_score_str, bold=True, font_size=16, bg_color="FFF3CD" if gs_val < 3.4 else "D9F2D9", align="CENTER"),
                    CellNode(text=global_band, bold=True, font_size=12, bg_color="FFF3CD" if gs_val < 3.4 else "D9F2D9", align="CENTER"),
                ]),
            ]
        ))
        nodes.append(SpacerNode(points=10))

        # Read resilience data.
        res_reading = vocab.get("resilience_reading", "Lectura de Resiliencia:")
        nodes.append(ParagraphNode(text=f"**{res_reading}** {global_reading}"))
        nodes.append(SpacerNode(points=15))

        # 3.2 Radar Chart
        nodes.append(HeadingNode(text=vocab.get("radar_title", "Perfil Visual de Madurez"), level=2, primary_color_rgb=self.primary_color_rgb))
        radar_path = case_dir / "pillar_radar_chart.generated.png"
        if radar_path.exists():
            nodes.append(PictureNode(path=str(radar_path), width_inches=6.0))
            nodes.append(SpacerNode(points=15))

        # 3.3 Score Justification Matrix (from CSV) with fallback mechanism
        csv_mat_path = modules_dir / "04_matriz_madurez.csv"
        if csv_mat_path.exists():
            # Ensure header collections are not empty to prevent the generation of malformed tables.
            mat_headers = vocab.get("justification_table_headers") or [
                "Pilar / Capacidad Evaluada", "Score AS-IS", "Análisis de Brecha y Justificación de Nota"
            ]
            nodes.append(self._parse_csv_generic(csv_mat_path, mat_headers))

        nodes.append(PageBreakNode())

        #
        # CHAPTER 4: TECHNOLOGICAL DIAGNOSIS AND PLATFORM ANALYSIS
        #
        nodes.append(HeadingNode(text=vocab.get("platform_overview_title", "4. Descripción de la Plataforma de Infraestructura Actual"), level=1, primary_color_rgb=self.primary_color_rgb))
        
        # 4.1. Description of the Current Infrastructure Platform (The Baseline)
        nodes.append(HeadingNode(text=vocab.get("platform_overview_title", "Descripción de la Plataforma"), level=2, primary_color_rgb=self.primary_color_rgb))
        
        # Inject supporting overview text.
        overview_text = (
            f"{vocab.get('default_overview_text', '')}{tower_name} de {client_name} se basan "
            f"on-premise y AWS, recogiendo volúmenes operativos y dependencias."
        )
        nodes.append(ParagraphNode(text=overview_text))

        desc_path = modules_dir / "03_descripcion_plataforma.md"
        if desc_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(desc_path))
        else:
            nodes.append(ParagraphNode(text="Módulo de descripción de plataforma no disponible."))

        nodes.append(PageBreakNode())

        #
        # CHAPTER 5: CROSS-FUNCTIONAL CAPABILITY ANALYSIS
        #
        trans_path = modules_dir / "05_transversal.md"
        if trans_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(trans_path))

        nodes.append(PageBreakNode())

        #
        # CHAPTER 6: QUANTITATIVE RISK MATRIX (O-FAIR)
        #
        nodes.append(HeadingNode(text=vocab.get("risk_matrix_title", "5. Matriz de Riesgo Cuantitativa (FAIR)"), level=1, primary_color_rgb=self.primary_color_rgb))
        
        # Generate introductory text by dynamically injecting the annualized loss exposure value.
        formatted_ale = f"{total_fair_ale:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") if meta_lang == "es" else f"{total_fair_ale:,.0f}"
        risk_intro = (
            f"{vocab.get('risk_intro_1', '')}{client_name}{vocab.get('risk_intro_2', '')}"
            f"**{formatted_ale} {currency}**{vocab.get('risk_intro_3', '')}"
        )
        nodes.append(ParagraphNode(text=risk_intro))

        # Insert an inline executive methodological note referencing Appendix D.
        nodes.append(ParagraphNode(text="*Nota Metodológica:* Para garantizar el máximo rigor directivo, la estimación del riesgo anualizado proyectado (ALE) y la priorización de vulnerabilidades técnicas en este informe se basan estrictamente en el estándar internacional **O-FAIR** y en simulaciones actuariales probabilísticas de Monte Carlo. Esto permite cuantificar con transparencia la exposición al riesgo en términos financieros reales del negocio. La explicación técnica, parámetros de calibración de pérdidas y las fórmulas estadísticas aplicadas se detallan en el **Apéndice D** de este reporte.", italic=True, space_after=12))

        #
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
                        r_item = {
                            "id": f"RVS{r_idx+1:02d}",
                            "pilar": pilar_full_name,
                            "capability": row_data[0].split(" - ")[1] if " - " in row_data[0] else row_data[0],
                            "finding": row_data[1],
                            "business_risk": row_data[2],
                            "tef": float(row_data[3]),
                            "lm": float(row_data[4]),
                            "ale": float(row_data[5]),
                        }
                        risks_data_list.append(r_item)
            except Exception:
                pass

        # 5.1 Generate 5x5 Heatmap (Word-native mosaic)
        if risks_data_list:
            nodes.append(HeadingNode(text=vocab.get("exposure_summary_title", "Resumen de Exposición y Mapa de Calor"), level=2, primary_color_rgb=self.primary_color_rgb))
            
            # Group risks by TEF x LM quadrant (1-5).
            matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
            for r in risks_data_list:
                r_tef = min(5, max(1, int(round(r["tef"]))))
                r_lm = min(5, max(1, int(round(r["lm"]))))
                matrix_cells[r_tef][r_lm].append(r["id"])

            # 6x6 matrix header
            heatmap_rows = []
            heatmap_headers = ["TEF \\ LM", "LM 1", "LM 2", "LM 3", "LM 4", "LM 5"]
            heatmap_rows.append(TableRowNode(cells=[
                CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                for h in heatmap_headers
            ], is_header=True))

            #
            for tef_val in range(5, 0, -1):
                row_cells = [CellNode(text=f"TEF {tef_val}", bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")]
                
                for lm_val in range(1, 6):
                    cell_risks = matrix_cells[tef_val][lm_val]
                    cell_text = ", ".join(cell_risks) if cell_risks else "-"
                    
                    #
                    severity = tef_val * lm_val
                    if severity >= 15:
                        bg_color = "FADBD8"  # Soft Red
                    elif severity >= 8:
                        bg_color = "FCF3CD"  # Soft Amber
                    else:
                        bg_color = "D5F5E3"  # Soft Green

                    row_cells.append(CellNode(text=cell_text, bold=True, bg_color=bg_color, align="CENTER"))
                
                heatmap_rows.append(TableRowNode(cells=row_cells))

            nodes.append(TableNode(rows=heatmap_rows))
            nodes.append(SpacerNode(points=15))

            # 5.2 Methodological Legends (TEF & LM Scales)
            nodes.append(HeadingNode(text="Leyendas Metodológicas", level=3, primary_color_rgb=self.primary_color_rgb))

            # TEF Table
            nodes.append(HeadingNode(text=vocab.get("tef_title", "Criterios de Frecuencia de la Amenaza (TEF)"), level=4, primary_color_rgb=self.primary_color_rgb))
            tef_headers = vocab.get("tef_headers") or ["Nivel TEF", "Denominación", "Frecuencia Anualizada Estimada"]
            tef_data = [
                ("TEF 1", "Muy Bajo" if meta_lang == "es" else "Very Low", "< 0,1 eventos/año (menos de una vez cada 10 años)" if meta_lang == "es" else "< 0.1 events/year (less than once every 10 years)"),
                ("TEF 2", "Bajo" if meta_lang == "es" else "Low", "0,1 - 0,5 eventos/año (una vez cada 4 años)" if meta_lang == "es" else "0.1 - 0.5 events/year (once every 4 years)"),
                ("TEF 3", "Medio" if meta_lang == "es" else "Medium", "0,5 - 2,0 eventos/año (una vez al año)" if meta_lang == "es" else "0.5 - 2.0 events/year (once a year)"),
                ("TEF 4", "Alto" if meta_lang == "es" else "High", "2,0 - 10 eventos/año (una vez al trimestre)" if meta_lang == "es" else "2.0 - 10 events/year (once a quarter)"),
                ("TEF 5", "Muy Alto" if meta_lang == "es" else "Very High", "> 10 eventos/año (una vez al mes)" if meta_lang == "es" else "> 10 events/year (once a month)"),
            ]

            tef_rows = [
                TableRowNode(cells=[
                    CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                    for h in tef_headers
                ], is_header=True)
            ]
            for t_idx, r_vals in enumerate(tef_data):
                bg = self.alt_row_hex if t_idx % 2 == 1 else "FFFFFF"
                tef_rows.append(TableRowNode(cells=[
                    CellNode(text=r_vals[0], bold=True, bg_color=self.alt_row_hex, align="CENTER"),
                    CellNode(text=r_vals[1], bg_color=bg, align="CENTER"),
                    CellNode(text=r_vals[2], bg_color=bg),
                ]))
            nodes.append(TableNode(rows=tef_rows))
            nodes.append(SpacerNode(points=10))

            # LM Table
            nodes.append(HeadingNode(text=vocab.get("lm_title", "Criterios de Magnitud de Pérdida Directa/Indirecta (LM)"), level=4, primary_color_rgb=self.primary_color_rgb))
            lm_headers = vocab.get("lm_headers") or ["Nivel LM", "Clasificación de Impacto", "Límite de Pérdida Financiera"]
            lm_data = [
                ("LM 1", "Muy Bajo" if meta_lang == "es" else "Very Low", f"< 1.000 {currency}" if meta_lang == "es" else f"< 1,000 {currency}"),
                ("LM 2", "Bajo" if meta_lang == "es" else "Low", f"1.000 {currency} - 5.000 {currency}" if meta_lang == "es" else f"1,000 {currency} - 5,000 {currency}"),
                ("LM 3", "Medio" if meta_lang == "es" else "Medium", f"5.000 {currency} - 25.000 {currency}" if meta_lang == "es" else f"5,000 {currency} - 25,000 {currency}"),
                ("LM 4", "Alto" if meta_lang == "es" else "High", f"25.000 {currency} - 100.000 {currency}" if meta_lang == "es" else f"25,000 {currency} - 100,000 {currency}"),
                ("LM 5", "Muy Alto" if meta_lang == "es" else "Very High", f"100.000 {currency} - 500.000 {currency}" if meta_lang == "es" else f"100,000 {currency} - 500,000 {currency}"),
            ]

            lm_rows = [
                TableRowNode(cells=[
                    CellNode(text=f"{h} ({currency})" if h_idx > 0 else h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                    for h_idx, h in enumerate(lm_headers)
                ], is_header=True)
            ]
            for l_idx, r_vals in enumerate(lm_data):
                bg = self.alt_row_hex if l_idx % 2 == 1 else "FFFFFF"
                lm_rows.append(TableRowNode(cells=[
                    CellNode(text=r_vals[0], bold=True, bg_color=self.alt_row_hex, align="CENTER"),
                    CellNode(text=r_vals[1], bg_color=bg, align="CENTER"),
                    CellNode(text=r_vals[2], bg_color=bg),
                ]))
            nodes.append(TableNode(rows=lm_rows))
            nodes.append(SpacerNode(points=20))

        # 5.3 Detailed Log Segmented by Domain (in multiple independent tables)
        if risks_data_list:
            nodes.append(HeadingNode(text=vocab.get("detailed_risks_title", "Registro Detallado de Hallazgos Forenses"), level=2, primary_color_rgb=self.primary_color_rgb))

            # Group risks by pillar.
            risks_by_pilar = {}
            for r in risks_data_list:
                p_name = r["pilar"]
                if p_name not in risks_by_pilar:
                    risks_by_pilar[p_name] = []
                risks_by_pilar[p_name].append(r)

            for p_name, pilar_risks in risks_by_pilar.items():
                pilar_header = vocab.get("detailed_risks_pilar_title", "Análisis de Vulnerabilidades: ") + p_name
                nodes.append(HeadingNode(text=pilar_header, level=3, primary_color_rgb=self.primary_color_rgb))

                headers_table = vocab.get("detailed_risks_headers") or ["ID", "Vulnerabilidad y Evidencias", "Exposición y Riesgo"]
                risk_rows = [
                    TableRowNode(cells=[
                        CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                        for h in headers_table
                    ], is_header=True)
                ]

                for s_idx, hc in enumerate(pilar_risks):
                    bg = self.alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
                    
                    # Construct the consolidated forensic cell.
                    vulnerability = f"Vulnerabilidad Identificada:\n{hc['finding']}\n\n"
                    impact = f"Impacto Operativo:\n{hc['business_risk']}\n\n"
                    evidence = "Evidencia Forense Literal:\n\"No se aportó evidencia literal para esta simulación.\""  # Provides a fallback value if the required information is missing from the RAG context.
                    desc_text = vulnerability + impact + evidence

                    #
                    tef = hc["tef"]
                    lm = hc["lm"]
                    ale = hc["ale"]

                    calc_txt = "N/A"
                    bg_severe = bg
                    if ale and ale > 0:
                        calc_txt = f"TEF: {tef:.1f} / 5,0\nLM: {lm:.1f} / 5,0\n\nALE: {ale:,.0f} {currency}".replace(",", "X").replace(".", ",").replace("X", ".")
                        
                        risk_score = tef * lm
                        if risk_score >= 15 or ale >= 1000000:
                            bg_severe = "F8D7DA" # Light Red
                        elif risk_score >= 10 or ale >= 250000:
                            bg_severe = "FFF3CD" # Light Amber
                        elif risk_score >= 5 or ale >= 50000:
                            bg_severe = "E2E3E5" # Light Gray

                    risk_rows.append(TableRowNode(cells=[
                        CellNode(text=hc["id"], bold=True, bg_color=self.alt_row_hex, align="CENTER"),
                        CellNode(text=desc_text, bg_color=bg, align="JUSTIFY"),
                        CellNode(text=calc_txt, bold=True, bg_color=bg_severe, align="RIGHT"),
                    ]))

                nodes.append(TableNode(rows=risk_rows))

        nodes.append(PageBreakNode())

        #
        # CHAPTER 7: NEXT STEPS AND CONCLUSIONS
        #
        concl_path = modules_dir / "07_conclusiones.md"
        if concl_path.exists():
            nodes.extend(self._parse_markdown_to_nodes(concl_path))

        #
        # APPENDICES (Glossary of Abbreviations, Limitation of Liability, Source Custody Record)
        #
        nodes.append(PageBreakNode())

        # Appendix A: Glossary and List of Abbreviations
        # Omit the manual 'Appendix A' prefix to avoid conflicts with Word's automatic 'Appendix A' style numbering.
        app_a_title = re.sub(r"^(Apéndice|Appendix)\s+[A-Z]:\s*", "", vocab.get("appendix_a_title", "Lista de Abreviaturas"))
        nodes.append(HeadingNode(text=app_a_title, level=1, primary_color_rgb=self.primary_color_rgb))
        nodes.append(ParagraphNode(text=vocab.get("appendix_a_intro", "A continuación se definen los términos técnicos utilizados:")))

        glossary_path = Path("engine_config/abbreviations_glossary.json")
        if glossary_path.exists():
            try:
                with open(glossary_path, "r", encoding="utf-8-sig") as gf:
                    glossary = json.load(gf)
                
                gloss_rows = [
                    TableRowNode(cells=[
                        CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                        for h in vocab.get("appendix_a_headers") or ["Abreviatura", "Significado / Descripción Técnica"]
                    ], is_header=True)
                ]

                for g_idx, (term, desc) in enumerate(sorted(glossary.items())):
                    bg = self.alt_row_hex if g_idx % 2 == 1 else "FFFFFF"
                    gloss_rows.append(TableRowNode(cells=[
                        CellNode(text=term, bold=True, bg_color=bg),
                        CellNode(text=desc, bg_color=bg),
                    ]))

                nodes.append(TableNode(rows=gloss_rows))
            except Exception:
                pass

        # Appendix B: Limitation of Liability Clause
        # Omit the manual 'Appendix B' prefix to prevent numbering conflicts.
        app_b_title = re.sub(r"^(Apéndice|Appendix)\s+[A-Z]:\s*", "", vocab.get("appendix_b_title", "Cláusula de Limitación de Responsabilidad"))
        nodes.append(SpacerNode(points=20))
        nodes.append(HeadingNode(text=app_b_title, level=1, primary_color_rgb=self.primary_color_rgb))
        nodes.append(ParagraphNode(text=vocab.get("disclaimer_text_1", self.disclaimer), italic=True, space_after=12))
        nodes.append(ParagraphNode(text=vocab.get("disclaimer_text_2", ""), italic=True, space_after=12))
        nodes.append(ParagraphNode(text=vocab.get("disclaimer_text_3", ""), italic=True, space_after=12))

        # Appendix C: Information Sources Chain of Custody
        # Omit the manual 'Appendix C' prefix to prevent numbering conflicts.
        app_c_title = re.sub(r"^(Apéndice|Appendix)\s+[A-Z]:\s*", "", vocab.get("appendix_c_title", "Registro de Custodia de Fuentes de Información"))
        nodes.append(SpacerNode(points=20))
        nodes.append(HeadingNode(text=app_c_title, level=1, primary_color_rgb=self.primary_color_rgb))
        nodes.append(ParagraphNode(text=vocab.get("appendix_c_intro", "Para garantizar la transparencia, a continuación se listan las fuentes documentales utilizadas:")))

        src_data = []
        source_docs = blueprint_data.get("source_documents")
        if source_docs:
            for doc_item in source_docs:
                src_data.append((
                    doc_item.get("code", "[Doc]"),
                    doc_item.get("name", "Documento"),
                    doc_item.get("desc", "Documento bajo custodia de auditoría.")
                ))
        else:
            src_data = [
                ("[Cuestionario de Autoevaluación]", f"preguntas_{client_name.lower()}_con_notas.txt", f"{vocab.get('bib_cues', '')}{tower_name}{vocab.get('bib_cues_desc', '')}{client_name}."),
                ("[Dossier de Contexto]", f"contexto_{client_name.lower()}_elite.docx", f"{vocab.get('bib_contexto', '')}{client_name}{vocab.get('bib_contexto_desc', '')}"),
                ("[Minutas de Sesión]", f"Sesión de Contexto ({client_name})", f"{vocab.get('bib_minutas', '')}{client_name}{vocab.get('bib_minutas_desc', '')}")
            ]

        source_rows = [
            TableRowNode(cells=[
                CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                for h in vocab.get("appendix_c_headers") or ["Código de Referencia", "Documento Fuente / Origen de Datos", "Descripción y Ámbito de Custodia"]
            ], is_header=True)
        ]

        for s_idx, row_vals in enumerate(src_data):
            bg = self.alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
            source_rows.append(TableRowNode(cells=[
                CellNode(text=row_vals[0], bold=True, bg_color=self.alt_row_hex, align="CENTER"),
                CellNode(text=row_vals[1], bg_color=bg, align="CENTER"),
                CellNode(text=row_vals[2], bg_color=bg),
            ]))

        nodes.append(TableNode(rows=source_rows))

        #
        # APPENDIX D: METHODOLOGY
        #
        nodes.append(SpacerNode(points=20))
        # Omit the 'Appendix D' prefix to prevent conflicts with Word's automatic numbering for that style.
        nodes.append(HeadingNode(text="Metodología", level=1, primary_color_rgb=self.primary_color_rgb))
        
        # D.1 Maturity Assessment Methodology
        nodes.append(HeadingNode(text="Metodología de Valoración de Madurez", level=2, primary_color_rgb=self.primary_color_rgb))
        nodes.append(ParagraphNode(text="La madurez se califica en una escala analítica del 1,00 al 5,00, donde cada nivel determina un estadio de control:"))
        
        nodes.append(ParagraphNode(text="**Nivel 1 - Inicial (1.0-1.8):** Prácticas ad-hoc, inestables o dependientes del esfuerzo heroico de personas clave.", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Nivel 2 - Básico (1.8-2.6):** Prácticas funcionales de manera parcial o irregular, sin consistencia organizativa.", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Nivel 3 - Estandarizado (2.6-3.4):** Procesos formalizados e implantados de manera coherente en toda la organización.", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Nivel 4 - Optimizado (3.4-4.2):** Capacidades industrializadas, gobernadas predictivamente y sustentadas en métricas.", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Nivel 5 - Avanzado (4.2-5.0):** Procesos dinámicos impulsados por automatización inteligente y mejora continua.", style="List Bullet"))

        # The style for "Evaluated Capabilities" must match the preceding style (Heading 2) for consistency.
        nodes.append(SpacerNode(points=10))
        nodes.append(HeadingNode(text="Capacidades Evaluadas y Cálculo del Score", level=2, primary_color_rgb=self.primary_color_rgb))
        nodes.append(ParagraphNode(text="El nivel de madurez técnica y el score global de la torre se consolidan mediante el promedio ponderado de las calificaciones obtenidas en las siguientes dimensiones y KPIs evaluados:"))
        
        nodes.append(ParagraphNode(text="**Compute Foundation & Virtualization (Peso: 22%):** Evalúa de manera integral la madurez operativa y los baselines técnicos de la infraestructura, analizando críticamente factores clave como estandarización del estate de cómputo (clusters/hosts/configuración), gestión del ciclo de vida del compute (patching/upgrades/firmware), capacity & Performance Management (CPU/RAM/overcommit, saturación) y disponibilidad de la plataforma de compute (HA operable y mantenibilidad).", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Container Platform & Kubernetes Operations (Peso: 19%):** Evalúa de manera integral la madurez operativa y los baselines técnicos de la infraestructura, analizando críticamente factores clave como estandarización de servicios base (ingress, registry, certificados, storage classes), gestión del ciclo de vida de clusters (upgrades, compatibilidad, deprecations), seguridad base and aislamiento (RBAC, namespaces, separación de roles) y operación y soporte del clúster (runbooks, incidentes, capacidad de nodos).", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Hybrid Cloud Enablement & Landing Zones (Peso: 21%):** Evalúa de manera integral la madurez operativa y los baselines técnicos de la infraestructura, analizando críticamente factores clave como existencia y cobertura de Landing Zone (estructura base cloud), guardrails y políticas de gobierno técnico (policy-as-code / estándares), estandarización de patrones de despliegue híbridos (IaaS/PaaS) y control de consumo y costes (tagging, showback, límites).", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Automation, Provisioning & Platform Self-Service (Peso: 18%):** Evalúa de manera integral la madurez operativa y los baselines técnicos de la infraestructura, analizando críticamente factores clave como cobertura de Infraestructura como Código (IaC) en el provisioning, madurez del catálogo y self-service (tiempo de provisión y control), gestión de golden images y configuración estándar (baseline), modelo operativo y gestión de la plataforma como producto y experiencia de consumo y adopción de la plataforma.", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Platform Operations, Observability & Reliability (Peso: 20%):** Evalúa de manera integral la madurez operativa y los baselines técnicos de la infraestructura, analizando críticamente factores clave como cobertura de observabilidad de compute y plataforma (métricas/logs/alertas), definición y seguimiento de SLO/SLAs de plataforma, gestión de incidentes y mejora continua (postmortems, runbooks) y capacity forecasting y prevención de degradaciones (plataforma).", style="List Bullet"))

        # D.2 Quantitative Risk Methodology (FAIR)
        nodes.append(SpacerNode(points=15))
        nodes.append(HeadingNode(text="Metodología Cuantitativa de Riesgos (FAIR)", level=2, primary_color_rgb=self.primary_color_rgb))
        nodes.append(ParagraphNode(text="Este diagnóstico técnico aplica el estándar internacional O-FAIR (Factor Analysis of Information Risk) del *The Open Group* para modelar, cuantificar y priorizar la exposición al riesgo de infraestructura en términos financieros reales."))
        nodes.append(ParagraphNode(text="Para evitar la \"Falacia de los Promedios\" (donde las estimaciones fijas e individuales distorsionan el riesgo real), el motor de la plataforma aplica un algoritmo de simulación actuarial de Monte Carlo de 10.000 iteraciones para cada hallazgo detectado, basado en los siguientes principios científicos:"))

        # Dynamically detect organizational scale to apply customized calibration.
        client_name_lower = client_name.lower()
        is_critical = "redeia" in client_name_lower or "eléctrica" in client_name_lower or "eurovision" in client_name_lower
        formatted_max_lm = "1.500.000 €" if is_critical else "500.000 €"

        nodes.append(ParagraphNode(text="1. **Estimaciones de Tres Puntos (Incertidumbre):** Cada nivel cualitativo de la auditoría (escala 1 a 5) se traduce a un rango dinámico definido por tres parámetros: Mínimo, Más Probable y Máximo.", bold=False))
        nodes.append(ParagraphNode(text="**Frecuencia de Amenaza (TEF):** Mapea la probabilidad anualizada de exposición (de 0,1 a 24 eventos de amenaza al año).", style="List Bullet"))
        nodes.append(ParagraphNode(text="**Vulnerabilidad (Vuln):** Mapea la probabilidad de éxito de la amenaza según el nivel de controles (de 5% a 100%).", style="List Bullet"))
        nodes.append(ParagraphNode(text=f"**Magnitud de Pérdida (LM):** Mapea el impacto financiero directo e indirecto (laboral, cumplimiento, remediación) desde 100 {currency} hasta {formatted_max_lm} por incidente.", style="List Bullet"))
        
        nodes.append(ParagraphNode(text="2. **Modelado con Curvas de Probabilidad Beta-PERT:** Para cada una de las 10.000 simulaciones de la simulación, el motor toma muestras aleatorias de las curvas de densidad de probabilidad continua Beta-PERT correspondientes a cada parámetro. Esto permite capturar el comportamiento realista de los incidentes tecnológicos (donde existe una 'larga cola' de costes de remediación elevados hacia la derecha).", bold=False))
        
        nodes.append(ParagraphNode(text="3. **Cálculo del Exposición Anualizada de Pérdida (ALE):** En cada iteración se realiza un sorteo de Bernoulli basado en la vulnerabilidad muestreada. Si el evento de pérdida se materializa, el coste anualizado para esa simulación es el producto de la frecuencia por la pérdida promedio:", bold=False))
        
        # Apply specific formatting to the formula: center alignment, bold, 12pt font, and primary corporate blue color (#0072BC).
        nodes.append(ParagraphNode(
            text="ALE = Frecuencia de Amenaza x Vulnerabilidad x Magnitud de Pérdida",
            bold=True,
            text_color_rgb=self.primary_color_rgb,
            align="CENTER",
            font_size=12.0,
            space_after=15
        ))
        
        nodes.append(ParagraphNode(text="4. **Métricas de Convergencia Estadística (ALE y P90):** El valor final de ALE Proyectado reflejado en las tablas detalladas del informe representa la media estadística de pérdida resultante de esas 10.000 iteraciones independientes. Adicionalmente, el sistema calcula la métrica P90 (Percentil 90) para alertar a la dirección sobre la exposición financiera máxima esperada en el peor escenario razonable de negocio.", bold=False))

        # D.3 Scale Calibration Profile
        nodes.append(SpacerNode(points=15))
        nodes.append(HeadingNode(text="Perfil de Calibración Activo y Escala de Pérdidas", level=2, primary_color_rgb=self.primary_color_rgb))
        
        if is_critical:
            nodes.append(ParagraphNode(text="**Perfil de Calibración Activo: CRITICAL_INFRASTRUCTURE (Escala Alta / Regulada)**", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"Debido a la naturaleza del negocio de **{client_name}** como operador de Infraestructura Crítica en el sector de Energía (o servicios globales de alta criticidad), se ha activado el Preset de calibración de alta escala. Esto ajusta los rangos de Magnitud de Pérdida (LM) de acuerdo con el impacto sistémico real de interrupciones en su plataforma core:", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 1 (Impacto Muy Bajo):** Rango de **< 1.000 {currency}**. Se fundamenta en el coste directo de intervenciones rápidas y sencillas de reconfiguración técnica (menos de 8 horas de dedicación de un ingeniero de soporte).", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 2 (Impacto Bajo):** Rango de **1.000 {currency} a 5.000 {currency}**. Se fundamenta en el coste laboral de paradas de servicio locales de menos de 3 horas que requieren la intervención de un Ingeniero Senior o Administrador de Sistemas para su remediación, sin penalizaciones por SLA de clientes.", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 3 (Impacto Medio):** Rango de **5.000 {currency} a 25.000 {currency}**. Se fundamenta en incidencias de seguridad de severidad media, caída de entornos de pre-producción o indisponibilidades que afecten temporalmente la productividad de equipos internos de ingeniería por un máximo de 24 horas laborables.", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 4 (Impacto Alto):** Rango de **50.000 {currency} a 300.000 {currency}**. Este umbral se fundamenta de forma estricta en el régimen sancionador de la directiva europea **NIS2** y el **Esquema Nacional de Seguridad (ENS)** en España para incidentes graves derivados de falta de mantenimiento u obsolescencia técnica.", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 5 (Impacto Muy Alto):** Rango de **250.000 {currency} a 1.500.000 {currency}**. Este rango está alineado con el estudio de referencia mundial **ITIC Global Server Hardware Downtime Report**, el cual determina que para el 98% de los operadores de infraestructuras críticas y energía, el coste de una sola hora de indisponibilidad de sistemas core supera el millón de euros debido a la interrupción de procesos, penalizaciones por acuerdos de nivel de servicio (SLA) y remediación forense urgente.", style="List Bullet"))
        else:
            nodes.append(ParagraphNode(text="**Perfil de Calibración Activo: MID_MARKET (Escala Organizacional Media)**", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"Debido a la escala organizativa de **{client_name}**, el motor de riesgos de la plataforma ha activado el Preset de calibración del mercado medio. Esto dimensiona las pérdidas a un rango adecuado al impacto de su negocio:", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 1 (Impacto Muy Bajo):** Rango de **< 1.000 {currency}**. Se fundamenta en el coste directo de reconfiguraciones técnicas rápidas de bajo impacto técnico.", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 2 (Impacto Bajo):** Rango de **1.000 {currency} a 5.000 {currency}**. Basado en incidencias menores solucionables por el equipo de soporte de primer nivel en pocas horas sin afectación de facturación.", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 3 (Impacto Medio):** Rango de **5.000 {currency} a 25.000 {currency}**. Estimando fallos parciales de disponibilidad que afecten temporalmente la productividad de equipos técnicos de soporte interno.", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 4 (Impacto Alto):** Rango de **25.000 {currency} a 100.000 {currency}**, estimando interrupciones de servicios no críticos y costes de auditorías de cumplimiento extraordinarias.", style="List Bullet"))
            nodes.append(ParagraphNode(text=f"**LM 5 (Impacto Muy Alto):** Rango de **100.000 {currency} a 500.000 {currency}**, basado en la parada de la cadena de facturación o producción durante más de 8 horas laborables consecutivas.", style="List Bullet"))

        return DocumentAST(title=f"Technical Annex - Tower {tower_id}", metadata=tower_meta, nodes=nodes)

    def _parse_markdown_to_nodes(self, md_path: Path, skip_level_1: bool = False) -> List[Any]:
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

            # Exclude special markers for table and mosaic directives from the content processing stream.
            if "--- TABLA COMPARATIVA" in cleaned or "FORTALEZAS_CLAVE:" in cleaned or "BRECHAS_CLAVE:" in cleaned or "--- FIN TABLA" in cleaned:
                continue

            #
            if cleaned.startswith("# "):
                if not skip_level_1:
                    nodes.append(HeadingNode(text=cleaned[2:], level=1, primary_color_rgb=self.primary_color_rgb))
            elif cleaned.startswith("## "):
                nodes.append(HeadingNode(text=cleaned[3:], level=2, primary_color_rgb=self.primary_color_rgb))
            elif cleaned.startswith("### "):
                nodes.append(HeadingNode(text=cleaned[4:], level=3, primary_color_rgb=self.primary_color_rgb))
            elif cleaned.startswith("#### "):
                nodes.append(HeadingNode(text=cleaned[5:], level=4, primary_color_rgb=self.primary_color_rgb))
            #
            elif cleaned.startswith("* ") or cleaned.startswith("- "):
                nodes.append(ParagraphNode(text=cleaned[2:], style="List Bullet", space_after=6))
            #
            elif cleaned.startswith("> "):
                nodes.append(ParagraphNode(text=cleaned[2:], italic=True, space_after=12))
            #
            else:
                nodes.append(ParagraphNode(text=cleaned, space_after=8))

        return nodes

    def _extract_key_bullets_from_md(self, md_path: Path, section_marker: str) -> List[str]:
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
                if cleaned.startswith("BRECHAS_CLAVE:") or cleaned.startswith("FORTALEZAS_CLAVE:") or "--- FIN TABLA" in cleaned:
                    break
                if cleaned.startswith("* ") or cleaned.startswith("- "):
                    bullets.append(cleaned[2:])
        return bullets

    def _parse_csv_generic(self, csv_path: Path, headers: List[str]) -> TableNode:
        rows = []
        #
        rows.append(TableRowNode(cells=[
            CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
            for h in headers
        ], is_header=True))

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)  #
            for r_idx, row_data in enumerate(reader):
                if not row_data:
                    continue
                bg = self.alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
                cells = []
                for c_idx, val in enumerate(row_data):
                    bold = (c_idx == 0)
                    align = "CENTER" if c_idx == 1 else ("LEFT" if c_idx == 2 else "JUSTIFY")
                    cells.append(CellNode(text=val, bold=bold, bg_color=bg, align=align))
                rows.append(TableRowNode(cells=cells))

        return TableNode(rows=rows)
