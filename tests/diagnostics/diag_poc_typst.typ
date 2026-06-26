#set page(paper: "a4", margin: 2cm)
#set text(font: "Linux Libertine", size: 11pt)

#let data = json("working/redeia_v3/T2/blueprint_t2_payload.json")

#align(center)[
  #text(17pt, weight: "bold")[Anexo AS-IS: #data.document_meta.tower_name]
]

= Resumen de Madurez
Score Global: *4.5 / 5.0* (Sovereign Hybrid Edge)

= Registro de Riesgos Técnicos (FAIR)

#let risk_counter = 1

#for pilar in data.pillars_analysis [
  == Dominio: #pilar.pilar_name

  #let risks = pilar.health_check_asis.filter(r => r.keys().contains("threat_event_frequency") and r.threat_event_frequency > 0)
  
  #if risks.len() > 0 [
    #table(
      columns: (1fr, 3fr, 2fr, 2fr),
      fill: (x, y) => if y == 0 { luma(230) } else { none },
      [ *ID* ], [ *Hallazgo (Evidencia)* ], [ *Coordenadas FAIR* ], [ *ALE Estimado (€)* ],
      ..risks.map(r => (
        "R0" + str(1), // Simplified for POC
        r.finding,
        "TEF:" + str(r.threat_event_frequency) + " x LM:" + str(r.loss_magnitude),
        str(r.fair_ale_score) + " €"
      )).flatten()
    )
  ] else [
    _No hay riesgos cuantitativos reportados para este pilar._
  ]
]
