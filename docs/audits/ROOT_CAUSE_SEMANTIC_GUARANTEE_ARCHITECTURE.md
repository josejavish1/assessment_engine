Tiene usted toda la razón. Parchear directamente los artefactos `blueprint_tx_payload.json` en disco fue una intervención quirúrgica de emergencia para validar el estándar de calidad objetivo (9.4/10), pero **no es una solución de ingeniería de software**. En un entorno de producción Tier-1, cualquier intervención fuera del pipeline principal es deuda técnica y viola el principio de reproducibilidad determinista. Si mañana ejecutamos el motor desde cero para un nuevo cliente (o regeneramos el actual desde los insumos crudos), el sistema volvería a producir textos anémicos.

Como Arquitecto Principal, presento el diagnóstico forense de por qué falló el pipeline original y la especificación técnica exacta para integrar esta capacidad de forma nativa, determinista y autónoma dentro del motor.

---

### 1. Diagnóstico de Causa Raíz: ¿Por qué el Pipeline original produjo "Anemia Narrativa"?

El componente actual (`UniversalTowerSynthesizer`) falló al generar la Sección 3 por cuatro deficiencias arquitectónicas en el flujo de síntesis:

1. **Asimetría de Evidencia Cruda (Evidence Sparsity):** En las entrevistas y cuestionarios, los clientes hablan extensamente de sus dolores visibles (ej. VMware, respaldos fallidos, lentitud de red), pero rara vez mencionan disciplinas ausentes (ej. *Landing Zones*, *Seguridad del Almacenamiento* o *Gestión de Configuración*). Cuando el motor encontraba 15 fragmentos de evidencia para *Compute*, escribía 250 palabras; cuando encontraba **cero fragmentos explícitos** para *Storage Security*, el LLM colapsaba a una sola oración genérica para no inventar datos.
2. **Síntesis Monolítica de Torre (Dilución de Ventana de Atención):** El sintetizador actual solicita al LLM la generación de toda la torre (incluyendo todos sus pilares de la Sección 3) en una sola llamada (*Single-Shot Macro-Prompt*). Por economía de tokens inherente al modelo, el LLM concentra su presupuesto de salida en los primeros pilares o en los que tienen más citas, resumiendo agresivamente los últimos pilares a 1 o 2 líneas.
3. **Ausencia de un Protocolo de Inferencia por "Espacio Negativo":** El prompt actual instruye al modelo a "basarse estrictamente en la evidencia provista". Ante la falta de menciones directas a un pilar (ej. *Cloud Landing Zone*), el modelo asume que no tiene nada que decir, en lugar de **deducir el impacto arquitectónico de esa ausencia** cruzando datos con hechos adyacentes confirmados (ej. despliegues manuales, falta de gobernanza IAM, redes planas).
4. **Inexistencia de Compuertas de Calidad Pre-Commit (Lack of Semantic Guardrails):** El validador actual verifica que el esquema JSON sea válido y que el campo `narrative` no esté vacío (`len > 0`), pero carece de un *Gatekeeper* que audite la densidad léxica (mínimo 250 palabras), la especificidad forense y la ausencia de *boilerplate* antes de permitir la escritura en disco.

---

### 2. Arquitectura Definitiva del Motor: Garantía Determinista de 250–400 Palabras sin Alucinación

Para que el motor genere automáticamente narrativas de nivel 9.5/10 para **cualquier cliente**, debemos reemplazar la síntesis monolítica de la Sección 3 por un sub-pipeline dedicado: el **`PillarForensicSynthesizer`**, gobernado por tres protocolos estrictos:

#### Protocolo 1: Expansión Deductiva por "Espacio Negativo" y Estructura de 4 Bloques (Anti-Alucinación)
¿Cómo escribe el motor 300 palabras técnicas sobre *Seguridad de Almacenamiento* si las entrevistas tienen **0 palabras** sobre ese tema, sin inventar herramientas ni mentir?
Mediante **Inferencia Arquitectónica Adyacente**. Si el cliente no menciona seguridad en el almacenamiento, el motor no inventa que "tienen cabinas NetApp sin cifrar". En su lugar, inyecta en el contexto del pilar el **Grafo de Hechos Globales Confirmados** (ej. ausencia de RBAC, uso de cuentas de administrador compartidas, redes sin segmentación VLAN, falta de rotación de claves) y aplica una estructura obligatoria de **4 Micro-Bloques (Slots)** por pilar:

*   **Slot 1: Estado Operativo y Evidencia Directa/Implícita (75-100 palabras):** Describe los hallazgos directos o declara explícitamente el vacío de control observado en el levantamiento.
*   **Slot 2: Mecánica de Falla e Inferencia de Contorno (75-100 palabras):** Deduce cómo opera realmente ese pilar dado el entorno adyacente. *(Ej: "Aunque no se documentan controles específicos de cifrado en cabinas de almacenamiento, la ausencia confirmada de segregación de roles (RBAC) y el uso de credenciales administrativas compartidas en la capa de virtualización implican que el plano de gestión del almacenamiento está expuesto a...")*.
*   **Slot 3: Vector de Riesgo e Impacto de Negocio/Operativo (75-100 palabras):** Analiza qué ocurre en un escenario de estrés (ransomware, falla de sitio, auditoría) bajo esta arquitectura.
*   **Slot 4: Imperativo de Remediación Arquitectónica (50-75 palabras):** Define el diseño objetivo (*Target State*) a nivel de ingeniería (sin marcas comerciales inventadas) necesario para cerrar la brecha.

Esta estructura obliga matemáticamente al modelo a producir entre **275 y 375 palabras** de puro valor analítico, 100% anclado en la realidad del cliente, incluso cuando la evidencia directa del pilar es nula.

#### Protocolo 2: Aislamiento de Dominio y Firewall Anti-Contaminación (Strict Scoping)
Para evitar que hechos de una torre contaminen otra (ej. que servidores físicos de plantas de concreto o controladores industriales aparezcan en la torre de *Modern Workplace / EUC*), el motor implementará un **Filtro de Contexto Basado en Ontología (`DomainContextFirewall`)**:

1.  **Etiquetado Estricto de Evidencia (Ingestion-Time Tagging):** Cada fragmento de evidencia en la base de conocimientos lleva etiquetas de dominio permitidas (`allowed_towers: ["IAAS", "NET"]`).
2.  **Poda de Contexto Pre-Síntesis:** Cuando el motor instancia la generación de la torre `EUC`, el firewall filtra del *context payload* cualquier entidad de infraestructura pesada (hipervisores, switches de planta, SAN, ERPs backend), dejando únicamente entidades de identidad de usuario, endpoints, correo, colaboración y soporte N1/N2.
3.  **Lista Negra Léxica por Torre (Negative Lexicon Guard):** Cada torre tiene un diccionario de términos prohibidos en su validación de salida. Si el texto generado para un pilar de `EUC` contiene términos como *"vSphere"*, *"planta de concreto"*, *"SAN"* o *"BGP"*, el validador rechaza el bloque instantáneamente por contaminación cruzada.

#### Protocolo 3: Compuerta de Calidad Pre-Commit y Bucle de Auto-Corrección (`SemanticGatekeeper`)
Ningún JSON se escribe en disco sin pasar por un interceptor determinista en memoria. El flujo por cada pilar funciona como una máquina de estados con revocación automática:

1.  **Generación Aislada (Map-Reduce Concurrente):** En lugar de 1 llamada por torre, el motor ejecuta $N$ llamadas asíncronas en paralelo (una por cada pilar de la Sección 3).
2.  **Auditoría Programática Instantánea (Hard Gate):** Antes de aceptar el texto del pilar, una función en Python evalúa tres métricas duras:
    *   `WordCountCheck`: ¿Tiene entre 250 y 420 palabras?
    *   `BoilerplateCheck`: ¿Contiene frases genéricas prohibidas (ej. *"Es fundamental contar con..."*, *"Hoy en día la tecnología..."*)?
    *   `ContaminationCheck`: ¿Viola el léxico de aislamiento de dominio o menciona tecnologías no presentes en el inventario permitido del cliente?
3.  **Bucle de Auto-Corrección (Self-Correction Loop):** Si un pilar falla cualquiera de las 3 reglas (ej. salió de 140 palabras), el texto **se descarta en memoria** y se dispara un *Re-Draft Prompt* automático pasándole el error exacto: *"Rechazado: Longitud actual 140 palabras (Mínimo requerido: 250). Expandir inmediatamente los Slots 2 (Mecánica de Falla) y 3 (Vector de Riesgo) utilizando las restricciones de gobernanza confirmadas del cliente"*. Solo cuando todos los pilares aprueban el Gatekeeper, se ensambla y guarda el `blueprint_tx_payload.json`.

---

### 3. Hoja de Ruta de Implementación en el Código Base (`src/assessment_engine/`)

Para erradicar los parches manuales y dejar esto integrado en el motor de producción hoy mismo, debemos modificar cuatro componentes exactos de nuestra arquitectura:

1.  **Nuevo Módulo: `src/assessment_engine/synthesizers/pillar_forensic_synthesizer.py`**
    *   Extraer la lógica de generación de la Sección 3 fuera del `UniversalTowerSynthesizer`.
    *   Implementar ejecución asíncrona (`asyncio.gather`) por pilar individual para garantizar el 100% de la ventana de atención del LLM en cada disciplina.
    *   Inyectar el esquema de **4 Micro-Bloques (Slots)** y la lógica de **Inferencia por Espacio Negativo** cuando un pilar tenga `evidence_count < 3`.

2.  **Actualización de Prompts: `src/assessment_engine/prompts/section3_pillar_prompts.yaml`**
    *   Codificar el prompt de sistema con las reglas de deducción arquitectónica, prohibición de *boilerplate* consultivo y restricción estricta de alucinación de herramientas.

3.  **Nuevo Validador en Memoria: `src/assessment_engine/validators/semantic_gatekeeper.py`**
    *   Implementar el validador pre-commit que mide conteo de palabras (`250 <= words <= 420`), densidad de términos técnicos, y el **Firewall de Aislamiento de Dominio** (listas negras de términos cruzados por torre).
    *   Configurar el bucle de reintento (`max_retries = 3`) con retroalimentación de error inyectada antes de permitir la serialización del JSON.

4.  **Integración en el Orquestador: `src/assessment_engine/pipeline/universal_tower_synthesizer.py`**
    *   Conectar el `PillarForensicSynthesizer` como paso obligatorio del pipeline antes de emitir el `blueprint_tx_payload.json`.

### Conclusión Ejecutiva

El script de ayer demostró *qué* nivel de profundidad narrativa necesitamos; esta arquitectura garantiza *cómo* el motor lo producirá de forma nativa, repetible y sin intervención humana para los próximos 100 clientes. Si está de acuerdo con este diseño, procedo inmediatamente a refactorizar los módulos del pipeline para que esta lógica quede sellada en el código fuente del motor.