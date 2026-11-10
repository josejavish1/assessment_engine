# PROMPT MAESTRO: PERFECCIONAMIENTO 10/10 BOARD-READY POR TORRE (AS-IS)

> **Uso:** Copia y pega el bloque inferior en cada ventana de Gemini CLI sustituyendo únicamente los identificadores de la torre correspondiente:
> - `[TORRE_ID]`: `T2`, `T3`, `T4`, `T5`, `T6`, `T7`, `T8`, `T9` o `T10`
> - `[NUM_ANEXO]`: `02`, `03`, `04`, `05`, `06`, `07`, `08`, `09` o `10`

---

## TABLA DE ASIGNACIÓN DE TORRES Y ARCHIVOS

| Torre | Núm | Especialidad / Rol de Auditor | Archivo Word (.docx) |
| :--- | :--- | :--- | :--- |
| **T1** | `01` | Data Center & Physical Infrastructure | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_01_Data_Center_ASIS.docx` |
| **T2** | `02` | Cómputo Híbrido & Virtualización | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx` |
| **T3** | `03` | Redes & Conectividad Industrial (SD-WAN) | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_03_Redes_ASIS.docx` |
| **T4** | `04` | Almacenamiento & Backup Empresarial | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_04_Datos_Storage_ASIS.docx` |
| **T5** | `05` | Continuidad de Negocio & Resiliencia DRP | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_05_Resiliencia_ASIS.docx` |
| **T6** | `06` | Ciberseguridad Industrial & NIS2 / IEC 62443 | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_06_Seguridad_Identidad_ASIS.docx` |
| **T7** | `07` | Operaciones ITSM, Observabilidad & SRE | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_07_Operaciones_ITSM_ASIS.docx` |
| **T8** | `08` | FinOps, Gobernanza Cloud & Licenciamiento | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_08_FinOps_Gobernanza_ASIS.docx` |
| **T9** | `09` | Digital Workplace, Puesto de Trabajo & EUC | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_09_Puesto_Trabajo_ASIS.docx` |
| **T10** | `10` | Sistemas de Expedición, Básculas & OT | `working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_10_Sistemas_Expedicion_Operaciones_ASIS.docx` |

---

## PROMPT A COPIAR Y PEGAR EN CADA VENTANA

```text
Actúa como Ingeniero Principal y Auditor Board-Ready. Tu misión exclusiva es subsanar el 100% de las objeciones emitidas por el Tribunal Experto para la Torre [TORRE_ID] y elevar su entregable Word oficial a calificación 10/10 (Aprobado sin reservas).

### ENTORNO Y ARCHIVOS ASIGNADOS
1. Informe del Tribunal Experto: docs/audits/tribunal_10_towers/AUDIT_EXPERT_[TORRE_ID].md
2. Documento Word oficial a corregir: working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_[NUM_ANEXO]_*.docx
3. Expediente de evidencia y datos respaldados:
   - working/molins/[TORRE_ID]/evidence_ledger.json
   - working/molins/[TORRE_ID]/findings.json
   - working/molins/[TORRE_ID]/blueprint_[TORRE_ID_LOWER]_payload.json
   - working/molins/client_intelligence.json

### MANDATO INMUTABLE: CERO ALUCINACIONES (ZERO SPECULATION)
- PROHIBIDO inventar métricas, servidores, fabricantes, tecnologías o cifras no respaldadas por los archivos de evidencia o el informe de auditoría.
- Toda corrección técnica debe corresponderse estrictamente con la realidad operativa de Cementos Molins:
  * Facturación: 1.144 M€ (~143.000 €/h globales; coste parada operativa central ~13.061 €/h).
  * Empleados: ~3.900.
  * Plantas: Fábrica central Sant Vicenç dels Horts, plantas de Prefabricados (Precast), plantas de hormigón/áridos, e integraciones internacionales (SECIL Portugal, etc.).
- Si se requiere un dato técnico concreto (modelos de switches, versiones de hipervisor, topologías SAN, capacidad de almacenamiento), debe consultarse directamente en working/molins/[TORRE_ID]/evidence_ledger.json o blueprint_[TORRE_ID_LOWER]_payload.json.

### LEYES DE RIGOR MATEMÁTICO Y EDITORIAL
1. Rigor Actuarial Open FAIR™:
   - ALE = SLE * TEF exacto al céntimo en todas y cada una de las fichas de riesgo detalladas.
   - Suma total de ALEs en la tabla resumen (Tabla 10) debe ser matemáticamente exacta a la suma de las fichas.
   - Biyección total con el Heatmap: Las celdas [TEF, LM] del mapa de calor deben reflejar exactamente los códigos de riesgo según su TEF y SLE.
   - El escenario catastrófico P90 debe envolver estrictamente al peor SLE individual (P90 >= peor SLE) y sus partidas deben ser financieramente realistas (evitar sobrecostes de consultoría de emergencia inverosímiles).
2. Consistencia CMMI:
   - Nivel 1 (Inicial): 1.00 a 1.59
   - Nivel 2 (Gestionado / Básico): 1.60 a 2.59
   - Nivel 3 (Definido / Estandarizado): 2.60 a 3.59
   - Nivel 4 (Medido cuantitativamente): 3.60 a 4.59
   - Nivel 5 (Optimizado): 4.60 a 5.00
   - Prohibido calificar puntuaciones como 1.88 "al límite del Nivel 3"; es Nivel 2.
3. Limpieza Editorial y Redundancias:
   - Eliminar párrafos duplicados palabra por palabra.
   - Completar frases truncadas o tablas cortadas.
   - Garantizar tono neutro, aséptico y de alta ingeniería técnica.

### PROTOCOLO DE EJECUCIÓN (PASO A PASO)
1. Lee docs/audits/tribunal_10_towers/AUDIT_EXPERT_[TORRE_ID].md y lista las objeciones concretas identificadas por el auditor.
2. Comprueba los datos canónicos en working/molins/[TORRE_ID]/evidence_ledger.json para asegurar respaldo probatorio.
3. Escribe un script en scripts/polish_[TORRE_ID_LOWER]_definitive_10_out_of_10.py usando `python-docx` para aplicar todas las modificaciones de forma determinista sobre el documento Word asignado:
   - working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/Molins_202610_Anexo_[NUM_ANEXO]_*.docx
4. Ejecuta el script con: python3 scripts/polish_[TORRE_ID_LOWER]_definitive_10_out_of_10.py
5. Inspecciona empíricamente el Word modificado (extrayendo textos y tablas modificadas) para certificar que el 100% de los fallos de la auditoría están resueltos.
6. AISLAMIENTO GITOPS: PROHIBIDO ejecutar `git add`, `git commit` o modificar archivos fuera de tu torre.
```
