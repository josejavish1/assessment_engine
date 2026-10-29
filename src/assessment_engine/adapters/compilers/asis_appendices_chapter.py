"""Technical appendices and regulatory disclaimers builder for Word DOCX."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Inches, Pt, RGBColor

from assessment_engine.infrastructure.docx_render_utils import (
    autofit_table_to_contents,
    finalize_table,
    shade_cell,
)
from assessment_engine.infrastructure.localization import (
    format_currency,
    format_number,
    t,
)
from assessment_engine.adapters.compilers.asis_docx_primitives import (
    DocumentCompilationContext,
    _add_markdown_bullet,
    add_appendix_heading,
    add_appendix_subheading,
    add_body_paragraph,
    add_spacer,
    format_currency_custom,
    set_cell_border_white,
    set_cell_text_custom,
)

logger = logging.getLogger(__name__)

def _compile_appendices(doc: Any, ctx: DocumentCompilationContext) -> None:
    """Assemble and render Appendices A, B, C, and D."""
    p_color_rgb = ctx["p_color_rgb"]
    text_color_rgb = ctx["text_color_rgb"]
    p_color_hex = ctx["p_color_hex"]
    alt_row_hex = ctx["alt_row_hex"]
    currency = ctx["currency"]
    is_critical = ctx["is_critical"]
    industry = ctx["industry"]
    doc_lang = ctx["doc_lang"]
    company_name = ctx["company_name"]
    client_name = ctx["client_name"]
    tower_name = ctx["tower_name"]
    tower_dir_obj = ctx["tower_dir_obj"]
    modules_dir = ctx["modules_dir"]
    vocab = ctx["vocab"]
    payload_path = ctx["payload_path"]
    b_data = ctx.get("b_data", {})

    def add_markdown_bullet_local(text: str, space_after: int = 4) -> Any:
        return _add_markdown_bullet(doc, text, text_color_rgb, space_after)

    # Assemble and render Appendix A: Quantitative Risk Methodology
    #
    add_appendix_heading(doc, "Metodología Cuantitativa de Riesgos", primary_color_rgb=p_color_rgb)
    add_body_paragraph(
        doc,
        "Este apéndice detalla el rigor metodológico, las ecuaciones estadísticas y los supuestos actuariales de "
        "calibración aplicados para sustentar las evaluaciones de riesgo de este informe. El objetivo de esta sección "
        "es blindar la validez de las proyecciones de costes frente a cualquier proceso de auditoría y, a la vez, "
        "explicar de manera sencilla y transparente cómo se conectan las deudas tecnológicas con el impacto financiero real.",
        text_color_rgb=text_color_rgb
    )

    # Detect if the organization operates in a regulated critical sector to apply custom parameters
    is_critical_client = is_critical if is_critical is not None else True
    
    # standard Actuarial Practice: Dynamic Regulatory Mapping (Industry Routing)
    # The regulatory framework narrative is mapped dynamically to the client's industry sector.
    if "Financial" in industry or "Banking" in industry:
        reg_name = "las regulaciones vigentes de resiliencia operativa financiera (v.g. DORA o normativas de banca central)"
        reg_fine_limit = f"15.000.000 {currency}"
    elif "Energy" in industry or "Critical Infrastructure" in industry:
        reg_name = "los marcos normativos de protección de infraestructuras críticas (v.g. Directiva NIS2 o leyes de seguridad nacional)"
        reg_fine_limit = f"10.000.000 {currency}"
    elif "Telecommunications" in industry or "Media" in industry:
        reg_name = "los marcos regulatorios sectoriales de Telecomunicaciones, Media y soberanía de datos"
        reg_fine_limit = f"5.000.000 {currency}"
    elif "Healthcare" in industry:
        reg_name = "las regulaciones de protección de datos de salud y privacidad (v.g. HIPAA o marcos locales equivalentes)"
        reg_fine_limit = f"5.000.000 {currency}"
    else:
        reg_name = "los marcos generales de protección de datos y privacidad (v.g. RGPD o legislación sectorial estándar)"
        reg_fine_limit = f"2.000.000 {currency}"

    # Section 1: Quantitative Rationale
    add_appendix_subheading(doc, "Limitaciones del Análisis Cualitativo frente a Open FAIR™", primary_color_rgb=p_color_rgb)
    p_why = (
        "Las metodologías tradicionales de evaluación de riesgos en TI, fundamentadas en análisis cualitativos de "
        "impacto y probabilidad (como las matrices de rango alto/medio/bajo), constituyen un valioso punto de partida para "
        "identificar y clasificar de forma temprana las superficies de vulnerabilidad de una organización. No obstante, para "
        "facilitar la toma de decisiones presupuestarias y justificar la rentabilidad de las inversiones tecnológicas (ROI), "
        "es necesario complementar estos marcos de referencia con un enfoque cuantitativo avanzado. Este diagnóstico "
        "adopta de forma complementaria la metodología estándar **Open FAIR™ (Factor Analysis of Information Risk)** "
        "(reconocida por *The Open Group* e incorporada en marcos normativos como ISO/IEC 27005), aportando una metodología "
        "rigurosa para modelar e identificar la exposición financiera real de la plataforma ante eventos de riesgo."
    )
    add_body_paragraph(doc, p_why, text_color_rgb=text_color_rgb)

    # Section 2: Dual-Layer Calibration Model
    add_appendix_subheading(doc, "El Modelo de Calibración Actuarial de Doble Capa", primary_color_rgb=p_color_rgb)
    p_layer_intro = (
        "Con el fin de comprender de forma intuitiva cómo una deficiencia técnica se propaga hasta impactar en el "
        "balance de la compañía, resulta de gran utilidad seguir paso a paso la cronología de un único evento de amenaza. "
        "A este recorrido lo denominamos 'La Biografía del Incidente'. Imaginemos, a modo de ejemplo ilustrativo, "
        f"un escenario de crisis en la torre de {tower_name}: un fallo operativo severo originado por una "
        "debilidad técnica previamente diagnosticada en esta auditoría. La propagación financiera "
        "de este incidente se rige por un modelo actuarial de doble capa:"
    )
    add_body_paragraph(doc, p_layer_intro, text_color_rgb=text_color_rgb)

    # Local inline Markdown parser to cleanly render bold (**) and italics (_) inside Appendix D bullet points,
    # completely eliminating raw asterisks and styling math variables beautifully.
    # Note: Function body is defined early in compile_docx to avoid scope conflicts.

    add_markdown_bullet_local(
        "Capa 1: Modelado de Vulnerabilidad (Garantía FAIR-CAM™) - Calibración Estocástica de Eficacia Defensiva: El incidente se inicia "
        "con la materialización de un evento de amenaza (v.g. un fallo operativo o desalineación en la capa de virtualización). En este "
        "instante, el evento choca contra las barreras de control de la organización. La probabilidad de que la amenaza supere estas "
        "salvaguardas y cause una pérdida real se define técnicamente como Vulnerabilidad (_VULN_). Nuestro motor aplica el estándar "
        "**FAIR-CAM™ (Control Analytics Model)** para calibrar esta probabilidad en función de la madurez real auditada en el Capítulo 3. "
        "Si la capacidad se sitúa en un nivel reactivo o inmaduro (Nivel 1 o 2), las barreras de control exhiben fallas estructurales severas, "
        "permitiendo el filtrado de la amenaza y detonando de inmediato **Pérdidas Primarias** (costes de respuesta de emergencia, "
        "horas de ingeniería extraordinaria de restauración e interrupción directa del negocio), cuyo coste de severidad "
        "es modelado estocásticamente mediante curvas continuas lognormales. Con el objetivo de distinguir matemáticamente las vulnerabilidades de riesgo estructural frente a ineficiencias rutinarias, "
        "el modelo aplica una **segregación tipológica**: si la deficiencia es de fricción operativa pura (ej. uso de hojas de cálculo o procesos ITSM lentos), "
        "el impacto se acota a un límite estricto de OPEX, garantizando proyecciones financieras realistas y contenidas.",
        space_after=4
    )

    add_markdown_bullet_local(
        f"Capa 2: Exposición Secundaria y Diligencia Debida (Garantía FAIR-MAM™) - Propagación Condicional de la Exposición Reguladora: "
        f"Una vez materializada la pérdida primaria, se activa de forma secuencial una segunda capa de exposición reguladora y "
        f"contractual basada en la demostración de la 'diligencia debida' (compliance). Utilizando la metodología **FAIR-MAM™ (Materiality Analytics Model)**, "
        f"el motor simula el desencadenamiento de **Pérdidas Secundarias** catastróficas (sanciones bajo {reg_name} de hasta "
        f"{reg_fine_limit} o reclamaciones por incumplimiento severo de SLAs). Esta propagación no utiliza saltos binarios arbitrarios, "
        f"sino que se modela mediante una **curva de transición logística continua** anclada en el nivel de madurez. A medida que la "
        f"madurez técnica decae por debajo del **Nivel 3 (Definido - score < 2,60)**, se asume una omisión estructural de diligencia, "
        f"disparando la probabilidad estocástica de sanción de forma asintótica hacia un techo del **15%**. Por el contrario, a medida que la capacidad "
        f"consolida el Nivel 3 o superior, la organización puede probar documentalmente su debida diligencia ante el regulador, "
        f"desplomando suavemente dicha probabilidad penalizadora hacia un suelo residual del **2%** de manera justificada.",
        space_after=12
    )

    # Section 3: Actuarial Simulation Core
    add_appendix_subheading(doc, "El Núcleo de Simulación Actuarial", primary_color_rgb=p_color_rgb)
    p_mc_intro = (
        "Más allá de la lógica conceptual, el verdadero valor diferencial de este diagnóstico reside en su arquitectura matemática. "
        "El motor de riesgo no emplea promedios estáticos, sino que ejecuta una **Simulación de Monte Carlo de 10.000 iteraciones** "
        "impulsada por un **Proceso de Riesgo Colectivo Compuesto de Dos Etapas**. Este núcleo de cálculo, diseñado bajo los "
        "estándares de la banca de inversión (Basilea III), modela la complejidad real del ciberespacio:"
    )
    add_body_paragraph(doc, p_mc_intro, text_color_rgb=text_color_rgb)

    add_markdown_bullet_local(
        "La Elicitación de Expertos (Consenso Adversarial Multi-Agente): Previo a la simulación matemática, el motor aplica un proceso de actualización bayesiana para adaptar las curvas de probabilidad teóricas a la realidad operativa de la organización. Mediante un panel automatizado de Inteligencia Artificial que debate desde perspectivas adversariales (viabilidad operativa vs. riesgo catastrófico), se deducen atenuantes topológicos (como el aislamiento de redes OT) y se separa la fricción técnica ordinaria del riesgo regulatorio. Este proceso simula de forma auditable la Elicitación de Expertos en la Materia (SME Elicitation) requerida por el estándar FAIR™, generando multiplicadores de descuento (Priors Bayesianos) que calibran el modelo y evitan el doble conteo de riesgos antes de inyectarlos en el núcleo estocástico.",
        space_after=4
    )

    add_markdown_bullet_local(
        "La Frecuencia de Amenazas - El Contagio (Distribución Binomial Negativa): En lugar de asumir una frecuencia fija o eventos aleatorios independientes (Poisson), "
        "el motor simula el número de amenazas anuales (_n_) mediante una **Distribución Binomial Negativa**. Este modelo captura la sobre-dispersión empírica de "
        "los ciberataques, donde un intento fallido suele preceder a una oleada concentrada de incidentes (clustering). "
        "La tasa media (_λ_) no es estática; se muestrea de una distribución de incertidumbre calibrada mediante **Elicitación de Expertos (Expert Elicitation)**, "
        "anclada en heurísticas de inteligencia de amenazas sectoriales y taxonomías de vulnerabilidad conocidas.",
        space_after=4
    )

    add_markdown_bullet_local(
        "El Pararrayos de Control - El Éxito o Fallo (Distribución Binomial): Para cada una de las amenazas simuladas (_n_), el ordenador "
        "simula si nuestras defensas reales desvían el impacto o fallan. El número final de pérdidas reales (_k_) sigue una distribución "
        "binomial (expresada matemáticamente como _k ~ Binomial(n, VULN)_). La vulnerabilidad (_VULN_) se correlaciona con la madurez "
        "técnica del Capítulo 3 mediante una **función de decadencia logística**, reflejando matemáticamente el desplome exponencial de eficacia defensiva cuando los controles caen por debajo de los estándares definidos.",
        space_after=4
    )

    add_markdown_bullet_local(
        f"La Severidad de Pérdidas - El Coste (Distribución Lognormal de Colas Pesadas): Para modelar el coste de reparación técnica y las posibles "
        f"multas secundarias, el motor emplea una **Distribución Lognormal**. Ante la ausencia de series temporales empíricas masivas del cliente, esta curva actúa como una "
        f"**Aproximación Conservadora de Valores Extremos (EVT)** para modelar impactos financieros con colas pesadas. Los parámetros de la curva (_μ_, _σ_) se ajustan estocásticamente. "
        f"Para evitar la inestabilidad estadística de simulaciones infinitas, el modelo realiza un truncamiento matemático (soft truncation) en el límite legal correspondiente "
        f"(hasta {reg_fine_limit}), forzando la convergencia estable de la Expectativa de Pérdida Anualizada (ALE) bajo el Teorema del Límite Central.",
        space_after=4
    )

    add_markdown_bullet_local(
        "Correlación Multivariante (Cópula Gaussiana Direccional): En el mundo real, un daño técnico severo eleva de forma casi determinista la probabilidad de sufrir "
        "una sanción regulatoria grave. Para evitar infravalorar eventos catastróficos, el motor no suma costes de forma independiente. Utiliza el Teorema de Sklar "
        "y una **Cópula Gaussiana** para inyectar una Dependencia de Cola asimétrica. Esto vincula causalmente las matrices de pérdida primaria y secundaria, "
        "garantizando que la distribución financiera final refleje el riesgo estructural compuesto con precisión absoluta.",
        space_after=12
    )

    # Section 4: Decision Metrics
    add_appendix_subheading(doc, "Definición de Métricas Decisionales de Exposición Financiera", primary_color_rgb=p_color_rgb)
    p_metrics_intro = (
        "Al integrar y ordenar los resultados de las 10.000 iteraciones de simulación virtual, el motor genera la distribución "
        "acumulada de pérdidas de la plataforma. De esta distribución se derivan matemáticamente las tres métricas decisionales "
        "que permiten al Consejo justificar las inversiones de mitigación:"
    )
    add_body_paragraph(doc, p_metrics_intro, text_color_rgb=text_color_rgb)

    p_m1 = add_markdown_bullet_local(
        "Pérdida Anualizada (ALE - Annual Loss Exposure): Representa la media aritmética de todos los escenarios de pérdida anualizada agregados. "
        "Es el impacto económico promedio latente que la organización experimenta cada año si decide mantener el statu quo (coste de inacción).",
        space_after=4
    )

    p_m2 = add_markdown_bullet_local(
        "Déficit Esperado Condicional (CVaR / Expected Shortfall): Representa el promedio matemático del 2.5% de los peores escenarios de la distribución de pérdidas (Expected Shortfall al 97.5%). "
        "Se define como una métrica de riesgo matemáticamente coherente (coherent risk measure) y de referencia bajo los más estrictos estándares internacionales de gestión financiera (como la Fundamental Review of the Trading Book - FRTB de Basilea III), "
        "capturando con rigor la verdadera magnitud de las pérdidas extremas en la cola de la distribución sin sufrir el efecto de dilución de eventos de baja frecuencia. Al agregar los valores, ilustramos el peor caso estructural absoluto "
        "donde las mayores vulnerabilidades convergen simultáneamente, proporcionando el requerimiento de capital de resiliencia necesario para proteger el Valor de la Empresa (Enterprise Value).",
        space_after=4
    )

    p_m3 = add_markdown_bullet_local(
        f"Rango Probabilístico de Pérdidas: Muestra la volatilidad de la exposición del riesgo, ilustrando desde un año virtual benigno (Mín) hasta "
        f"un año catastrófico (Máx) provocado por la ineficiencia acumulada de múltiples fallos y sanciones regulatorias de {reg_name} concurrentes.",
        space_after=12
    )

    p_convergence = (
        "*(Nota de Estabilidad y Exposición de Riesgo Bruto: El volumen de 10.000 iteraciones simuladas garantiza la plena convergencia "
        "y estabilidad matemática de los indicadores económicos bajo el Teorema del Límite Central, proporcionando un estimador de exposición "
        "financiero de alta precisión y máxima fidelidad estadística. Asimismo, todos los valores monetarios aquí expuestos (ALE y CVaR) representan "
        "el Riesgo Bruto Latente (Gross Exposure) antes de la aplicación de posibles mitigaciones de transferencia financiera (como franquicias o topes de pólizas de ciberseguro). "
        "Por consiguiente, deben interpretarse como indicadores de magnitud probabilística para la priorización ejecutiva de inversiones tecnológicas (Business Case), "
        "no como límites absolutos o provisiones directas de pasivos en el balance contable de la organización).*"
    )
    add_body_paragraph(doc, p_convergence, text_color_rgb=text_color_rgb)
    
        # Disable the `autofit` property to enforce a fixed table width of 6.5 inches.

    #
    # Assemble and render Appendix B: Information Sources Custody Ledger
    #
    add_appendix_heading(doc, vocab["appendix_c_title"], primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, vocab["appendix_c_intro"], text_color_rgb=text_color_rgb)

    source_table = doc.add_table(rows=1, cols=3)
    source_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(source_table)

    for i, h_txt in enumerate(vocab["appendix_c_headers"]):
        set_cell_text_custom(
            source_table.rows[0].cells[i],
            h_txt,
            bold=True,
            font_size=10,
            color_rgb=RGBColor(255, 255, 255),
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(source_table.rows[0].cells[i], p_color_hex)

    # Set initial column widths for header cells in centimeters
    source_table.rows[0].cells[0].width = Cm(1.5)
    source_table.rows[0].cells[1].width = Cm(4.5)
    source_table.rows[0].cells[2].width = Cm(10.5)

    # Data Sanitization: Prevent generation of invalid source file paths in the bibliography, per requirement 4.
    src_data = []
    b_data = ctx.get("b_data") or {}
    if not b_data and payload_path and payload_path.exists():
        try:
            with open(payload_path, "r", encoding="utf-8-sig") as f:
                b_data = json.load(f)
        except Exception:
            b_data = {}

    source_docs = b_data.get("source_documents") if payload_path and payload_path.exists() else None

    if source_docs:
        # If source file paths are provided in the payload, use them directly, overriding any dynamic generation logic.
        for doc_item in source_docs:
            src_data.append(
                (
                    doc_item.get("code", "[Doc]"),
                    doc_item.get("name", "Documento"),
                    doc_item.get("desc", "Documento bajo custodia de auditoría."),
                )
            )
    else:
        # Dynamically generate a context-aware bibliography based on the specified technology stack to avoid invalid source file references.
        client_name_slug = client_name.lower().replace(" ", "_")
        src_data = [
            (
                "[Cuestionario de Autoevaluación]",
                f"preguntas_{client_name_slug}.txt",
                f"Cuestionario estructurado de autoevaluación técnica de la torre de {tower_name}, recopilando "
                f"las respuestas oficiales, notas y telemetrías declaradas de buena fe por el equipo de ingeniería de {client_name}.",
            ),
            (
                "[Dossier de Contexto]",
                f"contexto_{client_name_slug}.docx",
                f"Dossier estratégico de contexto de arquitectura de {client_name} que define la volumetría del "
                f"patrimonio, distribución de centros de datos, dependencias y criticidad operativa general.",
            ),
            (
                "[Capa de Inteligencia de la Plataforma]",
                "client_intelligence.json",
                f"Módulo de ingesta y análisis semántico asistido por IA de la plataforma que recopila de forma automatizada "
                f"las regulaciones de cumplimiento (como NIS2, RGPD o DORA), requerimientos corporativos y baselines del sector (ITIC) "
                f"para calibrar y enriquecer los hallazgos técnicos con métricas cuantitativas de riesgo de negocio.",
            ),
            (
                "[ITIC-DOWNTIME]",
                "ITIC Global Server Hardware Downtime Report",
                "Estudio de referencia mundial y métrica estadística industrial que barema el coste promedio por hora de "
                "indisponibilidad de infraestructura core en grandes corporaciones y servicios críticos, utilizado como baseline de calibración de pérdidas primarias.",
            ),
            (
                "[CISA-KEV]",
                "CISA Known Exploited Vulnerabilities Catalog",
                "Catálogo internacional de vulnerabilidades explotadas activamente por agentes de amenaza, mantenido por la Cybersecurity "
                "and Infrastructure Security Agency (CISA) y utilizado como baseline para calibrar la Frecuencia de Eventos de Amenaza (TEF).",
            ),
            (
                "[DIRECTIVA-NIS2]",
                "Directiva (UE) 2022/2555 (NIS2)",
                "Directiva del Parlamento Europeo y del Consejo relativa a medidas destinadas a garantizar un elevado nivel común de ciberseguridad "
                "en toda la Unión, utilizada para calibrar el límite máximo legal de sanciones administrativas por negligencia (pérdidas secundarias).",
            ),
            (
                "[ISO-27001]",
                "Norma Internacional ISO/IEC 27001",
                "Estándar internacional de sistemas de gestión de seguridad de la información (SGSI), utilizado como marco de referencia "
                "universal para evaluar los controles de seguridad técnica, gobernanza y resiliencia operacional.",
            ),
            (
                "[DAMA-DMBOK]",
                "DAMA Data Management Body of Knowledge (DAMA-DMBOK v2)",
                "Marco metodológico estándar internacional para la evaluación de madurez del gobierno y gestión de datos corporativos, "
                "utilizado para modelar y auditar la consistencia del pilar de gobierno de datos de la plataforma.",
            ),
            (
                "[GOOGLE-DORA]",
                "Google DevOps Research and Assessment (DORA) Framework",
                "Estándar industrial internacional utilizado para evaluar la madurez de la automatización, entrega continua, "
                "y fiabilidad operacional (SRE) en ecosistemas modernos de desarrollo e infraestructura híbrida.",
            )
        ]

    for s_idx, row_vals in enumerate(src_data):
        row = source_table.add_row()
        set_cell_text_custom(
            row.cells[0],
            row_vals[0],
            bold=True,
            font_size=10,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_text_custom(
            row.cells[1], row_vals[1], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER
        )
        set_cell_text_custom(row.cells[2], row_vals[2], font_size=10)

        row.cells[0].width = Cm(1.5)
        row.cells[1].width = Cm(4.5)
        row.cells[2].width = Cm(10.5)

        if s_idx % 2 == 1:
            shade_cell(row.cells[0], alt_row_hex)
            shade_cell(row.cells[1], alt_row_hex)
            shade_cell(row.cells[2], alt_row_hex)

    add_spacer(doc, 12)

    #
    # Assemble and render Appendix C: Terms and Abbreviations Glossary
    #
    add_appendix_heading(doc, vocab["appendix_a_title"], primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, vocab["appendix_a_intro"], text_color_rgb=text_color_rgb)

    import re

    from assessment_engine.infrastructure.config_loader import (
        load_abbreviations_glossary,
    )

    try:
        full_glossary = load_abbreviations_glossary()

        # Merge case-specific client abbreviations if they exist in the case directory
        client_glossary_path = tower_dir_obj / "client_abbreviations_glossary.json"
        if client_glossary_path.exists():
            try:
                with open(client_glossary_path, "r", encoding="utf-8-sig") as cgf:
                    client_glossary = json.load(cgf)
                    for lang, terms in client_glossary.items():
                        if lang in full_glossary:
                            full_glossary[lang].update(terms)
                        else:
                            full_glossary[lang] = terms
            except json.JSONDecodeError as ex:
                logger.info(
                    f"⚠️  [Glosario] Error de sintaxis JSON en {client_glossary_path}: {ex}"
                )
            except Exception as ex:
                logger.info(f"⚠️  [Glosario] No se pudo leer {client_glossary_path}: {ex}")

        glossary = full_glossary.get(doc_lang, full_glossary.get("es", {}))

        # Gather all text accumulated in paragraphs and tables so far (now fully includes Appendix A and B!)
        all_text_elements = []
        for p in doc.paragraphs:
            if p.text:
                all_text_elements.append(p.text)
        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    if cell.text:
                        all_text_elements.append(cell.text)
        text_corpus = " ".join(all_text_elements)

        # Filter glossary keys that are actually present in the text corpus
        used_glossary = {}
        for term, desc in glossary.items():
            escaped_term = re.escape(term)
            pattern = rf"(?<![a-zA-Z0-9]){escaped_term}(?![a-zA-Z0-9])"
            if re.search(pattern, text_corpus):
                used_glossary[term] = desc

        # Quality Gate: First-Use Rule Verification
        for term, desc in used_glossary.items():
            # standard Bilingual Check: Extract both English form (before parenthesis) and Spanish translation (inside parenthesis)
            # to prevent false positive warnings when compiling documents in different languages
            parts = []
            if "(" in desc:
                main_part = desc.split("(")[0].strip()
                parts.append(main_part)
                sub_part = desc.split("(")[1].split(")")[0].strip()
                parts.append(sub_part)
            else:
                parts.append(desc)

            # Verification passes if either the English or the Spanish full form is located in the text
            if not any(p.lower() in text_corpus.lower() for p in parts if len(p) > 2):
                logger.info(
                    f"⚠️  [Glosario] Calidad: La sigla '{term}' se utiliza pero su definición extendida ('{parts[0]}') no aparece en el informe. Se recomienda expandirla en su primer uso."
                )

        if used_glossary:
            gloss_table = doc.add_table(rows=1, cols=2)
            gloss_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            finalize_table(gloss_table)

            for i, h_txt in enumerate(vocab["appendix_a_headers"]):
                set_cell_text_custom(
                    gloss_table.rows[0].cells[i],
                    h_txt,
                    bold=True,
                    font_size=10,
                    color_rgb=RGBColor(255, 255, 255),
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )
                shade_cell(gloss_table.rows[0].cells[i], p_color_hex)

            #
            gloss_table.rows[0].cells[0].width = Inches(1.5)
            gloss_table.rows[0].cells[1].width = Inches(5.0)  #

            for g_idx, (term, desc) in enumerate(sorted(used_glossary.items())):
                row = gloss_table.add_row()
                set_cell_text_custom(row.cells[0], term, bold=True, font_size=10)
                set_cell_text_custom(row.cells[1], desc, font_size=10)

                #
                row.cells[0].width = Inches(1.5)
                row.cells[1].width = Inches(5.0)

                if g_idx % 2 == 1:
                    shade_cell(row.cells[0], alt_row_hex)
                    shade_cell(row.cells[1], alt_row_hex)
    except Exception as ex:
        logger.info(f"⚠️  [Glosario] Error inesperado en el apéndice de abreviaturas: {ex}")

    add_spacer(doc, 12)

    #
    # Assemble and render Appendix D: Liability Limitation Clause
    # Always prioritize the central declarative brand disclaimer.
    #
    add_appendix_heading(doc, vocab["appendix_b_title"], primary_color_rgb=p_color_rgb)
    from assessment_engine.infrastructure.config_loader import get_localized_disclaimer
    disclaimer_raw = get_localized_disclaimer(doc_lang)
    if disclaimer_raw:
        for p_text in disclaimer_raw.split("\n\n"):
            if p_text.strip():
                formatted_p = (
                    p_text.strip().format(company_name=company_name)
                    if "{company_name}" in p_text
                    else p_text.strip()
                )
                add_body_paragraph(
                    doc,
                    formatted_p,
                    text_color_rgb=text_color_rgb,
                )
    else:
        for k in ["disclaimer_text_1", "disclaimer_text_2", "disclaimer_text_3", "disclaimer_text_4", "disclaimer_text_5"]:
            if vocab.get(k):
                add_body_paragraph(
                    doc, vocab.get(k, ""), text_color_rgb=text_color_rgb
                )

    add_spacer(doc, 20)


