import csv
import json
import sys
from pathlib import Path


def sanitize_semantic_prose(text: str, doc_lang: str = "es") -> str:
    """Rephrases technical prose to remove speculative language and align it with formal compliance terminology.

    This function applies two primary sets of transformations:
    1.  It replaces speculative or conditional phrases (e.g., "posiblemente",
        "potencialmente") with more declarative, assertive equivalents based on a
        pre-defined mapping.
    2.  It inspects the text for compliance-related keywords (e.g.,
        "automatización", "runbooks", "compliance"). If found, it may replace the
        entire input string with a standardized statement that frames the
        subject within target-state regulatory frameworks like ENS and NIS2.
        This transformation is language-dependent. If keywords are present but
        no specific replacement rule matches, a suffix is appended to indicate
        planned automation.

    The function is designed to standardize descriptions in formal reports,
    ensuring consistent, assertive, and compliance-oriented language.

    Args:
        text: The source prose to sanitize.
        doc_lang: The language identifier (e.g., "es", "en") used to select the
            appropriate set of transformation rules. Defaults to "es".

    Returns:
        The sanitized string, which may be a significant modification or a
        complete replacement of the original input.
    """
    if not text:
        return text

    t = str(text).strip()
    lang = str(doc_lang).lower()

    # RULE 1: Replace speculative or conditional language with declarative phrasing.
    speculative_patterns = {
        "posiblemente con componentes Mainframe": "integrando servidores corporativos y entornos de misión crítica de rango medio (Unix/AIX, AS/400 y plataformas legacy)",
        "posiblemente con componentes mainframe": "integrando servidores corporativos y entornos de misión crítica de rango medio (Unix/AIX, AS/400 y plataformas legacy)",
        "posiblemente con": "integrando",
        "posiblemente": "de manera probada",
        "potencialmente": "de forma estructurada",
        "tal vez": "con total seguridad",
    }
    for old, new in speculative_patterns.items():
        if old in t:
            t = t.replace(old, new)

    # RULE 2: Re-aligns terminology describing current strengths to match future-state compliance frameworks (e.g., NIS2/ENS).
    compliance_keywords = [
        "demostrar",
        "industrialización",
        "automatización",
        "automatizado",
        "continuo y auditable",
        "continuous and auditable",
    ]
    has_target_vocab = any(kw in t.lower() for kw in compliance_keywords)

    if has_target_vocab:
        if lang == "es":
            if "cumplimiento" in t.lower() or "normativo" in t.lower():
                t = "Sólida postura de partida y alineamiento inicial para facilitar la conformidad continua con marcos normativos (ENS, NIS2) en el estado objetivo."
            elif "runbooks" in t.lower():
                t = "Base técnica establecida para la futura codificación y automatización de procedimientos operativos (Runbooks-as-Code) de forma estructurada."
            else:
                t = (
                    t
                    + " (planeado para consolidarse de forma automatizada en el estado objetivo)."
                )
        else:
            if "compliance" in t.lower() or "regulatory" in t.lower():
                t = "Solid baseline posture and initial alignment to facilitate continuous compliance with regulatory frameworks (ENS, NIS2) in the target state."
            else:
                t = t + " (planned to be fully automated in the target state)."

    return t


def generate_modules(payload_path: str):
    """Generates a structured set of AS-IS assessment report modules from a JSON payload.

    This function processes a primary JSON payload, enriching it with data from
    supplementary files such as approved annexes, client intelligence reports,
    tower definitions, and localization vocabularies. The aggregated data is then
    serialized into a series of Markdown (.md) and CSV (.csv) files that
    constitute a complete technical AS-IS report.

    All output files are written to an `asis_modules` subdirectory, which is
    created within the same directory as the input `payload_path`.

    Args:
        payload_path (str): The file system path to the main JSON payload file.

    Returns:
        None. The function's primary effect is writing files to the file system.

    Raises:
        FileNotFoundError: If the file specified by `payload_path` does not exist.
        json.JSONDecodeError: If the main payload file contains malformed JSON.
        OSError: If an error occurs during directory creation or file I/O, such as
            insufficient write permissions.
    """
    payload_path_obj = Path(payload_path)
    tower_dir = payload_path_obj.parent
    modules_dir = tower_dir / "asis_modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Iniciando Extracción de Módulos Docs-as-Code en: {modules_dir}")

    # Loads technical payloads from the blueprint configuration, which serves as the primary data source.
    with open(payload_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    tower_meta = data.get("document_meta", {})
    doc_lang = tower_meta.get("language", "es").lower()

    #
    locales_path = Path("engine_config/locales.json")
    locales_data = {}
    if locales_path.exists():
        with open(locales_path, "r", encoding="utf-8-sig") as lf:
            try:
                locales_data = json.load(lf)
            except Exception:
                pass
    vocab = locales_data.get(doc_lang, locales_data.get("es", {}))

    tower_name = tower_meta.get("tower_name", "Desconocida")
    tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
    client_name = tower_meta.get("client_name", "Cliente")
    pillars = data.get("pillars_analysis", [])
    snap = data.get("executive_snapshot", {})
    cca = data.get("cross_capabilities_analysis", {})

    # Loads the `approved_annex` data if present, which contains curated and validated findings.
    annex_path = tower_dir / f"approved_annex_{tower_id.lower()}.template_payload.json"
    annex_data = {}
    if annex_path.exists():
        with open(annex_path, "r", encoding="utf-8-sig") as af:
            try:
                annex_data = json.load(af)
            except Exception:
                pass

    exec_sum = annex_data.get("executive_summary", {})
    score_profile = annex_data.get("pillar_score_profile", {})

    # Loads `client_intelligence` data from OSINT sources if the corresponding dataset is available.
    client_intel_path = payload_path_obj.parents[1] / "client_intelligence.json"
    intel = {}
    if client_intel_path.exists():
        with open(client_intel_path, "r", encoding="utf-8-sig") as cif:
            try:
                intel = json.load(cif)
            except Exception:
                pass
    business_context = intel.get("business_context", {})
    ceo_agenda_raw = business_context.get("ceo_agenda", {}).get("summary", "")

    # Dynamically loads the tower definition and integrates KPIs into a narrative paragraph, avoiding bulleted lists to maintain prose flow.
    pillars_list_md = ""
    tower_def_path = (
        Path("engine_config/towers")
        / tower_id
        / f"tower_definition_{tower_id.lower()}.json"
    )
    if not tower_def_path.exists():
        # Provides a fallback for case-insensitive key matching to handle variations in source data.
        tower_def_path = (
            Path("engine_config/towers")
            / tower_id
            / f"tower_definition_{tower_id}.json"
        )

    if tower_def_path.exists():
        with open(tower_def_path, "r", encoding="utf-8-sig") as tdf:
            try:
                t_def = json.load(tdf)
                for p in t_def.get("pillars", []):
                    p_name = p.get("pillar_name", "Pilar")
                    p_weight = p.get("weight_pct", "0")

                    # Extracts Key Performance Indicator (KPI) names for integration into narrative text.
                    kpi_names = []
                    for kpi in p.get("kpis", []):
                        k_name = kpi.get("kpi_name", "KPI").strip()
                        # Normalizes text to lowercase while preserving the case of known acronyms to maintain technical accuracy.
                        if k_name and not k_name.isupper() and len(k_name) > 4:
                            k_name = k_name[0].lower() + k_name[1:]
                        kpi_names.append(k_name)

                    # Formats the KPI list into a grammatically standard series (e.g., 'a, b, and c') for prose integration.
                    if len(kpi_names) > 1:
                        kpi_str = ", ".join(kpi_names[:-1]) + " y " + kpi_names[-1]
                    elif kpi_names:
                        kpi_str = kpi_names[0]
                    else:
                        kpi_str = "las capacidades operativas del pilar"

                    pillars_list_md += f"* **{p_name} (Peso: {p_weight}%)**: Evalúa de manera integral la madurez operativa y los baselines técnicos de la infraestructura, analizando críticamente factores clave como {kpi_str}.\n"
            except Exception as e:
                print(f"⚠️ Error parsing tower definition: {e}")

    if not pillars_list_md:
        # Returns a default empty string on a JSON parsing exception to prevent downstream processing failures.
        for p in pillars:
            p_name = p.get("pilar_name", "Pilar")
            pillars_list_md += f"* **{p_name}**: Evaluación técnica y análisis de brechas operativas en la torre.\n"

    #
    # SECTION MAPPING: Appendix B (Objective, Scope, Methodology) maps to `01_introduccion.md`.
    # The following section is designated for Appendix B to conform to the standard report structure.
    #
    intro_content = f"""# Objetivo, Alcance y Metodología del Assessment

## Objetivo y Alcance
Este documento técnico anexo detalla de manera exhaustiva el diagnóstico de situación actual (AS-IS) de la torre **{tower_name}** para **{client_name}**. El objetivo principal es identificar y registrar de manera estructurada las brechas operativas, riesgos de continuidad y obsolescencias tecnológicas dentro del perímetro de evaluación.

El alcance técnico incluye el inventario de infraestructura y la topología operativa, restringida estrictamente a los sistemas activos de producción del cliente, evaluando el nivel de madurez operativa basándose en evidencias de auditoría recopiladas empíricamente.

## Proceso de Ejecución del Assessment
La información base para este análisis ha sido recopilada de manera sistemática a partir de las sesiones de contexto de arquitectura mantenidas con los responsables operativos de {client_name}, así como de las respuestas detalladas proporcionadas por los equipos técnicos en los cuestionarios de autoevaluación de la torre.

## Metodología de Valoración de Madurez
La madurez se califica en una escala analítica del 1,00 al 5,00, donde cada nivel determina un estadio de control:
* **Nivel 1 - Inicial (1.0-1.8):** Prácticas ad-hoc, inestables o dependientes del esfuerzo heroico de personas clave.
* **Nivel 2 - Básico (1.8-2.6):** Prácticas funcionales de manera parcial o irregular, sin consistencia organizativa.
* **Nivel 3 - Estandarizado (2.6-3.4):** Procesos formalizados e implantados de manera coherente en toda la organización.
* **Nivel 4 - Optimizado (3.4-4.2):** Capacidades industrializadas, gobernadas predictivamente y sustentadas en métricas.
* **Nivel 5 - Avanzado (4.2-5.0):** Procesos dinámicos impulsados por automatización inteligente y mejora continua.

### Capacidades Evaluadas y Cálculo del Score
El nivel de madurez técnica y el score global de la torre se consolidan mediante el promedio ponderado de las calificaciones obtenidas en las siguientes dimensiones y KPIs evaluados:

{pillars_list_md}

## Metodología Cuantitativa de Riesgos (FAIR)
Este diagnóstico técnico aplica el estándar internacional **O-FAIR (Factor Analysis of Information Risk)** del *The Open Group* para modelar, cuantificar y priorizar la exposición al riesgo de infraestructura en términos financieros reales.

Para evitar la **\"Falacia de los Promedios\"** (donde las estimaciones fijas e individuales distorsionan el riesgo real), el motor de políticas de la plataforma aplica un algoritmo de simulación actuarial de **Monte Carlo de 10.000 iteraciones** para cada hallazgo detectado, basado en los siguientes principios científicos:

1. **Estimaciones de Tres Puntos (Incertidumbre):** Cada nivel cualitativo de la auditoría (escala 1 a 5) se traduce a un rango dinámico definido por tres parámetros: **Mínimo, Más Probable y Máximo**.
   - Frecuencia de Amenaza (TEF): Mapea la probabilidad anualizada de exposición (de 0,1 a 24 eventos de amenaza al año).
   - Vulnerabilidad (Vuln): Mapea la probabilidad de éxito de la amenaza según el nivel de controles (de 5% a 100%).
   - Magnitud de Pérdida (LM): Mapea el impacto financiero directo e indirecto (laboral, cumplimiento, remediación) desde 100 € hasta 500.000 € por incidente.
2. **Modelado con Curvas de Probabilidad Beta-PERT:** Para cada una de las 10.000 simulaciones de la simulación, el motor toma muestras aleatorias de las curvas de densidad de probabilidad continua **Beta-PERT** correspondientes a cada parámetro. Esto permite capturar el comportamiento realista de los incidentes tecnológicos (donde existe una \"larga cola\" de costes de remediación elevados hacia la derecha).
3. **Cálculo del Exposición Anualizada de Pérdida (ALE):** En cada iteración se realiza un sorteo de Bernoulli basado en la vulnerabilidad muestreada. Si el evento de pérdida se materializa, el coste anualizado para esa simulación es el producto de la frecuencia por la pérdida promedio:
   **ALE = Frecuencia de Amenaza x Vulnerabilidad x Magnitud de Pérdida**
4. **Métricas de Convergencia Estadística (ALE y P90):** El valor final de **ALE Proyectado** reflejado en las tablas detalladas del informe representa la **media estadística de pérdida resultante de esas 10.000 iteraciones independientes**. Adicionalmente, el sistema calcula la métrica **P90 (Percentil 90)** para alertar a la dirección sobre la exposición financiera máxima esperada en el peor escenario razonable de negocio.
"""
    with open(modules_dir / "01_introduccion.md", "w", encoding="utf-8") as f_out:
        f_out.write(intro_content.strip())

    #
    # SECTION MAPPING: Module 2 (Executive Summary) maps to `02_resumen_ejecutivo.md`.
    # Revises section titles to align with formal reporting terminology.
    #
    re_content = []
    re_content.append("# Resumen Ejecutivo y Contexto de Negocio\n")

    re_content.append("## Diagnóstico de Situación")
    if exec_sum:
        raw_headline = exec_sum.get("headline", "Diagnóstico General")
        clean_headline = (
            raw_headline.replace(" (Bottom Line)", "")
            .replace("(Bottom Line)", "")
            .strip()
        )
        re_content.append(f"**{clean_headline}**\n")

        # Enforces a Mutually Exclusive, Collectively Exhaustive (MECE) structure by extracting only the primary technical diagnosis paragraph.
        # Excludes forward-looking and strategic recommendations to maintain focus on current-state analysis.
        body_text = exec_sum.get("summary_body", "")
        if "\n\n" in body_text:
            body_text = body_text.split("\n\n")[0].strip()
        re_content.append(body_text)
    elif snap:
        re_content.append(snap.get("bottom_line", ""))

    if ceo_agenda_raw:
        re_content.append("\n## Impacto y Relevancia Estratégica para el Negocio")
        re_content.append(ceo_agenda_raw)

    if exec_sum and exec_sum.get("key_business_impacts"):
        re_content.append("\n## Principales Impactos de Negocio")
        for item in exec_sum.get("key_business_impacts", []):
            re_content.append(f"* {item}")
    elif snap and snap.get("structural_risks"):
        re_content.append("\n## Riesgos de Negocio más Materiales")
        for r in snap.get("structural_risks", []):
            re_content.append(f"* {r}")

    with open(modules_dir / "02_resumen_ejecutivo.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(re_content).strip())

    #
    # SECTION MAPPING: Module 3 (Platform Description) maps to `03_descripcion_plataforma.md`.
    #
    desc_raw = (
        pillars[0].get(
            "asis_architecture_description",
            "Descripción técnica de plataforma no disponible.",
        )
        if pillars
        else ""
    )
    desc_clean = sanitize_semantic_prose(desc_raw, doc_lang)
    desc_content = f"""# Descripción de la Plataforma de Infraestructura Actual

A continuación, se define de manera consolidada y unificada el inventario técnico, arquitectura y estado operativo general del entorno. Esta descripción unifica el contexto tecnológico general para evitar repeticiones innecesarias entre dominios:

{desc_clean}
"""
    with open(
        modules_dir / "03_descripcion_plataforma.md", "w", encoding="utf-8"
    ) as f_out:
        f_out.write(desc_content.strip())

    #
    # SECTION MAPPING: Module 4 (Maturity Matrix) maps to `04_matriz_madurez.csv`.
    #
    csv_mat_path = modules_dir / "04_matriz_madurez.csv"
    annex_pillars_map = {}
    if score_profile:
        for ap in score_profile.get("pillars", []):
            annex_pillars_map[ap.get("pillar_label")] = ap.get("executive_reading")

    with open(csv_mat_path, "w", newline="", encoding="utf-8") as cf_out:
        writer = csv.writer(cf_out, delimiter=";")
        writer.writerow(
            [
                "Pilar / Capacidad Evaluada",
                "Score AS-IS",
                "Análisis de Brecha y Justificación de Nota",
            ]
        )

        for p in pillars:
            p_name = p.get("pilar_name", "Pilar")
            justification = annex_pillars_map.get(p_name)
            if not justification:
                desc = p.get(
                    "asis_description",
                    p.get("asis_architecture_description", "No descripto."),
                )
                justification = (
                    desc.split(".")[0] + "." if desc else "Evaluado con éxito."
                )

            writer.writerow([p_name, f"{p.get('score', 0.0):.2f}", justification])

    #
    # SECTION MAPPING: Module 5 (Cross-Cutting Platform Analysis) maps to `05_transversal.md`.
    #
    # Consolidates technical debt, legacy paradigms, and cross-cutting weaknesses from the blueprint into a single dataset.
    trans_content = []
    trans_content.append("# Análisis Transversal de Capacidades\n")

    if cca:
        trans_content.append("## El Paradigma de Transformación")
        trans_content.append(cca.get("transformation_paradigm", "No definido.") + "\n")

        trans_content.append("## Deuda Técnica Crítica")
        trans_content.append(cca.get("critical_technical_debt", "No definido.") + "\n")

        trans_content.append("## Patrones Comunes de Deficiencia")
        def_patterns = cca.get("common_deficiency_patterns", [])
        if isinstance(def_patterns, str):
            trans_content.append(def_patterns + "\n")
        else:
            for pat in def_patterns:
                trans_content.append(f"* {pat}")
            trans_content.append("")

    with open(modules_dir / "05_transversal.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(trans_content).strip())

    #
    # SECTION MAPPING: Module 6 (Risk Register, FAIR) maps to `06_matriz_riesgos_fair.csv`.
    #
    # Exports data in the three-column format required by the blueprint specification.
    csv_risks_path = modules_dir / "06_matriz_riesgos_fair.csv"
    with open(csv_risks_path, "w", newline="", encoding="utf-8") as cf_out:
        writer = csv.writer(cf_out, delimiter=";")
        writer.writerow(
            [
                "Capacidad Técnica Evaluada",
                "Diagnóstico Técnico y Evidencias de Auditoría (Audit RAG)",
                "Riesgo de Negocio e Impacto Operativo",
                "TEF",
                "LM",
                "ALE",
            ]
        )

        for pilar in pillars:
            p_name = pilar.get("pilar_name", "General")
            for hc in pilar.get("health_check_asis", []):
                #
                finding = hc.get("finding", hc.get("risk_observed", "No descripto."))
                evidence = hc.get("literal_evidence", "No se aportó evidencia literal.")
                biz_risk = hc.get("business_risk", hc.get("impact", "No descripto."))

                #
                finding_full = (
                    f'{finding}\n\nEvidencia Forense Literal (Audit RAG):\n"{evidence}"'
                )

                tef = hc.get("threat_event_frequency", 0.0)
                lm = hc.get("loss_magnitude", 0.0)
                ale = hc.get("fair_ale_score", 0.0)

                writer.writerow(
                    [
                        f"{p_name} - {hc.get('target_state', hc.get('capability', 'Capacidad'))}",
                        finding_full,
                        biz_risk,
                        f"{tef:.1f}",
                        f"{lm:.1f}",
                        f"{ale:.0f}",
                    ]
                )

    #
    # SECTION MAPPING: Module 7 (Conclusions and Gaps) maps to `07_conclusiones.md`.
    #
    conc_content = []
    conc_content.append(
        f"# {vocab.get('conclusions_title', 'Conclusiones, Brechas y Coste de Inacción')}\n"
    )

    # Inserts the AS-IS summary into the conclusions section to provide final context.
    conc_content.append(
        f"## {vocab.get('asis_consolidated_title', 'Resumen de Situación (AS-IS Consolidado)')}"
    )
    asis_resumido_tmpl = vocab.get(
        "asis_consolidated_body",
        "El estado actual de la infraestructura de {tower_name}, subproducto de una evolución orgánica para dar servicio a una operación crítica, ha alcanzado un punto de inflexión. La plataforma se caracteriza por una fragmentación estructural, herramientas y operaciones en silos discretos para los entornos on-premise y cloud, y una dependencia sistémica de flujos de aprobación y procesos manuales para la provisión y el ciclo de vida.",
    )
    asis_resumido = asis_resumido_tmpl.format(tower_name=tower_name)
    conc_content.append(asis_resumido + "\n")

    conc_content.append(
        f"## {vocab.get('quick_diagnosis_title', 'Fortalezas y Brechas Clave (Diagnóstico Rápido)')}"
    )
    conc_content.append(
        vocab.get(
            "quick_diagnosis_intro",
            "A continuación se presenta el balance comparativo de las fortalezas encontradas frente a las deudas operativas más críticas:",
        )
    )

    # Structures strengths and gaps as discrete lists for rendering into a two-column table.
    strengths_list = []
    msg_strength = exec_sum.get("message_strength", "")
    if msg_strength:
        strengths_list.append(msg_strength)
    benefits = snap.get("operational_benefits", [])
    if isinstance(benefits, str):
        strengths_list.append(benefits)
    else:
        strengths_list.extend(benefits)

    gaps_list = []
    msg_gap = exec_sum.get("message_gap", "")
    if msg_gap:
        gaps_list.append(msg_gap)
    weaknesses = snap.get("structural_risks", [])
    if isinstance(weaknesses, str):
        gaps_list.append(weaknesses)
    else:
        gaps_list.extend(weaknesses)

    # Serializes data to a specific format required by the downstream document compilation service.
    conc_content.append("--- TABLA COMPARATIVA FORTALEZAS VS BRECHAS ---")
    conc_content.append("FORTALEZAS_CLAVE:")
    for s in strengths_list:
        conc_content.append(f"* {sanitize_semantic_prose(s, doc_lang)}")
    conc_content.append("BRECHAS_CLAVE:")
    for g in gaps_list:
        conc_content.append(f"* {sanitize_semantic_prose(g, doc_lang)}")
    conc_content.append("--- FIN TABLA --- \n")

    # Implements regulatory terminology harmonization as specified by Requirement 2.
    doc_lang = tower_meta.get("language", "es").lower()
    reg_frameworks = tower_meta.get("regulatory_frameworks")
    if not reg_frameworks:
        reg_frameworks = (
            "ENS y NIS2" if doc_lang == "es" else "applicable regulatory frameworks"
        )

    conc_content.append(
        f"## {vocab.get('operational_implications_title', 'Implicaciones Operativas Clave')}"
    )

    # Loads localized implication text from `locales.json` to generate context-specific output.
    bottlenecks_txt = vocab.get(
        "bottlenecks_bullet",
        "**Cuellos de botella sistémicos:** El modelo manual de aprovisionamiento de infraestructura limita la velocidad de entrega de las iniciativas estratégicas del negocio.",
    )
    delayed_txt = vocab.get(
        "delayed_faults_bullet",
        "**Detección tardía de fallas:** La falta de observabilidad correlacionada eleva el Tiempo Medio de Resolución (MTTR) de incidentes críticos.",
    )
    drift_tmpl = vocab.get(
        "config_drift_bullet",
        "**Riesgo de configuration drift:** El mantenimiento manual de las configuraciones dificulta demostrar el cumplimiento normativo en tiempo real de {reg_frameworks}.",
    )

    conc_content.append(f"* {bottlenecks_txt}")
    conc_content.append(f"* {delayed_txt}")
    conc_content.append(f"* {drift_tmpl.format(reg_frameworks=reg_frameworks)}\n")

    conc_content.append(
        f"## {vocab.get('coi_title', 'Coste de Inacción (Do Nothing) y Siguientes Pasos')}"
    )
    msg_bottle = exec_sum.get("message_bottleneck", "")
    if msg_bottle:
        conc_content.append(msg_bottle + "\n")

    coi = snap.get("cost_of_inaction", [])
    if isinstance(coi, str):
        conc_content.append(coi + "\n")
    else:
        for item in coi:
            conc_content.append(f"* {item}")

    with open(modules_dir / "07_conclusiones.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(conc_content).strip())

    print(f"🎉 ¡Módulos Docs-as-Code extraídos con éxito en: {modules_dir}!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python generate_asis_markdown_modules.py <blueprint_payload.json>")
        sys.exit(1)
    generate_modules(sys.argv[1])
