---
status: Draft
owner: docs-governance
source_of_truth:
  - ../../src/assessment_engine/scripts/run_scoring.py
  - ../../src/assessment_engine/scripts/run_tower_blueprint_engine.py
  - ../../src/assessment_engine/scripts/run_executive_annex_synthesizer.py
  - ../../src/assessment_engine/scripts/render_tower_blueprint.py
  - ../../src/assessment_engine/scripts/build_global_report_payload.py
  - ../../src/assessment_engine/scripts/run_global_pipeline.py
  - ../../src/assessment_engine/scripts/run_commercial_pipeline.py
  - ../../src/assessment_engine/scripts/render_web_presentation.py
  - ../../engine_config/towers/T3/tower_definition_T3.json
  - ../../working/vodafone_demo/T3/scoring_output.json
  - ../../working/vodafone_demo/T3/findings.json
  - ../../working/vodafone_demo/T3/blueprint_t3_payload.json
  - ../../working/vodafone_demo/T3/approved_annex_t3.template_payload.json
  - ../../working/vodafone_demo/global_report_payload.json
  - ../../working/vodafone_demo/commercial_report_payload.json
last_verified_against: 2026-05-02
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Assessment coherence remediation

Este documento deja persistido el diagnóstico de incoherencias detectadas en la pipeline de entregables para retomarlo en sesiones futuras sin depender del `plan.md` efímero de la sesión.

El objetivo de esta remediación es **sistémico y prospectivo**:

- no corregir solo `vodafone_demo`;
- no parchear un único tower payload o un único DOCX;
- sino asegurar que **cualquier caso futuro** use una única semántica coherente para score, banda, target, color, severidad y narrativa.

## Problema

La pipeline actual no mantiene una única semántica compartida para:

- score cuantitativo;
- banda cualitativa;
- madurez objetivo;
- severidad narrativa;
- y traducción visual por color/estado.

El resultado es que varios entregables pueden hablar del mismo caso con lecturas incompatibles entre sí.

## Caso que disparó la investigación

El caso `working/vodafone_demo/T3` expone la desalineación de forma evidente:

- `scoring_output.json` da `tower_score_exact = 3.528` y `tower_score_display_1d = 3.5`;
- `approved_annex_t3.template_payload.json` fija `target_maturity = 3.8`;
- la brecha real es pequeña;
- pero annex y blueprint usan un lenguaje propio de una situación casi crítica.

Ejemplos observados en T3:

- “infraestructura operada mediante un modelo predominantemente manual, reactivo y fragmentado”;
- “riesgo material para la continuidad operativa”;
- “la inacción perpetuará un modelo operativo de alto riesgo”;
- uso repetido de NIS2 como amplificador de urgencia.

Con un score medio-alto y un target cercano, esa narrativa no resulta proporcional ni defendible como assessment cliente-facing.

`vodafone_demo` se usa aquí solo como **caso índice** para detectar y demostrar el fallo. La corrección requerida debe aplicarse al diseño general de la pipeline, de modo que la misma incoherencia no reaparezca en ningún cliente futuro.

## Hallazgos confirmados

### 1. Doble sistema de bandas de madurez

Originalmente había al menos dos fuentes distintas para traducir score a banda cualitativa:

1. `run_scoring.py` usa `score_bands` definidos por torre en `engine_config/towers/*/tower_definition_*.json`.
2. `run_executive_annex_synthesizer.py` usa `derive_maturity_band()` con umbrales hardcodeados y etiquetas diferentes.

Consecuencia: un mismo score podía tener dos lecturas cualitativas distintas según el artefacto.

**Estado 2026-05-01:** la resolución `score -> banda` quedó centralizada en `src/assessment_engine/scripts/lib/maturity_band.py` y ya es consumida por scoring, annex, blueprint, global y web. Esta pieza mantiene el diagnóstico histórico y el resto de remediaciones abiertas.

### 2. T3 ya demuestra la inconsistencia

Para `T3`:

- la definición de torre clasifica `3.4 - 4.19` como `Nivel 4 - Optimizado`;
- `scoring_output.json` asigna a `3.528` la banda `Nivel 4 - Optimizado`;
- el annex usa otra semántica y lo presenta como `Gestionado`.

Esto rompe cualquier coherencia entre score, banda y lenguaje.

### 3. El blueprint DOCX mezcla dos fuentes

`render_tower_blueprint.py` no renderiza solo desde `blueprint_*_payload.json`.

También carga `approved_annex_*.template_payload.json` y mezcla:

- snapshot y contenido estructural del blueprint;
- score, banda, target, perfil de madurez y cierre procedentes del annex.

Consecuencia: el blueprint DOCX no es una proyección limpia de un único payload. Si blueprint y annex no están alineados, el propio documento queda internamente contaminado.

### 4. El tono del blueprint está inducido a dramatizar

El closing del blueprint usa prompting que fuerza:

- expansión amplia del diagnóstico;
- `cost_of_inaction` severo;
- riesgos estructurales fuertes;
- y conexión intensa con agenda del CEO y presión regulatoria.

No existen guardrails suficientes que modulen el lenguaje según:

- score actual;
- gap al target;
- fuerza de evidencia;
- sensibilidad del tipo de entregable.

### 5. El annex hereda y amplifica el problema

El annex reutiliza business risks y snapshot del blueprint en:

- `executive_summary`;
- `pillar_score_profile`;
- `gap_rows`;
- `conclusion`.

No hay una capa de recalibración que impida lenguaje extremo cuando:

- el score es medio-alto;
- la brecha al target es pequeña;
- o la evidencia encontrada es de “base funcional con margen de mejora”.

### 6. `findings.json` es más moderado que los DOCX

En `T3/findings.json` aparecen formulaciones del tipo:

- “base funcional ya implantada”;
- “evidencia suficiente para sostener un nivel operativo aprovechable”;
- “mantiene margen de mejora para alcanzar un nivel plenamente optimizado y medible”.

Es decir, la capa de findings parece más compatible con un 3.x medio-alto que la narrativa final renderizada.

### 7. El target maturity puede quedar demasiado cerca sin forzar una narrativa coherente

En `client_intelligence.json`, T3 tiene `target_maturity = 3.8`.

El sistema hoy permite combinar:

- score actual razonable;
- target cercano;
- y relato de urgencia estructural muy fuerte.

No hay una regla explícita que diga:

- gap pequeño -> lenguaje incremental;
- gap grande -> lenguaje de transformación estructural.

### 8. El global introduce sus propias simplificaciones erróneas

`build_global_report_payload.py` consolida los blueprints, pero simplifica en exceso:

- asigna banda casi binaria (`Optimizada` vs `Básica`);
- colorea estados con una lógica distinta a la de torre;
- agrega riesgos con `impact_level = "Alto"` por defecto.

Consecuencia: el global puede pintar en verde una torre con score medio-alto mientras el texto describe amenazas sistémicas severas.

### 9. El global propaga el sesgo de los blueprints

El informe global toma su narrativa de torre desde `executive_snapshot.bottom_line` de los blueprints.

Si el blueprint dramatiza, el global dramatiza también.

### 10. El comercial es otro tipo de artefacto

`Account_Action_Plan_*.docx` es explícitamente:

- `CONFIDENCIAL - USO INTERNO`;
- orientado a venta, urgencia, objeciones, TAM y posicionamiento.

En ese artefacto el tono agresivo no es necesariamente un bug.

El problema grave está en los artefactos cliente-facing o técnico-estratégicos:

- annex por torre;
- blueprint por torre;
- informe global;
- dashboard web.

### 11. El dashboard web también hereda la incoherencia

`render_web_presentation.py` consume:

- `global_report_payload.json`;
- blueprints por torre.

Por tanto replica:

- score;
- target;
- riesgos estructurales;
- coste de inacción;
- narrativa ejecutiva.

Si las capas previas salen desalineadas, el dashboard también.

### 12. El blueprint recalcula scores con otra lógica

`run_tower_blueprint_engine.py` no reutiliza directamente `scoring_output.json` como fuente autoritativa de score por pilar.

En su lugar:

- vuelve a agrupar respuestas por pilar;
- calcula una media simple directa de respuestas;
- y redondea a una decimal ya en esa fase.

Esto introduce otra duplicación semántica:

- `run_scoring.py` calcula scores exactos por KPI, luego por pilar, y conserva más precisión;
- el blueprint usa otro cálculo más tosco y más temprano.

Aunque en `vodafone_demo/T3` las cifras quedan parecidas, el diseño sigue siendo inconsistente y puede divergir en otros casos.

### 13. El global toma el target desde el primer pilar

`build_global_report_payload.py` no calcula el target global de torre de forma robusta.

Actualmente toma:

- `data["pillars_analysis"][0].get("target_score", 4.0)`

Es decir, usa el target del primer pilar como target de toda la torre.

Eso solo funciona si todos los pilares comparten exactamente el mismo target. Como diseño es frágil y no debería asumirse.

### 14. Hay metadatos hardcodeados que rompen trazabilidad

`build_global_report_payload.py` fija:

- `date = "14 de Abril de 2026"`

Esto hace que el payload y los entregables derivados puedan mostrar una fecha ficticia o desfasada, reduciendo trazabilidad y credibilidad.

### 15. El global hardcodea severidad y prioridad

En `build_global_report_payload.py`:

- los riesgos estratégicos se crean con `impact_level = "Alto"` por defecto;
- las iniciativas se crean con `priority = "Alta"` por defecto.

Esto destruye granularidad y contamina cualquier análisis posterior que tome esos campos como semánticamente fiables.

### 16. Hay defaults silenciosos cuando falla `client_intelligence`

En `build_case_input.py`, si la carga de `client_intelligence.json` falla:

- se hace `except Exception: pass`;
- y el sistema cae silenciosamente al default `target_maturity = 4.0`.

Esto es peligroso porque una degradación de contexto o un error de parsing no deja señal visible y cambia la semántica del caso sin trazabilidad clara.

### 17. Existe abuso de `except` amplios y silenciosos

Se han encontrado varios puntos con:

- `except Exception: pass`
- o capturas amplias que degradan lógica sin mecanismo claro de invalidación.

Esto aparece en zonas de:

- carga de inteligencia;
- render;
- construcción de payloads;
- y parsing auxiliar.

Para una pipeline de evaluación y reporting, esto incrementa el riesgo de generar entregables aparentemente válidos pero semánticamente degradados.

### 18. El perfil de modelo comercial está acoplado al refiner global

`run_commercial_refiner.py` resuelve el modelo con:

- `resolve_model_profile_for_role("global_refiner")`

Eso sugiere que el comercial no tiene una configuración de rol claramente separada del refiner global. Aunque no rompe por sí solo la coherencia documental, sí es una señal de acoplamiento innecesario entre dominios de salida distintos.

### 19. La plantilla comercial reutiliza la ruta de plantilla global

`run_commercial_pipeline.py` pasa a `render_commercial_report.py` la ruta de:

- `resolve_global_report_template_path()`

El comercial sí usa realmente esa plantilla al crear el DOCX.

Puede ser intencional, pero como mínimo es un punto de revisión:

- o existe una plantilla comercial específica y no se está usando;
- o se está reutilizando la plantilla global para un artefacto con semántica distinta.

En ambos casos conviene dejar explícito si es una decisión deliberada o una deuda técnica.

## Cadena real de propagación

La dependencia efectiva observada hoy es:

1. `scoring_output.json` y respuestas alimentan el blueprint.
2. El blueprint alimenta el annex.
3. El annex vuelve a contaminar el blueprint DOCX renderizado.
4. Los blueprints alimentan el global.
5. El global alimenta el comercial.
6. El global y los blueprints alimentan el dashboard web.
7. El `.tar.gz` solo empaqueta esos artefactos ya generados.

Conclusión: una incoherencia en scoring/semántica de torre se propaga casi a toda la familia de entregables.

## Fuente única de verdad requerida

La corrección debe partir de una única semántica compartida para todo el sistema y para cualquier caso futuro.

### 1. Score

- mantener score exacto interno;
- mantener score redondeado de presentación;
- nunca recalcularlo de forma divergente en una capa posterior.

### 2. Banda cualitativa

- resolverla en un helper o contrato único;
- o bien usar una política central común, o bien reutilizar la definición de bandas de torre;
- pero nunca permitir mapeos locales hardcodeados por artefacto.

### 3. Target maturity

- debe venir de una única política compartida;
- debe incluir justificación;
- debe validarse contra el score actual y el tipo de transformación.

#### Rediseño propuesto para target maturity

La lógica futura no debe depender de una cifra fijada manualmente ni de un mínimo hardcodeado visible en código. Debe generar objetivos que, en la práctica, sean:

- superiores al estado actual cuando exista margen razonable de evolución;
- suficientemente ambiciosos para sostener una agenda de transformación relevante;
- y defendibles ante el cliente con argumentos técnicos y de negocio.

#### Variables que sí deben entrar en el cálculo

El target debe construirse a partir de señales explícitas y auditables, por ejemplo:

- score actual de la torre;
- criticidad de negocio de la torre;
- presión regulatoria aplicable a la torre;
- urgencia de cambio;
- horizonte de transformación del cliente;
- restricciones operativas;
- evidencia de programas activos ya en marcha;
- y madurez sectorial esperable para organizaciones comparables.

#### Forma recomendada de cálculo

En lugar de “poner un número”, el sistema debería calcular:

1. una **madurez base esperada** para la torre en ese tipo de cliente;
2. un **uplift objetivo** sobre el score actual;
3. y un **target final acotado** por credibilidad y por capacidad de ejecución.

Conceptualmente:

- `expected_maturity_baseline`
- `uplift_window`
- `credibility_cap`
- `target_maturity = min(max(score_actual + uplift_window, expected_maturity_baseline), credibility_cap)`

No hace falta que esas variables usen esos nombres exactos, pero sí esa lógica.

#### Requisitos funcionales del cálculo

1. El target debe ser normalmente **mayor que el score actual**.
2. El target no debe quedar tan cerca que la propuesta de evolución pierda sentido.
3. El target no debe ser utópico ni tan alto que resulte inverosímil.
4. El target debe poder justificarse sin mencionar ninguna regla comercial interna.
5. La justificación debe salir de factores observables del cliente y del contexto de la torre.

#### Cómo justificar el target ante el cliente

La explicación no debe decir “se fija un mínimo comercial”.

Debe poder expresarse en términos como:

- criticidad del dominio para el negocio;
- necesidad de operar de forma predecible y gobernada;
- exigencia regulatoria y de resiliencia;
- agenda de simplificación y automatización;
- presión de escala multinacional o complejidad operativa;
- nivel de madurez esperable para soportar los objetivos del negocio.

Ejemplo de justificación aceptable:

> La madurez objetivo se fija en un nivel superior al actual porque la torre soporta capacidades críticas para continuidad, crecimiento digital y cumplimiento. El estado actual permite operar, pero no ofrece todavía el nivel de industrialización, gobierno y repetibilidad que exige el contexto del cliente. El objetivo propuesto representa un nivel alcanzable dentro del horizonte de transformación definido y consistente con la criticidad operativa del dominio.

#### Restricción importante

La lógica debe tender a producir objetivos comercialmente útiles para consultoría, pero esa ambición debe emerger de la política de cálculo y de los factores del caso, no de un número mínimo hardcodeado tipo `3.9`.

#### Cambios de implementación necesarios

- sacar `target_maturity` de la improvisación del prompt y llevarlo a una política explícita de cálculo;
- persistir junto al target los factores usados y su justificación;
- eliminar el default silencioso `4.0` como fallback no trazable;
- hacer que scoring, blueprint, annex, global y web lean exactamente el mismo target ya resuelto;
- y permitir auditoría posterior del tipo:
  - score actual;
  - baseline esperado;
  - uplift aplicado;
  - target final;
  - justificación textual.

### 4. Tono narrativo

- debe estar acotado por score, gap y evidencia;
- no puede depender solo del estilo del prompt;
- debe diferenciar claramente entre:
  - assessment cliente-facing;
  - entregable técnico interno;
  - pieza comercial interna.

### 5. Claims regulatorios

- deben usarse solo cuando la torre, la evidencia y la severidad lo justifiquen;
- NIS2 no debe actuar como refuerzo retórico automático.

## Reglas de coherencia obligatorias

Mañana, cualquier cambio debe respetar estas reglas para todos los clientes y no solo para `vodafone_demo`:

1. Un mismo score no puede tener dos bandas distintas en artefactos diferentes.
2. Un score medio-alto con target cercano no puede detonar lenguaje de colapso o “riesgo inaceptable” salvo evidencia excepcional.
3. El blueprint DOCX no debe mezclar semánticas incompatibles entre blueprint y annex.
4. El global no puede reinterpretar bandas, colores o severidad con reglas distintas a la torre.
5. El comercial puede mantener urgencia comercial, pero no debe contaminar la semántica cliente-facing.
6. El dashboard web debe ser consumidor fiel de la misma semántica compartida.

## Orden recomendado de corrección

Antes de empezar a tocar código o regenerar artefactos, hacer **backup** de los archivos y outputs relevantes para poder comparar antes/después y tener rollback seguro.

1. Auditar de extremo a extremo el flujo:
   respuestas -> scoring -> findings -> blueprint -> annex -> global -> web.
2. Fijar un helper o contrato único para:
   `score -> banda -> color -> lectura`.
3. Eliminar o redirigir recalibraciones locales en:
   - annex;
   - blueprint render;
   - global;
   - web.
4. Revisar la política de `target_maturity`.
5. Acotar prompting y postprocesado para el tono cliente-facing.
6. Añadir tests y validaciones de consistencia.
7. Regenerar `vodafone_demo` completo, al menos T2, T3 y T5, y después global/web.

## Priorización por retorno de valor

La priorización siguiente no está ordenada por elegancia técnica sino por **retorno de valor esperado**:

- cuánto reduce incoherencias visibles para cliente;
- cuánto desbloquea una semántica común para todos los artefactos;
- cuánto evita retrabajo posterior;
- y cuánto corrige problemas sistémicos con un esfuerzo relativamente contenido.

### Prioridad 0 — Máximo retorno inmediato

Estas piezas son las que más valor devuelven antes y las que más reducen caos aguas abajo.

#### P0.1 Unificar la fuente de verdad de score, banda, color y lectura

Incluye:

- centralizar `score -> banda -> color -> lectura`;
- eliminar `derive_maturity_band()` hardcodeado del annex;
- evitar recalculados locales incompatibles en global y web.

**Retorno de valor:** muy alto.  
**Por qué va primero:** una sola corrección aquí limpia annex, blueprint, global y dashboard a la vez.

**Estado 2026-05-01:** completado para la traducción de `score -> banda`; siguen abiertas las remediaciones sobre color, target, severidad y tono.

#### P0.2 Corregir la política de target maturity

Incluye:

- sacar el target de una política explícita y auditable;
- eliminar defaults silenciosos como `4.0`;
- garantizar que el target sea ambicioso pero justificable;
- y que se propague igual a todas las capas.

**Retorno de valor:** muy alto.  
**Por qué va primero:** el target condiciona tono, gap, roadmap y narrativa de transformación.

#### P0.3 Acotar el tono cliente-facing

Incluye:

- introducir guardrails en blueprint, annex, global y web;
- ligar severidad del lenguaje a score, gap y evidencia;
- separar claramente assessment de discurso comercial interno.

**Retorno de valor:** muy alto.  
**Por qué va primero:** es el punto más visible para cliente y el que más afecta credibilidad comercial y consultiva.

#### P0.4 Evitar que el blueprint DOCX mezcle semánticas incompatibles

Incluye:

- revisar la mezcla blueprint + annex en `render_tower_blueprint.py`;
- decidir una sola fuente para score, target y perfil de madurez en el blueprint renderizado.

**Retorno de valor:** muy alto.  
**Por qué va primero:** hoy el blueprint es un punto de contaminación central para varias incoherencias.

### Prioridad 1 — Alto retorno estructural

Estas piezas no siempre son las más visibles en el primer minuto, pero consolidan la solución y evitan recaídas.

#### P1.1 Hacer que scoring sea la fuente autoritativa de cálculo

Incluye:

- dejar de recalcular scores por pilar en el blueprint;
- reutilizar `scoring_output.json` o un helper común equivalente;
- mantener precisión interna sin redondeos tempranos.

**Retorno de valor:** alto.  
**Por qué va aquí:** evita divergencias ocultas y estabiliza la semántica matemática de toda la pipeline.

#### P1.2 Corregir la consolidación global

Incluye:

- quitar la lógica binaria `Optimizada/Básica`;
- eliminar severidades y prioridades hardcodeadas;
- calcular target y colores desde la misma semántica de torre.

**Retorno de valor:** alto.  
**Por qué va aquí:** el global es el agregador ejecutivo; si queda mal, amplifica todos los errores previos.

#### P1.3 Acotar claims regulatorios

Incluye:

- gobernar uso de NIS2 y marcos similares por torre;
- impedir que se usen como amplificador retórico automático;
- exigir relación explícita con evidencia y criticidad real.

**Retorno de valor:** alto.  
**Por qué va aquí:** protege la credibilidad del diagnóstico y reduce sobredramatización.

#### P1.4 Eliminar defaults silenciosos y capturas amplias que degradan semántica

Incluye:

- sustituir `except Exception: pass` en puntos críticos;
- hacer explícitos fallbacks y su trazabilidad;
- impedir degradaciones invisibles de `client_intelligence`, target o render.

**Retorno de valor:** alto.  
**Por qué va aquí:** no mejora el Word por sí sola, pero evita incoherencias fantasma y errores difíciles de detectar.

### Prioridad 2 — Medio retorno, alto valor de consolidación

Estas tareas rematan la robustez del sistema y mejoran mantenibilidad y reproducibilidad.

#### P2.1 Añadir tests de coherencia transversal

Incluye validaciones para:

- score;
- banda;
- target;
- color;
- tono narrativo;
- y coherencia entre payload y render.

**Retorno de valor:** medio-alto.  
**Por qué va aquí:** evita regresiones, pero conviene hacerlo cuando la semántica principal ya esté decidida.

#### P2.2 Revisar visualizaciones y dashboard

Incluye:

- heatmaps;
- radar;
- status colors;
- y cualquier simplificación visual que no respete el payload real.

**Retorno de valor:** medio.  
**Por qué va aquí:** importante para coherencia final, pero depende de haber corregido antes score/banda/target.

#### P2.3 Revisar naming, joins y normalización transversal

Incluye:

- nombres de torres;
- labels de capacidades;
- iniciativas;
- y referencias cruzadas entre artefactos.

**Retorno de valor:** medio.  
**Por qué va aquí:** mejora consistencia técnica y reduce fallos sutiles de consolidación.

#### P2.4 Revisar plantilla comercial y acoplamientos de pipeline

Incluye:

- confirmar si el comercial debe usar plantilla global o propia;
- separar perfiles de modelo entre global y comercial;
- dejar explícitas fronteras entre outputs cliente-facing e internos.

**Retorno de valor:** medio.  
**Por qué va aquí:** aporta limpieza arquitectónica y evita contaminación conceptual futura.

### Prioridad 3 — Investigación y endurecimiento adicional

Estas líneas son valiosas, pero su retorno es mayor una vez corregido el núcleo.

#### P3.1 Auditar contaminación legacy

Validar si piezas `_legacy` o compatibilidades antiguas siguen alterando el flujo vigente.

#### P3.2 Revisar casos borde con evidencia débil

Comprobar comportamiento cuando faltan respuestas, claims o contexto suficiente.

#### P3.3 Revaluar el peso del dossier de inteligencia frente a la evidencia técnica

Determinar si `client_intelligence` está condicionando demasiado target y narrativa.

#### P3.4 Revisar la lógica de priorización de iniciativas y dependencias cruzadas

Alinear prioridades, quick wins y dependencias con impacto, esfuerzo y bloqueos reales.

## Secuencia recomendada de ejecución

Si mañana hubiera que maximizar valor lo antes posible, el orden práctico recomendado sería:

1. **P0.1** unificar score/banda/color/lectura.
2. **P0.2** rediseñar target maturity.
3. **P0.4** limpiar la mezcla blueprint/annex en render.
4. **P0.3** recalibrar tono cliente-facing.
5. **P1.1** hacer de scoring la fuente autoritativa.
6. **P1.2** corregir la consolidación global.
7. **P1.3** acotar claims regulatorios.
8. **P1.4** eliminar fallbacks silenciosos.
9. **P2.1** añadir tests transversales.
10. **P2.2 + P2.3 + P2.4** rematar visualización, naming y acoplamientos.
11. Regenerar artefactos de referencia y revisar el resultado completo.

## Qué no hacer primero aunque sea tentador

- No empezar por retocar textos individuales de `vodafone_demo`.
- No empezar por el dashboard antes de arreglar score/banda/target.
- No empezar por el comercial interno como si fuera el principal problema.
- No añadir más prompting sin antes fijar la semántica base.

Eso solo movería síntomas sin corregir la lógica central.

## Otras líneas de investigación abiertas

Además de los hallazgos ya confirmados, todavía conviene investigar estas familias de problemas potenciales:

### 1. Desalineación entre schemas y uso real

Puede haber campos presentes en los modelos que:

- se calculan de forma distinta según el paso;
- se rellenan con semánticas diferentes;
- o se preservan formalmente en contrato pero no en significado.

### 2. Contradicciones entre payload y DOCX renderizado

Es posible que el JSON y el Word final no cuenten exactamente la misma historia por:

- defaults de render;
- placeholders;
- limpieza textual;
- o fusiones tardías de fuentes.

### 3. Pérdida de trazabilidad de evidencias

Hay que comprobar si afirmaciones fuertes de blueprint, annex, global o web siguen siendo trazables hacia:

- respuestas del cliente;
- findings;
- claims del dossier;
- o señales verificables del caso.

### 4. Reglas distintas por torre sin una política clara

Puede haber diferencias de bandas, thresholds, lecturas operativas o semánticas por torre que no respondan a una política común ni a una razón explícita.

### 5. Normalización inconsistente de nombres y labels

Hay riesgo de que la misma torre, capacidad o iniciativa se nombre de forma distinta en:

- scoring;
- blueprint;
- annex;
- global;
- comercial;
- dashboard.

Eso puede romper joins lógicos y consolidaciones narrativas.

### 6. Redondeos demasiado tempranos

Si el sistema redondea antes de tiempo, una variación pequeña puede alterar:

- banda;
- color;
- prioridad;
- target;
- o tono narrativo.

### 7. Sesgo inducido por prompting aunque el payload sea correcto

Incluso con payloads técnicamente válidos, algunos prompts pueden empujar a:

- dramatizar;
- comercializar;
- o sobredimensionar el impacto.

### 8. Contaminación por lógica legacy

Hay que confirmar hasta qué punto piezas `_legacy`, compatibilidades antiguas o adaptadores heredados siguen afectando el flujo vigente.

### 9. Visualizaciones con semántica simplificada

Radar, heatmaps, colores, tablas o roadmap pueden estar simplificando el estado de forma incoherente respecto al payload estructurado.

### 10. Divergencia entre torres y consolidado global

El global puede estar reinterpretando el caso en lugar de agregarlo fielmente, generando una historia más dura o más simple que la suma real de T2/T3/T5.

### 11. Priorización de iniciativas poco conectada al gap real

Hay que verificar si prioridades, quick wins y programas:

- salen de una lógica explícita;
- o si se rellenan con defaults y simplificaciones que no respetan score, esfuerzo, dependencia e impacto.

### 12. Dependencias cruzadas mal modeladas

Algunas recomendaciones pueden depender de otras torres o programas, pero no estar expresadas con suficiente claridad en la secuencia de ejecución.

### 13. Peso excesivo del dossier de inteligencia sobre la evidencia técnica

El `client_intelligence` puede estar condicionando demasiado:

- target;
- tono;
- presión regulatoria;
- y discurso estratégico,

por encima de la evidencia técnica real del caso.

### 14. Casos borde con datos escasos o evidencia débil

Hay que revisar qué ocurre cuando faltan:

- respuestas;
- claims;
- señales regulatorias;
- o contexto suficiente.

El sistema no debería rellenar automáticamente con narrativa segura si la evidencia no lo soporta.

### 15. Falta de tests de coherencia transversal

Puede que existan tests por contrato o render, pero no tests que validen de extremo a extremo:

- score;
- banda;
- target;
- color;
- prioridad;
- y tono narrativo.

Sin esos tests, la incoherencia puede reaparecer aunque una parte del sistema se haya corregido.

## Cómo evitar que la calidad vuelva a degradarse

La remediación no será suficiente si no se convierte también en disciplina de desarrollo. El objetivo no es solo corregir esta iteración, sino impedir que futuras modificaciones rompan de nuevo score, target, bandas, tono o trazabilidad.

### 1. Convertir la semántica en contratos de código

Las best practices clave no deben vivir solo en prompts o en conocimiento implícito del equipo. Deben materializarse en:

- helpers compartidos;
- políticas configurables;
- esquemas validados;
- y tests automáticos.

Regla: si una decisión de negocio o de reporting es importante, no puede depender solo de “recordarlo”.

### 2. Introducir una capa explícita de políticas

Debe existir una capa de política claramente identificable para:

- bandas de madurez;
- target maturity;
- severidad narrativa;
- colores y estados visuales;
- uso de claims regulatorios.

Regla: ninguna de esas semánticas debe quedar embebida de forma local dentro de renderizadores, refinadores o scripts aislados.

### 3. Tests de coherencia obligatorios en CI

La CI debería bloquear cambios que rompan:

- unicidad de score por torre;
- coincidencia de banda entre capas;
- target consistente entre payloads;
- ausencia de recalculados divergentes;
- coherencia entre payload y render;
- y restricciones mínimas de tono para cliente-facing.

Regla: sin tests transversales, la calidad volverá a degradarse.

### 4. Golden cases y artefactos de referencia

Debe mantenerse un pequeño conjunto de casos de referencia estables para comparar:

- payloads de scoring;
- payloads de blueprint;
- annex;
- global;
- web.

No para congelar el texto palabra por palabra, sino para detectar cambios de semántica no deseados.

### 5. Code review con checklist específico de coherencia

Toda PR que toque scoring, blueprint, annex, global, dashboard, prompts o client intelligence debería revisar explícitamente:

1. ¿Introduce una nueva fuente de verdad?
2. ¿Duplica un cálculo ya existente?
3. ¿Añade defaults silenciosos?
4. ¿Redondea demasiado pronto?
5. ¿Cambia la semántica de score/banda/target/color?
6. ¿Puede afectar al tono cliente-facing?
7. ¿Queda cubierto por tests?

Regla: el review debe vigilar coherencia, no solo estilo o lint.

### 6. Prohibir degradaciones silenciosas en zonas críticas

En componentes críticos no deberían aceptarse patrones como:

- `except Exception: pass`;
- fallbacks implícitos sin trazabilidad;
- hardcodes de severidad, banda, prioridad o target;
- y mezclas no documentadas de múltiples payloads.

Regla: si el sistema no puede resolver una semántica crítica con garantías, debe fallar de forma explícita o dejar una señal auditable.

### 7. Separar claramente dominios de salida

Debe quedar institucionalizado que existen al menos tres dominios distintos:

- cliente-facing;
- técnico interno;
- comercial interno.

Cada uno puede tener distinto tono, pero todos deben consumir la misma base semántica de score y target.

Regla: el tono puede variar, la verdad del dato no.

### 8. Documentación viva y canónica

El documento `docs/operations/assessment-coherence-remediation.md` debe ser solo el punto de arranque. Después de la corrección conviene derivar de aquí:

- una guía canónica de semántica de madurez;
- una política de target maturity;
- y una checklist operativa de validación de entregables.

Regla: cuando la solución ya esté implementada, la documentación debe pasar de “diagnóstico de remediation” a “norma de operación”.

### 9. Ownership claro

Tiene que existir ownership explícito sobre:

- scoring y contratos de madurez;
- target policy;
- render cliente-facing;
- global consolidation;
- y governance documental.

Regla: si nadie es dueño de la semántica, la semántica se degrada.

### 10. Validación de cambios sobre artefactos reales antes de dar por buena una PR

Cada cambio relevante debería revisarse no solo en tests unitarios sino también sobre uno o más casos completos regenerados, comprobando:

- payloads;
- DOCX;
- dashboard;
- y alineación narrativa.

Regla: no cerrar cambios solo porque “pasan tests” si alteran artefactos ejecutivos.

## Mecanismos concretos de prevención recomendados

Para que esto sea sostenible, la combinación mínima recomendable es:

1. **Helper único** para score/banda/color/lectura.
2. **Política explícita** de target maturity con justificación persistida.
3. **Tests transversales** en CI.
4. **Golden cases** de referencia.
5. **Checklist de PR** específica de coherencia.
6. **Prohibición de fallbacks silenciosos** en zonas críticas.
7. **Revisión manual corta de artefactos finales** en cambios sensibles.

## Seguridad y observabilidad de grado enterprise

La refactorización no debe mejorar solo la coherencia funcional. También debe dejar una base de operación y gobierno con estándares enterprise en seguridad y observabilidad.

### 1. Seguridad de datos y artefactos

Hay que revisar:

- qué información sensible puede acabar en payloads, DOCX, HTML o logs;
- si existen datos de cliente, claims, prompts o contextos que no deberían persistirse completos;
- y si los artefactos generados exponen más información de la necesaria.

Objetivo:

- minimizar exposición de datos;
- separar claramente artefactos cliente-facing e internos;
- y evitar filtrado accidental de contexto sensible en outputs o ficheros intermedios.

### 2. Trazabilidad de decisiones semánticas

Toda decisión crítica debería ser auditable:

- cómo se calculó score;
- cómo se resolvió banda;
- cómo se derivó target maturity;
- qué señales justificaron claims regulatorios;
- y qué políticas se aplicaron en cada etapa.

Objetivo:

- permitir auditoría técnica;
- explicar resultados internamente;
- y detectar cambios no deseados tras una modificación de código o prompts.

### 3. Logging estructurado y orientado a diagnóstico

La pipeline debería dejar trazas suficientes para entender:

- qué inputs usó cada etapa;
- qué defaults o políticas aplicó;
- qué fallbacks se activaron;
- y qué diferencias hubo entre score, target y narrativa.

Objetivo:

- evitar cajas negras;
- acelerar troubleshooting;
- y hacer visible cualquier degradación semántica.

### 4. Observabilidad de pipeline end-to-end

Conviene tener visibilidad operacional sobre:

- duración por etapa;
- fallos por módulo;
- tasa de regeneraciones fallidas;
- desalineaciones detectadas por tests;
- y calidad de artefactos generados.

Objetivo:

- detectar regresiones pronto;
- medir estabilidad;
- y saber dónde se rompe la cadena cuando un artefacto sale mal.

### 5. Señales de calidad ejecutiva

No basta con saber que el script terminó. También hay que observar:

- si hubo incoherencia entre score y banda;
- si el target quedó demasiado cerca o demasiado lejos;
- si el tono disparó reglas de severidad no esperadas;
- y si el render consumió fuentes incompatibles.

Objetivo:

- tener alertas funcionales de calidad, no solo métricas técnicas de éxito/error.

### 6. Gestión explícita de errores y degradaciones

En zonas críticas no debería haber degradación silenciosa.

Debe distinguirse entre:

- error bloqueante;
- fallback controlado;
- semántica incompleta;
- y artefacto no apto para cliente.

Objetivo:

- que el sistema no produzca outputs aparentemente válidos cuando la semántica crítica quedó comprometida.

### 7. Separación de dominios y privilegios

Hace falta revisar la frontera entre:

- assets cliente-facing;
- documentación interna;
- outputs comerciales;
- prompts;
- y dossiers de inteligencia.

Objetivo:

- asegurar que cada tipo de artefacto solo accede a la información que necesita;
- y reducir contaminación entre dominios con sensibilidades distintas.

### 8. Checklist enterprise mínimo a implantar

Después de la corrección, debería existir como mínimo:

1. logging estructurado por etapa;
2. trazabilidad de políticas aplicadas;
3. clasificación clara de artefactos internos vs cliente-facing;
4. validaciones automáticas de coherencia semántica;
5. reglas de fallo explícito en vez de degradación silenciosa;
6. y revisión de exposición de datos en payloads, renders y bundles.

## Señal de que la solución está bien gobernada

Se podrá considerar que la calidad queda protegida cuando:

- modificar un render no pueda cambiar score o banda;
- modificar un prompt no pueda romper la semántica base;
- modificar `client_intelligence` no pueda degradar target sin trazabilidad;
- y cualquier incoherencia vuelva a detectarse automáticamente antes de llegar a cliente.

## Criterio de aceptación sistémico

La corrección no se considerará resuelta si únicamente mejora `vodafone_demo`.

Debe quedar resuelto el comportamiento general de la pipeline para que:

- cualquier torre futura consuma la misma semántica de madurez;
- cualquier cliente futuro renderice entregables coherentes entre sí;
- y ninguna capa posterior vuelva a reinterpretar score, banda o target por su cuenta.

## Resultado esperado tras la corrección

El sistema debe producir un conjunto de entregables donde:

- el score es único y trazable;
- la banda cualitativa coincide en todas las capas;
- el target es creíble y narrativamente consistente;
- el tono es proporcional a la evidencia;
- y todos los artefactos cuentan la misma historia con distinto nivel de detalle, no historias distintas.

Ese resultado debe cumplirse en `vodafone_demo` como prueba inmediata, pero la solución válida es la que también queda preparada para cualquier caso futuro.
o.
