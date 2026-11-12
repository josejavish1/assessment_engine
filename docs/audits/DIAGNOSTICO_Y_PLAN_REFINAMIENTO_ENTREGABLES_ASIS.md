---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
last_verified_against: 2026-11-12
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---
# Pliego Formal de Refinamiento de Entregables AS-IS (Auditoría Técnica y Visual)

**Estado:** Aprobado para Planificación e Implementación  
**Fecha:** Noviembre 2026  
**Destinatarios:** Comité de Arquitectura, Dirección de Consultoría Estratégica, Motor de Compilación AST  
**Documentos Objeto:** Anexos Técnicos Especialistas AS-IS (Torre 1 Data Center, Torre 2 Cómputo Híbrido y subsiguientes)

---

## 1. Resumen Ejecutivo de la Revisión de Calidad

A partir de la inspección directa de los entregables preliminares compilados en formato DOCX y PDF, se ha detectado la presencia de artefactos de diseño, vicios de consultoría tradicional e inconsistencias en la delimitación de fronteras metodológicas entre el informe de **Situación Actual (AS-IS)** y el proyecto de **Transformación Futura (TO-BE)**.

El objetivo de este pliego es consolidar, formalizar y estructurar con rigor profesional las 12 observaciones críticas formuladas sobre el documento, estableciendo una especificación técnica libre de ambigüedades para su implementación en el compilador declarativo (`payload_to_ast.py` y `docx_compiler.py`).

---

## 2. Matriz Estructurada de Observaciones y Acciones Requeridas

### Bloque A: Portada, Estructura Formal e Índice

#### 1. Limpieza y Reorganización de la Portada
* **Deficiencia Observada:** La portada contiene etiquetas y bloques flotantes redundantes o carentes de significado de negocio:
  * *"Instalación: Perímetro de infraestructura y activos tecnológicos"* (texto genérico de relleno).
  * *"Proyecto: Diagnóstico de Arquitectura, Madurez Operativa y Resiliencia Cuantitativa (O-FAIR)"* (subtítulo burocrático sobrecargado).
  * El bloque *"STRATEGIC ADVISORY | Noviembre 2026 | Versión 1.0 | Confidencial"* aparece flotando en el cuerpo central de la página en lugar de anclarse en el pie.
* **Acción Requerida:**
  1. Suprimir la línea *"Instalación: Perímetro de infraestructura y activos tecnológicos"*.
  2. Suprimir el subtítulo redundante *"Proyecto: Diagnóstico de Arquitectura..."*. Mantener de forma limpia el Título Principal y el Título del Anexo Técnico correspondiente.
  3. Desplazar los metadatos de versión, fecha y confidencialidad estrictamente a la franja de pie de página inferior de la portada.

#### 2. Automatización Nativa del Índice (TOC OpenXML)
* **Deficiencia Observada:** El índice de contenidos se construye mediante una tabla estática con números de página sintetizados en el AST, generando desconfianza sobre su dinamismo y sincronización si se edita el documento.
* **Acción Requerida:**
  * Implementar el campo nativo de OpenXML para Tabla de Contenidos (`w:fldSimple` o `w:instrText` con instrucción `TOC \o "1-3" \h \z \u`), manteniendo una tabla de fallback estéticamente maquetada y limpia pero con enlaces nativos actualizables en Microsoft Word.

---

### Bloque B: Delimitación de Fronteras (AS-IS vs. TO-BE)

#### 3. Delimitación Estricta del Resumen Ejecutivo (Capítulo 1)
* **Deficiencia Observada:** 
  * El Resumen Ejecutivo afirma de forma prematura que la organización *"quiere alcanzar el Nivel 4 Gestionado"*, fijando una meta arbitraria de consultoría en un documento cuyo único propósito es evaluar el estado actual.
  * Se incluyen párrafos que prescriben la inversión: *"Para neutralizar esta exposición el programa de modernización requiere una inversión de CAPEX de... bla bla bla"*. Esta información pertenece exclusivamente a la propuesta económica y hoja de ruta TO-BE (Capítulo de Roadmap o Caso de Negocio General), no al diagnóstico AS-IS.
* **Acción Requerida:**
  1. Eliminar la fijación arbitraria del Nivel 4 como meta predeterminada en el AS-IS. Si se menciona un nivel objetivo, debe ser exclusivamente en función de marcos normativos sectoriales obligatorios (ej. NIS2 / DORA) y no como un deseo autoimpuesto.
  2. Suprimir cualquier mención a planes de inversión, compras de equipamiento, cifras de CAPEX o programas de modernización en el Capítulo 1. El AS-IS diagnostica la exposición actual y la postura observada, sin adelantar la venta de proyectos futuros.

#### 4. Referenciación Cruzada de Cifras Actuariales
* **Deficiencia Observada:** En el párrafo del Resumen Ejecutivo donde se cita la exposición financiera cuantitativa bajo Open FAIR (ej. pérdida esperada y simulaciones estocásticas), el lector no dispone de una llamada que le indique dónde consultar el respaldo técnico de esas cifras.
* **Acción Requerida:**
  * Incluir una referencia cruzada explícita y ejecutiva (ej. *"El desglose detallado de los escenarios y la justificación actuarial de estas cifras se desarrolla en el Capítulo 4 y en el Apéndice B"*).

---

### Bloque C: Marco Metodológico y Coherencia Tipográfica

#### 5. Supresión de Metodología de Calibración en Tres Fases (Capítulo 2)
* **Deficiencia Observada:** El apartado metodológico del Capítulo 2 incluye un bloque teórico denominado *"Metodología de calibración en tres fases"* que resulta académico, accesorio y no aporta valor práctico al cliente.
* **Acción Requerida:**
  * Eliminar íntegramente la subsección *"Metodología de calibración en tres fases"*.

#### 6. Estandarización y Armonización Tipográfica (Capítulo 2)
* **Deficiencia Observada:** En las tablas del Capítulo 2 (*Escala analítica de madurez CMMI* y *Capacidad evaluada de cálculo y score*), se aprecian discrepancias en los tamaños de fuente (variaciones entre 8.0, 8.5 y 10.0 pt sin criterio jerárquico).
* **Acción Requerida:**
  * Unificar la escala tipográfica en todas las tablas del Capítulo 2 bajo un patrón estricto (Cabeceras: 9.0 pt Bold; Celdas de datos: 8.5 pt Regular; Etiquetas de badge: 8.0 pt Bold).

---

### Bloque D: Reingeniería Integral de la Exposición al Riesgo (Capítulo 4)

#### 7. Evaluación y Supresión del Hexágono de Retorno/Resiliencia
* **Deficiencia Observada:** La presencia del diagrama o referencia al *"Hexágono de retorno de resiliencia y eficiencia"* en el Capítulo 4 genera confusión conceptual y no encaja con el estándar cuantitativo Open FAIR.
* **Acción Requerida:**
  * Suprimir el hexágono de resiliencia del Capítulo 4 para focalizar el capítulo estrictamente en la modelización actuarial de pérdidas.

#### 8. Simplificación y Rediseño Visual de las Cabeceras de Ficha de Riesgo
* **Deficiencia Observada:**
  * Los títulos de las tarjetas están saturados de texto: concatenan código, capacidad, pilar, cartera y porcentajes en un solo bloque denso (ej. `[RVS06] Gestión de Puntos Calientes... | Cartera: Tier 1 (#1 | 22%)`).
  * Los colores de severidad son excesivamente saturados y estridentes, alejándose de una estética editorial sobria y ejecutiva.
* **Acción Requerida:**
  1. Descongestionar y acortar el título de cabecera: presentar de forma limpia el ID y la Capacidad de forma legible, reubicando los metadatos secundarios.
  2. Suavizar la paleta cromática hacia tonos corporativos mates y elegantes (Slate, Navy, Amber y Crimson desaturados, cumpliendo WCAG 2.1).

#### 9. Erradicación del Texto Boilerplate ("Evento Amenaza Iniciador")
* **Deficiencia Observada:** En todas las tarjetas de riesgo, la primera columna de la cadena Bow-Tie repite exactamente el mismo texto genérico (*"Avería o fallo de componente electromecánico principal durante la operación continua de planta"*), lo que destruye el valor del análisis y denota contenido automatizado sin criterio.
* **Acción Requerida:**
  * Eliminar la caja estática de *"Evento Amenaza Iniciador"* si no aporta un desencadenante específico y diferencial por escenario.

#### 10. Sustitución de Directivas TO-BE por la Justificación Forense de Cifras Actuariales
* **Deficiencia Observada:**
  * La fila inferior de la tarjeta contiene una *"Directiva de Mitigación Ejecutiva"*, la cual vuelve a incurrir en el error de prescribir soluciones futuras dentro de un informe AS-IS.
  * El cliente y el CFO se preguntan de dónde salen los importes (ALE de 169.249 €, SLE de 470.137 €) sin que la tarjeta explique la fórmula física observada.
* **Acción Requerida:**
  * Reemplazar la franja de *"Directiva de Mitigación Ejecutiva"* por una sección de alto valor para el CFO: **Justificación y Desglose Actuarial del Cálculo**.
  * Explicar de forma transparente los factores empíricos que componen el cálculo:
    $$\text{Impacto por Evento (SLE)} = \text{MTTR Observado (2,5 h)} \times \text{Coste Hora de Planta (15.600 €/h)} + \text{Costes de Reposición (6.000 €)}$$
    $$\text{Frecuencia Anual (LEF)} = 0,36 \text{ eventos/año (1 cada 2,8 años)}$$
    $$\text{Pérdida Anualizada (ALE)} = \text{SLE} \times \text{LEF}$$

#### 11. Calibración Realista de Cifras y Enfoque Epistémico de Hipótesis
* **Deficiencia Observada:**
  * **Cifras Desorbitadas:** En Torre 1 continúan apareciendo cifras millonarias no calibradas (ALE total superior a 1.050.000 € y SLEs de 470.000 €), contradiciendo el dictamen previo de que una parada puntual en una planta industrial con mantenimiento 24/7 y contratos de fabricante se resuelve en 2 a 4 horas (exposición de 25.000 € a 45.000 € por evento, y ALE de torre en torno a 118.500 €/año).
  * **Tono Catastrófico vs. Hipótesis Técnica:** Las descripciones afirman hechos futuros de forma determinista y sensacionalista: *"esta recirculación revienta los compresores, dispara la factura eléctrica y provoca caídas simultáneas..."*. En ingeniería de riesgos, una vulnerabilidad no "revienta" equipos de forma garantizada; incrementa la probabilidad de fallo.
* **Acción Requerida:**
  1. Re-calibrar la base de datos de Torre 1 a las cifras reales acordadas (ALE consolidado de torre ~118.500 €/año, SLEs de 25.000 € - 45.000 € basados en 2-4 horas de parada real).
  2. Modular la redacción al lenguaje riguroso de hipótesis actuarial: *"Bajo condiciones de estrés operacional no mitigadas, la persistencia de gradientes térmicos elevados incrementa la probabilidad de parada por sobrecalentamiento en los compresores, pudiendo ocasionar una interrupción del servicio estimada en..."*.
  3. Eliminar o reformular el concepto abstracto de *"Acoplamiento sistémico estrecho (Cascada crítica)"* por un término claro para el cliente (ej. *"Impacto en Cadena: Alto - Propagación a múltiples líneas"*).

---

### Bloque E: Conclusiones y Apéndices

#### 12. Supresión de Proyecciones de Inversión en Capítulo 5 y Eliminación Integral del Apéndice A
* **Deficiencia Observada:**
  * El Capítulo 5 incluye la tabla *"Proyección Multi-Horizonte del Coste de Inacción vs. Programa de Modernización"* (Horizontes de 1, 3 y 5 años con CAPEX, ROI y Payback). Todo este contenido es exclusivo de la fase de propuesta TO-BE.
  * El *Apéndice A ("Registro de Custodia de Fuentes de Información")* resulta burocrático, prescindible y no aporta sustancia técnica al especialista ni al decisor.
* **Acción Requerida:**
  1. Transformar el Capítulo 5 en **Síntesis Diagnóstica y Conclusiones del AS-IS**, resumiendo la postura de madurez actual, las principales vulnerabilidades encontradas y la urgencia de actuar, suprimiendo las tablas de CAPEX, ROI y Horizontes de modernización.
  2. Eliminar completamente el Apéndice A del documento. Renombrar el Apéndice B (Metodología Open FAIR) como el único apéndice técnico de referencia.

---

## 3. Criterios de Aceptación

1. **Pureza de Fase:** Ningún capítulo del entregable AS-IS contendrá cifras de CAPEX, presupuestos de modernización, plazos de payback o promesas de inversión TO-BE.
2. **Realismo Actuarial:** Todas las cifras de exposición financiera reflejarán tiempos de recuperación de 1,5 a 4,0 horas respaldados por la justificación de costes reales de planta.
3. **Lenguaje Sobrio y Probabilístico:** Cero dramatismos o términos coloquiales en las descripciones de riesgos.
4. **Acabado Editorial:** Portada limpia, índice automatizado y tipografía uniforme en todas las tablas.
