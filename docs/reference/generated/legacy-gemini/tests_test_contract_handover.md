# Documentación: `tests/test_contract_handover.py`

## Resumen

Este módulo de tests está diseñado para validar los "contratos de datos" y los puntos de "traspaso" (handover) entre las principales etapas del pipeline. Su foco no está en la lógica interna de los scripts, sino en asegurar que la **salida de una etapa es una entrada válida para la siguiente**. Esto es fundamental para mantener la integridad de la arquitectura "Top-Down" y evitar inconsistencias entre los diferentes artefactos generados.

## Tests Principales

Cada test se centra en un punto de intercambio de datos (un "contrato") específico en el flujo de trabajo.

### `test_contract_blueprint_to_annex()`

-   **Propósito:** Asegura que el `blueprint_t5_payload.json` (la salida del motor de blueprint) es un contrato válido que puede ser consumido por el siguiente paso, el sintetizador del anexo.
-   **Método:** Carga el fichero "golden" del blueprint, lo valida contra su esquema `BlueprintPayload` y realiza comprobaciones básicas para simular cómo lo leería el sintetizador.

### `test_contract_annex_is_valid_payload()`

-   **Propósito:** Garantiza que el `approved_annex_t5.template_payload.json` (la salida del sintetizador) cumple estrictamente con el esquema `AnnexPayload`.
-   **Método:** Carga el fichero "golden" del anexo y lo valida contra su esquema, asegurando que tiene la estructura que el renderizador de Word espera.

### `test_contract_global_report_schema()`

-   **Propósito:** Es un test estructural para validar que el esquema `GlobalReportPayload` es coherente y utilizable.
-   **Método:** Como no existe un fichero "golden" de informe global, este test construye un diccionario de datos simulado (`mock`) con la estructura mínima requerida y lo valida contra el esquema `GlobalReportPayload`. Esto demuestra que el contrato está bien definido.

### `test_contract_commercial_hybrid_lineage()`

-   **Propósito:** Valida el "Contrato Híbrido" del Plan Comercial, una de las características clave de la arquitectura. Asegura que el `CommercialPayload` puede contener datos que provienen tanto del informe global (estratégico) como de los blueprints (tácticos).
-   **Método:** Construye un `CommercialPayload` simulado que incluye metadatos de linaje híbrido y un `intelligence_dossier` que referencia a los blueprints fuente. Al validarlo contra el esquema, prueba que el contrato soporta esta fusión de datos.

## Rol en el Proyecto

Este fichero de tests actúa como el **Guardián de la Integridad del Pipeline**.

-   **Aplicación de la Arquitectura:** Es la implementación automatizada que fuerza el cumplimiento de los principios "Top-Down" y "Contract-First".
-   **Prevención de Regresiones:** Evita que los cambios en un script (por ejemplo, en el motor del blueprint) rompan de forma silenciosa un script posterior (como el renderizador del anexo). Actúa como una red de seguridad contra la "deriva de datos" entre etapas.
-   **Facilita la Refactorización:** Permite a los desarrolladores (o a una IA) modificar un script con la confianza de que, mientras estos tests sigan pasando, no se ha roto la compatibilidad con el resto del sistema.
-   **Documentación Viva:** Los propios tests sirven como una forma de documentación, mostrando claramente qué artefactos de datos se pasan entre qué etapas del proceso.
