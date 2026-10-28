from __future__ import annotations

from typing import Any

from assessment_engine.domain.schemas.ast import (
    CellNode,
    ParagraphNode,
    TableNode,
    TableRowNode,
)


def build_criticality_bullet(business_criticality: float) -> ParagraphNode:
    """Builds the MCDA business criticality bullet node."""
    if business_criticality >= 80.0:
        return ParagraphNode(
            text=f"* **Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Extrema]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. En este caso, este valor extremo confirma que los procesos operativos core de la organización dependen críticamente de esta plataforma, y su indisponibilidad causaría una interrupción inmediata de servicios esenciales."
        )
    elif business_criticality >= 50.0:
        return ParagraphNode(
            text=f"* **Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Alta]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. El score alto refleja una fuerte dependencia operativa, si bien existe un margen de tolerancia temporal antes de que impacte directamente en la continuidad del negocio."
        )
    return ParagraphNode(
        text=f"* **Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Media]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. El impacto medio sugiere que la torre provee servicios de soporte o back-office cuya indisponibilidad temporal es asumible mediante planes de contingencia estándar."
    )


def build_regulatory_bullet(regulatory_compliance: float) -> ParagraphNode:
    """Builds the MCDA regulatory pressure bullet node."""
    if regulatory_compliance >= 80.0:
        return ParagraphNode(
            text=f"* **Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Crítica]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo marcos normativos o directivas aplicables como NIS2, DORA o ISO 27001) que aplica sobre el perímetro de esta plataforma. Este score revela una exposición regulatoria crítica, donde las brechas de seguridad se traducen directamente en riesgo de sanciones económicas elevadas y responsabilidad legal corporativa."
        )
    elif regulatory_compliance >= 50.0:
        return ParagraphNode(
            text=f"* **Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Moderada]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo marcos normativos o directivas aplicables como NIS2, DORA o ISO 27001) que aplica sobre el perímetro de esta plataforma. Existen requerimientos de cumplimiento y políticas de seguridad corporativas estrictas, requiriendo auditorías periódicas de los controles de TI."
        )
    return ParagraphNode(
        text=f"* **Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Estándar]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo marcos normativos o directivas aplicables como NIS2, DORA o ISO 27001) que aplica sobre el perímetro de esta plataforma. Exposición regulatoria estándar basada en el cumplimiento de buenas prácticas de ingeniería sin un escrutinio normativo crítico directo."
    )


def build_feasibility_bullet(implementation_feasibility: float) -> ParagraphNode:
    """Builds the MCDA operational feasibility bullet node."""
    if implementation_feasibility >= 60.0:
        return ParagraphNode(
            text=f"* **Viabilidad Operativa (MCDA) [{implementation_feasibility:.1f}% - Favorable]:** Estima el nivel de complejidad operativa y facilidad técnica para ejecutar los proyectos del plan de acción propuesto, considerando recursos, ventanas de mantenimiento y dependencias previas. La viabilidad de transformación es favorable. Los proyectos de modernización se pueden abordar con tecnologías maduras y recursos disponibles en el mercado sin generar disrupciones críticas."
        )
    return ParagraphNode(
        text=f"* **Viabilidad Operativa (MCDA) [{implementation_feasibility:.1f}% - Compleja]:** Estima el nivel de complejidad operativa y facilidad técnica para ejecutar los proyectos del plan de acción propuesto, considerando recursos, ventanas de mantenimiento y dependencias previas. La baja calificación actual refleja que existe una alta complejidad para la transformación debido a la presencia de deudas estructurales profundas, cuellos de botella en el mantenimiento o falta de talento especializado."
    )


def build_dii_bullet(dii_pct: float) -> ParagraphNode:
    """Builds the Decision Instability Index (DII) bullet node."""
    if dii_pct < 15.0:
        return ParagraphNode(
            text=f"* **Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Alta Estabilidad]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). En este caso, el índice extremadamente bajo garantiza de forma objetiva que el diagnóstico es altamente robusto y representativo de la realidad de la plataforma, impidiendo que fluctuaciones puntuales alteren las conclusiones estratégicas."
        )
    elif dii_pct < 30.0:
        return ParagraphNode(
            text=f"* **Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Estabilidad Moderada]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). El índice registrado indica una sensibilidad moderada; el diagnóstico es sustancialmente estable, si bien ciertas puntuaciones dependen en parte de interpretaciones técnicas que requieren consolidación técnica futura."
        )
    return ParagraphNode(
        text=f"* **Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Sensibilidad Alta (Volátil)]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). El valor registrado muestra una sensibilidad alta, sugiriendo que la escasez de evidencias o variaciones de criterio podrían alterar la nota asignada, por lo que se recomienda un análisis de contraste de evidencias confirmatorio."
    )


def build_erc_bullet(erc_val_num: float) -> ParagraphNode:
    """Builds the Error Propagation Index (ERC) bullet node."""
    if erc_val_num >= 0.50:
        return ParagraphNode(
            text=f"* **Propagación de Fallos (ERC) [{erc_val_num:.3f} - Alta]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor elevado indica que un incidente crítico en este perímetro se propagaría con gran facilidad hacia otras áreas conectadas. El índice confirma una influencia estructural alta, donde una degradación de servicio desestabilizaría de manera en cadena gran parte de la plataforma corporativa."
        )
    elif erc_val_num >= 0.20:
        return ParagraphNode(
            text=f"* **Propagación de Fallos (ERC) [{erc_val_num:.3f} - Media]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor elevado indica que un incidente crítico en este perímetro se propagaría con gran facilidad hacia otras áreas conectadas. La influencia estructural registrada es media; un incidente tendría un efecto moderado o contenido, afectando solo a sistemas inmediatamente adyacentes."
        )
    return ParagraphNode(
        text=f"* **Propagación de Fallos (ERC) [{erc_val_num:.3f} - Baja/Aislada]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor de propagación bajo indica una influencia estructural baja; un fallo técnico se contendría dentro de su propio perímetro sin arrastrar a otras torres tecnológicas clave."
    )


def build_spof_bullet(spof_status: str) -> ParagraphNode:
    """Builds the Single Point of Failure (SPOF) bullet node."""
    if spof_status == "SÍ":
        return ParagraphNode(
            text=f"* **Punto Único de Fallo (SPOF) [SÍ - Crítico]:** Identifica si el dominio tecnológico actúa como un cuello de botella o eslabón débil de la infraestructura que, en caso de caída o compromiso técnico, detendría inmediatamente los flujos de servicio esenciales de la organización. La evaluación alerta de manera inequívoca que esta plataforma representa un cuello de botella o eslabón débil crítico sin redundancia suficiente, requiriendo acción de mitigación inmediata."
        )
    return ParagraphNode(
        text=f"* **Punto Único de Fallo (SPOF) [NO - Estable]:** Identifica si el dominio tecnológico actúa como un cuello de botella o eslabón débil de la infraestructura que, en caso de caída o compromiso técnico, detendría inmediatamente los flujos de servicio esenciales de la organización. La evaluación confirma que esta torre no actúa como un cuello de botella o eslabón débil único en la topología de la red operativa general."
    )


def build_heatmap_mosaic(risks_data_list: list[dict[str, Any]]) -> TableNode:
    """Builds the 5x5 FAIR Risk Heatmap mosaic TableNode."""
    matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
    for r in risks_data_list:
        r_tef = min(5, max(1, int(round(r["tef"]))))
        r_lm = min(5, max(1, int(round(r["lm"]))))
        matrix_cells[r_tef][r_lm].append(r["id"])

    heatmap_rows = []
    heatmap_headers = [r"TEF \ LM", "LM 1", "LM 2", "LM 3", "LM 4", "LM 5"]
    heatmap_rows.append(
        TableRowNode(
            cells=[
                CellNode(
                    text=h,
                    bold=True,
                    bg_color="0072BC",
                    text_color_rgb=[255, 255, 255],
                    align="CENTER",
                )
                for h in heatmap_headers
            ],
            is_header=True,
        )
    )

    for tef_val in range(5, 0, -1):
        row_cells = [
            CellNode(
                text=f"TEF {tef_val}",
                bold=True,
                bg_color="0072BC",
                text_color_rgb=[255, 255, 255],
                align="CENTER",
            )
        ]
        for lm_val in range(1, 6):
            cell_risks = matrix_cells[tef_val][lm_val]
            cell_text = ", ".join(cell_risks) if cell_risks else "-"
            severity = tef_val * lm_val
            if severity >= 15:
                bg_color = "FADBD8"
            elif severity >= 8:
                bg_color = "FCF3CD"
            else:
                bg_color = "D5F5E3"
            row_cells.append(
                CellNode(text=cell_text, bold=True, bg_color=bg_color, align="CENTER")
            )
        heatmap_rows.append(TableRowNode(cells=row_cells))

    return TableNode(rows=heatmap_rows)


TEF_SCALE_DEFINITIONS: dict[str, list[tuple[str, str]]] = {
    "es": [
        ("Muy Bajo", "< 0,1 eventos/año (menos de una vez cada 10 años)"),
        ("Bajo", "0,1 - 0,5 eventos/año (una vez cada 4 años)"),
        ("Medio", "0,5 - 2,0 eventos/año (una vez al año)"),
        ("Alto", "2,0 - 10 eventos/año (una vez al trimestre)"),
        ("Muy Alto", "> 10 eventos/año (una vez al mes)"),
    ],
    "en": [
        ("Very Low", "< 0.1 events/year (less than once every 10 years)"),
        ("Low", "0.1 - 0.5 events/year (once every 4 years)"),
        ("Medium", "0.5 - 2.0 events/year (once a year)"),
        ("High", "2.0 - 10 events/year (once a quarter)"),
        ("Very High", "> 10 events/year (once a month)"),
    ],
}


def build_tef_scale_table(vocab: dict[str, Any], meta_lang: str, alt_row_hex: str) -> TableNode:
    """Builds the Threat Event Frequency (TEF) criteria scale TableNode."""
    tef_headers = vocab.get("tef_headers") or [
        "Nivel TEF",
        "Denominación",
        "Frecuencia Anualizada Estimada",
    ]
    tef_tuples = TEF_SCALE_DEFINITIONS.get(meta_lang, TEF_SCALE_DEFINITIONS["es"])
    tef_data = [(f"TEF {i+1}", tef_tuples[i][0], tef_tuples[i][1]) for i in range(5)]
    tef_rows = [
        TableRowNode(
            cells=[
                CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                for h in tef_headers
            ],
            is_header=True,
        )
    ]
    for t_idx, r_vals in enumerate(tef_data):
        bg = alt_row_hex if t_idx % 2 == 1 else "FFFFFF"
        tef_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=r_vals[0], bold=True, bg_color=alt_row_hex, align="CENTER"),
                    CellNode(text=r_vals[1], bg_color=bg, align="CENTER"),
                    CellNode(text=r_vals[2], bg_color=bg),
                ]
            )
        )
    return TableNode(rows=tef_rows)


def build_lm_scale_table(
    vocab: dict[str, Any], meta_lang: str, currency: str, is_critical: bool, alt_row_hex: str
) -> TableNode:
    """Builds the Loss Magnitude (LM) criteria scale TableNode."""
    lm_headers = vocab.get("lm_headers") or [
        "Nivel LM",
        "Clasificación de Impacto",
        "Límite de Pérdida Financiera",
    ]
    labels_es = ["Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"]
    labels_en = ["Very Low", "Low", "Medium", "High", "Very High"]
    labels = labels_es if meta_lang == "es" else labels_en

    if is_critical:
        limits = [
            f"< 1.000 {currency}",
            f"1.000 {currency} - 10.000 {currency}",
            f"10.000 {currency} - 50.000 {currency}",
            f"50.000 {currency} - 300.000 {currency}",
            f"250.000 {currency} - 1.500.000 {currency}",
        ] if meta_lang == "es" else [
            f"< 1,000 {currency}",
            f"1,000 {currency} - 10,000 {currency}",
            f"10,000 {currency} - 50,000 {currency}",
            f"50,000 {currency} - 300,000 {currency}",
            f"250,000 {currency} - 1,500,000 {currency}",
        ]
    else:
        limits = [
            f"< 1.000 {currency}",
            f"1.000 {currency} - 5.000 {currency}",
            f"5.000 {currency} - 25.000 {currency}",
            f"25.000 {currency} - 100.000 {currency}",
            f"100.000 {currency} - 500.000 {currency}",
        ] if meta_lang == "es" else [
            f"< 1,000 {currency}",
            f"1,000 {currency} - 5,000 {currency}",
            f"5,000 {currency} - 25,000 {currency}",
            f"25,000 {currency} - 100,000 {currency}",
            f"100,000 {currency} - 500,000 {currency}",
        ]

    lm_data = [(f"LM {i+1}", labels[i], limits[i]) for i in range(5)]
    lm_rows = [
        TableRowNode(
            cells=[
                CellNode(
                    text=f"{h} ({currency})" if h_idx > 0 else h,
                    bold=True,
                    bg_color="0072BC",
                    text_color_rgb=[255, 255, 255],
                    align="CENTER",
                )
                for h_idx, h in enumerate(lm_headers)
            ],
            is_header=True,
        )
    ]
    for l_idx, r_vals in enumerate(lm_data):
        bg = alt_row_hex if l_idx % 2 == 1 else "FFFFFF"
        lm_rows.append(
            TableRowNode(
                cells=[
                    CellNode(text=r_vals[0], bold=True, bg_color=alt_row_hex, align="CENTER"),
                    CellNode(text=r_vals[1], bg_color=bg, align="CENTER"),
                    CellNode(text=r_vals[2], bg_color=bg),
                ]
            )
        )
    return TableNode(rows=lm_rows)
