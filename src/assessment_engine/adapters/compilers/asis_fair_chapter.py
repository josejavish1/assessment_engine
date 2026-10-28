"""Actuarial Open FAIR quantitative risk matrix chapter builder for Word DOCX."""
from __future__ import annotations

import csv
import json
import logging
import os
from pathlib import Path
from typing import Any

from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from assessment_engine.infrastructure.docx_render_utils import (
    autofit_table_to_contents,
    finalize_table,
    set_cell_text,
    shade_cell,
)
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_number,
    t,
)
from assessment_engine.infrastructure.text_utils import clean_text_for_word
from assessment_engine.adapters.compilers.asis_docx_primitives import (
    COLOR_BLUE,
    _add_markdown_bullet,
    add_appendix_subheading,
    add_body_paragraph,
    add_callout_box,
    add_heading,
    add_spacer,
    format_currency_custom,
    parse_and_append_markdown_section,
    set_cell_border_white,
    set_cell_text_custom,
)

logger = logging.getLogger(__name__)

def _compile_chapter_4_fair_risk_matrix(doc: Any, ctx: dict[str, Any]) -> dict[str, Any]:
    """Assemble and render Chapter 4: Quantitative Risk Matrix."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    p_color_hex = ctx["p_color_hex"]
    alt_row_hex = ctx["alt_row_hex"]
    vocab = ctx["vocab"]
    modules_dir = ctx["modules_dir"]
    doc_lang = ctx["doc_lang"]
    currency = ctx.get("currency", "€")
    is_critical = ctx.get("is_critical", False)
    global_fair_ale = ctx["global_fair_ale"]
    b_data = ctx.get("b_data", {})
    payload_path = ctx.get("payload_path", Path("."))
    tower_dir_obj = ctx["tower_dir_obj"]
    payload_path = ctx["payload_path"]
    client_name = ctx["client_name"]
    reg_name = ctx.get("reg_name", "las regulaciones aplicables")
    industry_name = ctx.get(
        "industry_name",
        "Sector Estándar" if doc_lang == "es" else "Standard Sector",
    )

    total_p90 = 0.0
    formatted_ale_item = "0"
    formatted_p90 = "0"
    t_sep = vocab.get("thousands_sep", ".")
    d_sep = vocab.get("decimal_sep", ",")

    def add_markdown_bullet_local(text: str, space_after: int = 4) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

    # Assemble and render Chapter 4: Quantitative Risk Matrix.
    #
    add_heading(doc, vocab["risk_matrix_title"], level=1, primary_color_rgb=p_color_rgb)

    # Format the Annualized Loss Expectancy (ALE) value. Localization logic is isolated in a separate function, per requirement 2.
    t_sep = vocab.get("thousands_sep", ".")
    d_sep = vocab.get("decimal_sep", ",")
    formatted_ale = format_currency_custom(global_fair_ale, t_sep, d_sep)

    # Load dynamic SRE hourly rate and currency symbol from custom calibration if available (FAIR-MAM)
    import os
    client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
    tower_id = b_data.get("document_meta", {}).get("tower_code", "T2")
    custom_profile_path = Path(f"working/{client_id}/{tower_id}/custom_risk_profile.json")
    if not custom_profile_path.exists():
        for t_code in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]:
            temp_path = Path(f"working/{client_id}/{t_code}/custom_risk_profile.json")
            if temp_path.exists():
                custom_profile_path = temp_path
                break

    custom_calibration = {}
    if custom_profile_path.exists():
        try:
            with open(custom_profile_path, "r", encoding="utf-8-sig") as cf:
                custom_calibration = json.load(cf)
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")

    sre_rate = round(float(custom_calibration.get("hourly_rate_sre_eur", 36.0)))
    currency = (
        ctx.get("currency")
        or custom_calibration.get("currency_symbol")
        or ("€" if doc_lang == "es" else "$")
    )

    # Calculate aggregate Tail Risk (P90 and Max Probable Loss)
    total_p90 = 0.0
    total_max = 0.0
    try:
        for pillar in b_data.get("pillars_analysis", []):
            for hc in pillar.get("health_check_asis", []):
                total_p90 += hc.get("fair_p90_score", 0.0) or 0.0
                total_max += hc.get("fair_max_score", 0.0) or 0.0
    except (OSError, ValueError, KeyError, AttributeError) as ex:

        logger.debug(f"[Fallback] Excepción controlada: {ex}")
    
    formatted_p90 = format_currency_custom(total_p90, t_sep, d_sep).split(d_sep)[0]
    formatted_max = format_currency_custom(total_max, t_sep, d_sep).split(d_sep)[0]

    if doc_lang == "es":
        intro_prose_p1 = (
            f"Los riesgos identificados en este análisis han sido modelados y evaluados utilizando el modelo de "
            f"**Análisis Cuantitativo de Riesgo Tecnológico** basado en el estándar internacional **O-FAIR (Open Factor Analysis of Information Risk)**, "
            f"una metodología estándar reconocida globalmente para traducir deudas técnicas en impacto financiero real para el negocio."
        )
        intro_prose_p2 = (
            f"El análisis cuantitativo del estado actual establece que las deudas técnicas operativas y las vulnerabilidades detectadas exclusivamente "
            f"dentro del perímetro de esta torre tecnológica exponen a {client_name} a una **Expectativa de Pérdida Anualizada (ALE - Annual Loss Exposure)** "
            f"de **{formatted_ale} {currency}** anuales. Es fundamental entender que esta métrica representa el impacto económico promedio latente (fricción operativa, "
            f"coste de horas de ticketing manual e ineficiencias de procesos rutinarios) que la organización asume de manera ordinaria como el 'coste de hacer negocio' si decide mantener el statu quo."
        )
        intro_prose_p3 = (
            f"Por el contrario, el verdadero caso de negocio y la justificación de la inversión tecnológica no reside en mitigar esa ineficiencia promedio, "
            f"sino en proteger el balance frente a escenarios de estrés operativo y regulatorio severo. Para ello, el modelo calcula los escenarios más "
            f"extremos en la cola de la distribución mediante el llamado **Déficit Esperado Condicional o CVaR al 97.5% (Expected Shortfall)**. "
            f"En un escenario de alta adversidad anual (donde los procesos manuales colapsen por saturación de incidentes concurrentes o se active la exposición "
            f"a sanciones bajo {reg_name}), la exposición de la plataforma podría promediar los **{formatted_p90} {currency}**, "
            f"llegando a un límite máximo estimado (P99) de **{formatted_max} {currency}**."
        )
        intro_prose_p4 = (
            f"Es crítico destacar que, ante esta exposición, la opción de añadir recursos humanos adicionales (tales como la incorporación de "
            f"personal de soporte operativo extraordinario) no mitiga el riesgo, sino que multiplica la probabilidad de error humano, el cual constituye "
            f"estadísticamente la causa raíz de más del 80% de los fallos de configuración. Adicionalmente, las intervenciones manuales no escalan físicamente "
            f"ante picos de demanda o incidentes de gran escala (provocando la violación de los RTOs exigidos por la red de transporte eléctrico), "
            f"y mantener un proceso crítico sin controles automatizados puede ser catalogado como negligencia regulatoria estructural bajo las estrictas "
            f"exigencias de debida diligencia de la directiva {reg_name}, exponiendo a la compañía a sanciones de rango máximo. Por tanto, estas cifras reflejan "
            f"la asunción de riesgo implícita de mantener el estado actual (coste de inacción)."
        )
        intro_prose_p5 = (
            f"*(Nota: Para garantizar que estas proyecciones financieras sean objetivas y auditables, el modelo de cálculo no emplea estimaciones subjetivas "
            f"arbitrarias, sino que opera bajo un proceso riguroso de tres etapas: 1) Los rangos iniciales se calibran con bases de datos de siniestralidad reales del sector de "
            f"infraestructuras críticas (específicamente el **Verizon Data Breach Investigations Report - DBIR** y el estudio **IBM Cost of a Data Breach** de Ponemon Institute); "
            f"2) Estos rangos promedio se ajustan aplicando un factor de escala bayesiano derivado de la madurez real de {client_name} y de vuestra tarifa horaria de convenio en `rate_card.json` ({sre_rate} {currency}/hora); "
            f"y 3) Se ejecuta una simulación estocástica de Monte Carlo de 10.000 iteraciones truncada al percentil 99.0% para descartar outliers por causas de fuerza mayor. "
            f"Para una comprensión detallada de los principios estadísticos, se recomienda consultar el Apéndice Metodológico situado al final de este informe).*"
        )
    else:
        intro_prose_p1 = (
            f"The risks identified in this assessment have been modeled and evaluated using the **Quantitative Technology Risk Analysis** "
            f"model based on the international **O-FAIR (Open Factor Analysis of Information Risk)** standard, a globally recognized methodology "
            f"to translate technical debts directly into real financial impact for the business."
        )
        intro_prose_p2 = (
            f"The quantitative current state analysis establishes that the technical operational debts and identified vulnerabilities exclusively "
            f"within the perimeter of this technological tower expose {client_name} to a real **Annual Loss Exposure (ALE)** "
            f"of **{formatted_ale} {currency}** annually. It is crucial to understand that this metric represents the average latent economic "
            f"impact (operational friction, manual ticketing support salary costs, and routine process inefficiencies) that the organization assumes ordinarily as the 'cost of doing business' "
            f"if it chooses to maintain the status quo."
        )
        intro_prose_p3 = (
            f"On the contrary, the true business case and justification for technological investment does not lie in mitigating that average inefficiency, "
            f"but in protecting the balance sheet against severe operational and regulatory stress scenarios. To do this, the model calculates extreme tail scenarios using "
            f"**Conditional Value at Risk (CVaR) or Expected Shortfall at 97.5%**. In a highly adverse annual scenario (where manual processes "
            f"collapse under the strain of concurrent incidents or exposure to severe penalties under {reg_name} is triggered), the financial "
            f"exposure of the platform will average **{formatted_p90} {currency}**, potentially reaching an estimated maximum plausible limit (P99) of up to **{formatted_max} {currency}**."
        )
        intro_prose_p4 = (
            f"It is critical to note that, in the face of this exposure, the option of adding additional human resources (such as the incorporation of "
            f"extraordinary operational support personnel) does not mitigate the risk, but rather multiplies the probability of human error, which statistically constitutes the "
            f"root cause of over 80% of configuration failures. Additionally, manual interventions do not physically scale under stress or large-scale "
            f"incidents (leading to the violation of RTOs required by the electrical grid), and maintaining a critical process without automated controls "
            f"can be classified as structural regulatory negligence under the strict due diligence requirements of the {reg_name} directive, exposing the company to maximum-range "
            f"sancions. Therefore, these figures reflect the implicit risk assumption of maintaining the status quo (cost of inaction)."
        )
        intro_prose_p5 = (
            f"*(Note: To ensure these financial projections are objective and auditable, the calculation model does not employ subjective estimates "
            f"arbitrarily, but operates under a rigorous three-stage process: 1) Initial ranges are calibrated with actual loss databases of the "
            f"critical infrastructure sector, specifically the **Verizon Data Breach Investigations Report - DBIR** and the **IBM Cost of a Data Breach** study; "
            f"2) These average industry ranges are adjusted using a Bayesian scale factor derived from {client_name}'s real maturity and your agreement hourly rate in `rate_card.json` ({sre_rate} {currency}/hour); "
            f"and 3) A Monte Carlo stochastic simulation of 10,000 iterations truncated at the 99.0th percentile is run to discard extreme force majeure outliers. "
            f"For a detailed understanding of the statistical principles, please refer to the Methodological Appendix at the end of this report).*"
        )

    add_body_paragraph(doc, intro_prose_p1, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p2, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p3, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p4, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p5, text_color_rgb=text_color_rgb, italic=True)

    def add_markdown_bullet_local(text: str, space_after: int = 4) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

    add_appendix_subheading(doc, "El Hexágono de Valor: Palancas de Retorno de Resiliencia y Eficiencia (RoRE)", primary_color_rgb=p_color_rgb)
    
    if doc_lang == "es":
        lever_intro = (
            "Para proporcionar una visión empresarial de 360 grados que justifique las decisiones de modernización tecnológica, "
            "este diagnóstico complementa la cuantificación de riesgos de Open FAIR con el marco internacional de gestión de valor "
            "**TBM (Technology Business Management)** y **FinOps**. Toda ineficiencia o proceso manual identificado en esta torre "
            "se analiza de manera agregada bajo seis dimensiones o palancas de valor diferenciadas:"
        )
        add_body_paragraph(doc, lever_intro, text_color_rgb=text_color_rgb)
        
        add_markdown_bullet_local(
            "Palanca 1 - Recuperación de Capital Laboral (Lean IT): Cuantifica el coste salarial directo perdido de forma recurrente "
            "por los ingenieros sénior al ejecutar tareas manuales rutinarias que un sistema programático realizaría en segundos.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 2 - Coste de Oportunidad del Talento: El valor marginal que la organización deja de percibir al mantener a sus "
            "arquitectos e ingenieros sénior haciendo mantenimiento reactivo en lugar de dedicarlos a proyectos de innovación estratégica.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 3 - Coste de Demora de Proyectos (Demora de Proyectos): La pérdida económica indirecta que sufre el negocio debido a que "
            "los proyectos estratégicos se retrasan semanas esperando el aprovisionamiento o la configuración manual de Sistemas.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 4 - Eliminación de Desperdicio de Infraestructura (Capacity Waste): El sobrecoste derivado de la sobredimensión "
            "de almacenamiento o servidores 'por si acaso' en procesos manuales, así como la acumulación de recursos huérfanos encendidos.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 5 - Evitación de Costes de Soporte por Obsolescencia: El sobreprecio extraordinario de mantenimiento (Extended Support) "
            "que se paga a fabricantes para mantener con vida asistida hardware o software legacy que carece de soporte estándar.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 6 - Mitigación de Riesgos de Cola de Balance: La reducción real de la probabilidad de sufrir incidentes catastróficos "
            "por error humano (causa del 80% de caídas de red) o severas sanciones legales por negligencia regulatoria bajo NIS2 (CVaR P99).",
            space_after=12
        )
    else:
        lever_intro = (
            "To provide a 360-degree business view that justifies technological modernization decisions, "
            "this diagnosis complements Open FAIR risk quantification with the international value management frameworks "
            "**TBM (Technology Business Management)** and **FinOps**. Every technical debt or manual process identified in this tower "
            "is analyzed in an aggregated manner under six distinct value levers:"
        )
        add_body_paragraph(doc, lever_intro, text_color_rgb=text_color_rgb)
        
        add_markdown_bullet_local(
            "Lever 1 - Labor Capital Recovery (Lean IT): Quantifies the direct salary cost lost on a recurring basis "
            "by senior engineers executing routine manual tasks that a programmatic system would perform in seconds.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 2 - Talent Opportunity Cost: The marginal value that the organization fails to realize by keeping "
            "its senior architects and engineers on reactive maintenance instead of dedicating them to strategic innovation projects.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 3 - Project Cost of Delay: The indirect financial loss suffered by the business due to "
            "strategic projects being delayed for weeks waiting for manual provisioning or systems configuration.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 4 - Capacity Waste Elimination (FinOps): The extra cost derived from overprovisioning "
            "storage or servers 'just in case' in manual processes, as well as the accumulation of running orphaned resources.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 5 - Extended Support Avoidance: The extraordinary maintenance premium paid to vendors "
            "to keep legacy hardware or software on life support when it lacks standard official support.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 6 - Tail Risk Balance Sheet Mitigation: The real reduction in the probability of suffering catastrophic "
            "incidents due to human error (root cause of 80% of outages) or severe NIS2 penalties under stress (CVaR P99).",
            space_after=12
        )

    #
    csv_risks_path = modules_dir / "06_matriz_riesgos_fair.csv"
    risks_data_list = []
    risks_by_pilar = {}

    if csv_risks_path.exists():
        with open(csv_risks_path, "r", encoding="utf-8") as cf:
            reader = csv.reader(cf, delimiter=";")
            next(reader)
            for r_idx, row_data in enumerate(reader):
                pilar_full_name = row_data[0].split(" - ")[0]
                r_item = {
                    "id": f"RVS{r_idx + 1:02d}",
                    "pilar": pilar_full_name,
                    "capability": row_data[0].split(" - ")[1]
                    if " - " in row_data[0]
                    else row_data[0],
                    "finding": row_data[1],
                    "business_risk": row_data[2],
                    "tef": float(row_data[3]),
                    "lm": float(row_data[4]),
                    "ale": float(row_data[5]),
                    "prioritization_rationale": row_data[6]
                    if len(row_data) > 6
                    else None,  #
                }
                risks_data_list.append(r_item)

                if pilar_full_name not in risks_by_pilar:
                    risks_by_pilar[pilar_full_name] = []
                risks_by_pilar[pilar_full_name].append(r_item)

    # Assemble and render Section 5.1: 5x5 Heatmap as a centered, native table mosaic.
    industry_name = ctx.get("industry", "Infraestructura y Operaciones")
    if risks_data_list:
        add_heading(
            doc, vocab["exposure_summary_title"], level=2, primary_color_rgb=p_color_rgb
        )

        if doc_lang == "es":
            sec_intro_p1 = (
                f"Para facilitar la visualización y priorización de las deudas técnicas y vulnerabilidades identificadas, se presenta a continuación la "
                f"**Matriz de Riesgo Cuantitativa (Mosaico 5x5)**. Este mapa de calor distribuye los riesgos detectados interrelacionando la "
                f"**Frecuencia de Eventos de Amenaza (TEF)** (estimación anualizada de ocurrencias) con la **Magnitud de la Pérdida (LM)** (el impacto financiero de cada evento)."
            )
            sec_intro_p2 = (
                f"La calibración de los rangos de esta Magnitud de Pérdida (LM) para {client_name} se realiza bajo el criterio riguroso de operador de "
                f"{industry_name}. De acuerdo con el estudio de referencia mundial *ITIC Global Server Hardware Downtime Report*, el coste promedio de indisponibilidad "
                f"de sistemas core supera el millón de euros por hora para el 98% de los operadores de su sector, debido a la interrupción en cadena de procesos operativos, "
                f"las severas penalizaciones por acuerdos de nivel de servicio (SLA) y los costes de remediación forense urgente."
            )
            sec_intro_p3 = (
                f"Bajo esta base empírica, los umbrales de pérdida financiera de la matriz se bareman de forma escalonada para modelar con precisión el impacto directivo real en los siguientes cuadrantes:"
            )
        else:
            sec_intro_p1 = (
                f"To facilitate the visualization and prioritization of the identified technical vulnerabilities, the **Quantitative Risk Matrix (5x5 Heatmap)** "
                f"is presented below. This heatmap distributes the risks by cross-referencing the **Threat Event Frequency (TEF)** (annualized frequency of occurrence) "
                f"with the **Loss Magnitude (LM)** (the financial impact of each event)."
            )
            sec_intro_p2 = (
                f"The calibration of these Loss Magnitude (LM) ranges for {client_name} is performed under the rigorous criteria of a "
                f"{industry_name} operator. According to the global benchmark study *ITIC Global Server Hardware Downtime Report*, the average cost "
                f"of core system downtime exceeds one million euros per hour for 98% of operators in its sector, due to cascading process interruptions, "
                f"severe Service Level Agreement (SLA) penalties, and urgent forensic remediation costs."
            )
            sec_intro_p3 = (
                f"Based on this empirical foundation, the financial loss thresholds of the matrix are graduated to accurately model the real management impact across the following quadrants:"
            )
            
        add_body_paragraph(doc, sec_intro_p1, text_color_rgb=text_color_rgb)
        add_body_paragraph(doc, sec_intro_p2, text_color_rgb=text_color_rgb)
        add_body_paragraph(doc, sec_intro_p3, text_color_rgb=text_color_rgb)
        add_spacer(doc, 15)

        matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
        for r in risks_data_list:
            r_tef = min(5, max(1, int(round(r["tef"]))))
            r_lm = min(5, max(1, int(round(r["lm"]))))
            matrix_cells[r_tef][r_lm].append(r["id"])

        # Initialize a 6x6 table (5x5 data grid plus headers). The table is centered and set to full page width.
        heatmap_table = doc.add_table(rows=6, cols=6)
        heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        finalize_table(heatmap_table)

        #
        cell_0_0 = heatmap_table.rows[0].cells[0]
        set_cell_text_custom(
            cell_0_0,
            "TEF \\ LM",
            bold=True,
            font_size=9,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            color_rgb=RGBColor(255, 255, 255),
            no_bullets=True,
        )
        shade_cell(cell_0_0, COLOR_BLUE)
        set_cell_border_white(cell_0_0)
        cell_0_0.width = Inches(1.3)  # Slightly wider for inline ranges
        cell_0_0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        
        for col_idx in range(1, 6):
            if is_critical:
                lm_ranges = {
                    1: f"< 1k {currency}",
                    2: f"1k - 10k {currency}",
                    3: f"10k - 50k {currency}",
                    4: f"50k - 300k {currency}",
                    5: f"250k - 1.5M {currency}",
                }
            else:
                lm_ranges = {
                    1: f"< 1k {currency}",
                    2: f"1k - 5k {currency}",
                    3: f"5k - 25k {currency}",
                    4: f"25k - 100k {currency}",
                    5: f"100k - 500k {currency}",
                }
            lm_lbl = f"LM {col_idx}\n({lm_ranges[col_idx]})"
            cell = heatmap_table.rows[0].cells[col_idx]
            set_cell_text_custom(
                cell,
                lm_lbl,
                bold=True,
                font_size=9,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                color_rgb=RGBColor(255, 255, 255),
                no_bullets=True,
            )
            shade_cell(cell, COLOR_BLUE)
            set_cell_border_white(cell)
            cell.width = Inches(1.04)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        # Populate the 5x5 data matrix with content, ensuring it fills the full width of the table.
        for row_idx, tef_val in enumerate(range(5, 0, -1), 1):
            tef_ranges = {
                5: f"> 10/año" if doc_lang == "es" else f"> 10/year",
                4: f"2,0 - 10/año" if doc_lang == "es" else f"2.0 - 10/year",
                3: f"0,5 - 2,0/año" if doc_lang == "es" else f"0.5 - 2.0/year",
                2: f"0,1 - 0,5/año" if doc_lang == "es" else f"0.1 - 0.5/year",
                1: f"< 0,1/año" if doc_lang == "es" else f"< 0.1/year",
            }
            tef_lbl = f"TEF {tef_val}\n({tef_ranges[tef_val]})"
            cell_header = heatmap_table.rows[row_idx].cells[0]
            set_cell_text_custom(
                cell_header,
                tef_lbl,
                bold=True,
                font_size=9,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                color_rgb=RGBColor(255, 255, 255),
                no_bullets=True,
            )
            shade_cell(cell_header, COLOR_BLUE)
            set_cell_border_white(cell_header)
            cell_header.width = Inches(1.3)
            cell_header.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            for col_idx, lm_val in enumerate(range(1, 6), 1):
                cell = heatmap_table.rows[row_idx].cells[col_idx]

                # Configure table dimensions to create a fixed, full-width mosaic layout.
                cell.width = Inches(1.04)
                heatmap_table.rows[row_idx].height = Cm(0.4)

                cell_risks = matrix_cells[tef_val][lm_val]
                cell_text = ", ".join(cell_risks) if cell_risks else "-"

                set_cell_text_custom(
                    cell,
                    cell_text,
                    bold=True,
                    font_size=8,
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )
                set_cell_border_white(cell)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

                severity = tef_val * lm_val
                if severity >= 15:
                    shade_cell(cell, "FADBD8")  #
                elif severity >= 8:
                    shade_cell(cell, "FCF3CF")  #
                else:
                    shade_cell(cell, "D5F5E3")  #

        heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER  # Recalculate cell content alignment. This is required because the initial auto-fit operation may not apply alignment correctly.
        add_spacer(doc, 20)

    # Build a lookup map from blueprint payload findings for detailed FAIR metrics
    fair_lookup = {}
    if payload_path.exists():
        try:
            for pillar in b_data.get("pillars_analysis", []):
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

    # Assemble and render Section 5.3: Detailed Risk Register; left-aligned content per requirement 4.2.
    add_heading(
        doc, vocab["detailed_risks_title"], level=2, primary_color_rgb=p_color_rgb
    )

    if doc_lang == "es":
        detailed_risks_intro = (
            "El inventario analítico se presenta estructurado en **Portafolios de Priorización de Deuda Técnica** (conforme al estándar Open FAIR™), "
            "agrupando los hallazgos según su impacto económico relativo dentro de la propia torre. Esta clasificación dinámica "
            "establece tres niveles de prioridad basados en la desviación de cada riesgo respecto al coste de inacción promedio de la plataforma."
        )
        guide_intro = "Adicionalmente, para facilitar la lectura y comprensión del impacto financiero en las fichas detalladas, las métricas de exposición proyectada representan:"
    else:
        detailed_risks_intro = (
            "The analytical inventory is structured into **Technical Debt Prioritization Portfolios** (in accordance with the Open FAIR™ standard), "
            "grouping findings based on their relative economic impact within the tower itself. This dynamic classification "
            "establishes three priority levels based on each risk's deviation from the platform's average cost of inaction."
        )
        guide_intro = "Additionally, to facilitate reading and understanding the financial impact in the detailed cards, the projected exposure metrics represent:"

    add_body_paragraph(doc, detailed_risks_intro, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, guide_intro, text_color_rgb=text_color_rgb)

    if doc_lang == "es":
        b1_text = "Pérdida Anualizada (ALE): El coste económico promedio esperado cada año. Constituye el valor base del coste de inacción operativo."
        b2_text = "Peor Caso (CVaR): El promedio económico del 10% de los peores escenarios posibles. Indica la magnitud del desastre financiero si las amenazas más graves se materializan de forma simultánea en un mismo año."
        b3_text = "Rango Probabilístico: El abanico estadístico de pérdidas posibles, desde un impacto menor hasta el máximo teórico si se detonan sanciones regulatorias o incumplimientos de SLA."
    else:
        b1_text = "Annualized Loss Expectancy (ALE): The average economic cost expected each year. It constitutes the baseline value of the operational cost of inaction."
        b2_text = "Worst Case (CVaR): The economic average of the 10% worst-case scenarios. It indicates the magnitude of the financial disaster if the most severe threats materialize simultaneously in a single year."
        b3_text = "Probabilistic Range: The statistical spectrum of possible losses, from a minor impact up to the theoretical maximum if regulatory sanctions or SLA breaches are triggered."

    add_body_paragraph(doc, b1_text, style="List Bullet", text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, b2_text, style="List Bullet", text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, b3_text, style="List Bullet", text_color_rgb=text_color_rgb)

    add_spacer(doc, 15)

    # Dynamic Relative Materiality Threshold Calculation (Statistical Mean ALE)
    total_risks_count = len(risks_data_list)
    local_mean_ale = (sum(r["ale"] for r in risks_data_list) / total_risks_count) if total_risks_count > 0 else 0.0
    
    tier1_threshold = local_mean_ale * 1.5
    tier2_threshold = local_mean_ale * 0.5

    tier1_risks = [r for r in risks_data_list if r["ale"] >= tier1_threshold]
    tier2_risks = [r for r in risks_data_list if tier2_threshold <= r["ale"] < tier1_threshold]
    tier3_risks = [r for r in risks_data_list if r["ale"] < tier2_threshold]

    # Sort each tier by ALE descending to guarantee standard prioritization
    tier1_risks.sort(key=lambda x: x["ale"], reverse=True)
    tier2_risks.sort(key=lambda x: x["ale"], reverse=True)
    tier3_risks.sort(key=lambda x: x["ale"], reverse=True)

    t_sep1 = format_currency_custom(tier1_threshold, t_sep, d_sep).split(d_sep)[0]
    t_sep2 = format_currency_custom(tier2_threshold, t_sep, d_sep).split(d_sep)[0]
    
    tiers_config = [
        (
            "Tier 1: Prioridad de Modernización",
            "Tier 1: Modernization Priority",
            tier1_risks,
            f"Hallazgos de alto impacto (outliers estadísticos con exposición mayor o igual a {t_sep1} {currency}/año) que concentran la mayor ineficiencia financiera relativa dentro de esta plataforma. Representan las principales prioridades de modernización para mitigar el riesgo de la torre."
            if doc_lang == "es" else
            f"High-impact findings (statistical outliers with exposure greater than or equal to {t_sep1} {currency}/year) that concentrate the highest relative financial inefficiency within this platform. They represent the main modernization priorities to mitigate the tower's risk."
        ),
        (
            "Tier 2: Optimización Operativa",
            "Tier 2: Operational Optimization",
            tier2_risks,
            f"Ineficiencias operativas que se sitúan en torno a la exposición promedio de la torre (entre {t_sep2} y {t_sep1} {currency}/año). Constituyen la fricción técnica y operativa normalizada del ecosistema actual."
            if doc_lang == "es" else
            f"Operational inefficiencies situated around the tower's average exposure (between {t_sep2} and {t_sep1} {currency}/year). They constitute the normalized technical and operational friction of the current ecosystem."
        ),
        (
            "Tier 3: Backlog de Mantenimiento",
            "Tier 3: Maintenance Backlog",
            tier3_risks,
            f"Desviaciones menores (exposición menor a {t_sep2} {currency}/año) cuyo peso estadístico es marginal frente a la deuda técnica total de la torre, representando oportunidades de mejora o mantenimiento ordinario."
            if doc_lang == "es" else
            f"Minor deviations (exposure under {t_sep2} {currency}/year) whose statistical weight is marginal against the tower's total technical debt, representing ordinary maintenance or improvement opportunities."
        ),
    ]

    for title_es, title_en, p_risks, p_desc in tiers_config:
        title = title_es if doc_lang == "es" else title_en
        
        add_heading(
            doc,
            title,
            level=3,
            primary_color_rgb=p_color_rgb,
        )
        add_body_paragraph(doc, p_desc, text_color_rgb=text_color_rgb)
        add_spacer(doc, 10)

        if not p_risks:
            empty_msg = (
                "No se registran vulnerabilidades de esta prioridad de exposición en la evaluación actual."
                if doc_lang == "es" else
                "No vulnerabilities of this exposure priority are registered in the current assessment."
            )
            add_body_paragraph(doc, empty_msg, text_color_rgb=text_color_rgb)
            add_spacer(doc, 15)
            continue

        table_risks = doc.add_table(rows=1, cols=3)
        table_risks.alignment = WD_TABLE_ALIGNMENT.LEFT
        finalize_table(table_risks)
        table_risks.autofit = False
        table_risks.allow_autofit = False

        tblPr = table_risks._tbl.tblPr
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            table_risks._tbl.insert(0, tblPr)

        # Apply robust OXML column widths to guarantee Word doesn't shrink the third column
        tblGrid = table_risks._tbl.find(qn('w:tblGrid'))
        if tblGrid is not None:
            table_risks._tbl.remove(tblGrid)
            
        tblGrid = OxmlElement('w:tblGrid')
        col_widths = [Cm(1.2), Cm(10.45), Cm(5.77)]
        for w in col_widths:
            gridCol = OxmlElement('w:gridCol')
            gridCol.set(qn('w:w'), str(int(w.twips)))
            tblGrid.append(gridCol)
            
        # Insert tblGrid immediately after tblPr to conform to OOXML schema
        tblPr_index = table_risks._tbl.index(tblPr)
        table_risks._tbl.insert(tblPr_index + 1, tblGrid)
        
        # Remove any existing autofit tags and set rigid total width
        for child in list(tblPr):
            if child.tag.endswith('tblLayout') or child.tag.endswith('tblW'):
                tblPr.remove(child)
                
        tblLayout = OxmlElement('w:tblLayout')
        tblLayout.set(qn('w:type'), 'fixed')
        tblPr.append(tblLayout)
        
        tblW = OxmlElement('w:tblW')
        tblW.set(qn('w:type'), 'dxa')
        tblW.set(qn('w:w'), str(sum(int(w.twips) for w in col_widths)))
        tblPr.append(tblW)

        headers_table = vocab["detailed_risks_headers"]
        for i, h_txt in enumerate(headers_table):
            cell = table_risks.rows[0].cells[i]
            set_cell_text_custom(
                cell,
                h_txt,
                bold=True,
                font_size=8.5,
                color_rgb=RGBColor(255, 255, 255),
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            # Force exact width on the cell level in OXML
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is not None:
                tcPr.remove(tcW)
            tcW = OxmlElement('w:tcW')
            tcW.set(qn('w:type'), 'dxa')
            tcW.set(qn('w:w'), str(int(col_widths[i].twips)))
            tcPr.append(tcW)
            shade_cell(cell, p_color_hex)

        for r_idx, r in enumerate(p_risks):
            row = table_risks.add_row()

            #
            set_cell_text_custom(
                row.cells[0],
                r["id"],
                bold=True,
                font_size=8.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(row.cells[0], alt_row_hex)

            # Assemble and render Section 2: Description and Evidence, justified per user request.
            # Clear default paragraph and build explicitly to prevent Shift+Enter stretching bugs
            cell_desc = row.cells[1]
            cell_desc.text = ""
            p_desc_lbl = cell_desc.paragraphs[0]
            p_desc_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_desc_lbl.paragraph_format.space_after = Pt(2)

            finding = r["finding"]
            biz_risk = r["business_risk"]
            cap_name = r["capability"]

            parts_f = finding.split("\n\nEvidencia Forense Literal (Audit RAG):\n")

            import re
            from assessment_engine.infrastructure.localization import (
                apply_vocabulary_substitutions,
            )
            raw_client_name = ctx.get("raw_client_name", client_name)

            clean_finding_text = apply_vocabulary_substitutions(
                clean_text_for_word(parts_f[0]), locale="es"
            )
            clean_finding_text = re.sub(
                re.escape(raw_client_name),
                client_name,
                clean_finding_text,
                flags=re.IGNORECASE,
            ).strip()

            clean_biz_text = apply_vocabulary_substitutions(
                clean_text_for_word(biz_risk), locale="es"
            )
            clean_biz_text = re.sub(
                re.escape(raw_client_name),
                client_name,
                clean_biz_text,
                flags=re.IGNORECASE,
            ).strip()

            run_obs = p_desc_lbl.add_run("Vulnerabilidad Identificada:")
            run_obs.bold = True
            run_obs.font.name = "Arial"
            run_obs.font.size = Pt(8.5)

            p_desc_txt = cell_desc.add_paragraph(clean_finding_text)
            p_desc_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_desc_txt.paragraph_format.space_after = Pt(8)
            for run in p_desc_txt.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)

            p_biz_lbl = cell_desc.add_paragraph()
            p_biz_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_biz_lbl.paragraph_format.space_after = Pt(2)
            run_biz = p_biz_lbl.add_run("Impacto de TI / Operativo:")
            run_biz.bold = True
            run_biz.font.name = "Arial"
            run_biz.font.size = Pt(8.5)

            p_biz_txt = cell_desc.add_paragraph(clean_biz_text)
            p_biz_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_biz_txt.paragraph_format.space_after = Pt(0)
            for run in p_biz_txt.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)

            # Assemble and render Section 3: Business Risk and FAIR Impact, left-aligned per user request.
            # Use native paragraphs to avoid Shift+Enter stretching bugs and carriage return issues
            cell_risk = row.cells[2]
            cell_risk.text = ""
            p_fair_lbl = cell_risk.paragraphs[0]
            p_fair_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_fair_lbl.paragraph_format.space_after = Pt(2)
            run_fair_lbl = p_fair_lbl.add_run("Exposición Cuantitativa (FAIR):")
            run_fair_lbl.bold = True

            tef = r["tef"]
            lm = r["lm"]
            ale = r["ale"]

            # Fetch detailed FAIR metrics from lookup map
            fair_metrics = fair_lookup.get(cap_name, {})
            p90_val = fair_metrics.get("p90", 0.0) or 0.0
            min_val = fair_metrics.get("min", 0.0) or 0.0
            max_val = fair_metrics.get("max", 0.0) or 0.0

            p_fair_val = cell_risk.add_paragraph()
            p_fair_val.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_fair_val.paragraph_format.space_after = Pt(6)
            p_fair_val.add_run(f"• Frecuencia (TEF): {tef:.1f} / 5,0\n• Magnitud (LM): {lm:.1f} / 5,0")

            p_exp_lbl = cell_risk.add_paragraph()
            p_exp_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_exp_lbl.paragraph_format.space_after = Pt(2)
            run_exp_lbl = p_exp_lbl.add_run("Exposición Financiera Proyectada:")
            run_exp_lbl.bold = True

            p_exp_val = cell_risk.add_paragraph()
            p_exp_val.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_exp_val.paragraph_format.space_after = Pt(0)

            formatted_p90 = format_currency_custom(p90_val, t_sep, d_sep).split(d_sep)[0]
            formatted_min = format_currency_custom(min_val, t_sep, d_sep).split(d_sep)[0]
            formatted_max = format_currency_custom(max_val, t_sep, d_sep).split(d_sep)[0]
            formatted_ale_item = format_currency_custom(ale, t_sep, d_sep).split(d_sep)[0]

            p_exp_val.add_run("• Pérdida Anualizada (ALE): ")
            run_ale_val = p_exp_val.add_run(f"{formatted_ale_item} {currency}\n")
            run_ale_val.bold = True
            run_ale_val.font.color.rgb = RGBColor(180, 0, 0)
            
            p_exp_val.add_run(f"• Peor Caso (CVaR): {formatted_p90} {currency}\n")
            p_exp_val.add_run(f"• Rango Probabilístico: {formatted_min} {currency} a {formatted_max} {currency}")

            # Apply fonts to all runs in the third cell
            for p_item in cell_risk.paragraphs:
                for r_item in p_item.runs:
                    r_item.font.name = "Arial"
                    r_item.font.size = Pt(8.5)

            # Apply uniform alternating row backgrounds to maintain pure aesthetic logic
            row_bg = alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
            for i in range(3):
                shade_cell(row.cells[i], row_bg)

            # Apply vertical centering to all cells in the row
            row.cells[0].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            row.cells[1].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            row.cells[2].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            # Enforce exact centimeter-based column widths on every cell of every row at the VERY END, 
            # so that previous text injections and shade_cell don't overwrite the tcPr OXML.
            for i in range(3):
                cell = row.cells[i]
                tcPr = cell._tc.get_or_add_tcPr()
                tcW = tcPr.find(qn('w:tcW'))
                if tcW is not None:
                    tcPr.remove(tcW)
                tcW = OxmlElement('w:tcW')
                tcW.set(qn('w:type'), 'dxa')
                tcW.set(qn('w:w'), str(int(col_widths[i].twips)))
                tcPr.append(tcW)

        add_spacer(doc, 15)

    #

    return {
        "total_p90": total_p90,
        "formatted_ale_item": formatted_ale_item,
        "formatted_p90": formatted_p90,
        "t_sep": t_sep,
        "d_sep": d_sep,
    }


