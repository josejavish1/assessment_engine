---
status: Verified
owner: docs-governance
source_of_truth:
- docs/ai/documentation-governance.md
- docs/README.md
- docs/documentation-map.yaml
- docs/operations/agentic-development-workflow.md
- docs/operations/engineering-quality-gates.md
last_verified_against: 2026-06-26
applies_to:
- ai-agents
doc_type: operational
diataxis: how_to
verification_mode: editorial
---
# AGENTS

Este fichero es la **puerta de entrada corta para cualquier agente de IA** que trabaje en `assessment-engine`.

## Lee en este orden

1. [`README.md`](README.md)
2. [`docs/README.md`](docs/README.md)
3. [`docs/ai/documentation-governance.md`](docs/ai/documentation-governance.md)
4. [`docs/operations/agentic-development-workflow.md`](docs/operations/agentic-development-workflow.md) si vas a trabajar con cambios asistidos por IA
5. [`docs/operations/engineering-quality-gates.md`](docs/operations/engineering-quality-gates.md) si vas a tocar código o tests
6. el documento canónico más cercano al cambio que vayas a hacer

## Reglas mínimas

- no trates este archivo como fuente de verdad del proyecto;
- no introduzcas aquí arquitectura, contratos ni operación detallada;
- usa el código, tests, schemas y workflows como verdad primaria;
- no implementes sobre una instrucción vaga: explicita problema, alcance, fuente de verdad e invariantes;
- materializa reglas importantes en código, tests, schemas o workflows, no solo en prompts;
- actualiza `docs/documentation-map.yaml` si cambia el estado o el destino de un documento;
- si una afirmación no puede verificarse, márcala como `Needs Review` en vez de inventarla;
- **GOLDEN PATHS (Estricto):** Nunca crees un archivo desde cero para un nuevo servicio, worker o endpoint. DEBES usar las plantillas ubicadas en `templates/golden_paths/` como base y rellenar únicamente la lógica de negocio. No alteres la estructura de logging ni las validaciones base de la plantilla. Si el archivo que estás creando es un simple modelo Pydantic, un DTO o un helper puro sin estado, puedes usar un archivo en blanco pero DEBES incluir el comentario `# golden-path: ignore` en la cabecera para que el Validador de Arquitectura lo permita.

## Leyes de Ingeniería No Negociables (Zero-Tolerance Rules)

Todo agente (Gemini, ChatGPT, Cursor o Copilot) debe someterse a estas leyes soberanas del repositorio:

1. **La Tiranía del Protocolo (Anti-Complacencia):** La calidad técnica es superior a la velocidad. Queda estrictamente prohibido forzar pases de CI/CD, ignorar advertencias, deshabilitar pruebas automáticas o forzar merges eludiendo las barreras de protección de rama.
2. **Cero Parches (Zero Workarounds):** Ante cualquier fallo o error en tiempo de ejecución, de tipado o de linter, es obligatorio investigar la causa raíz y aplicar una solución definitiva y estructuralmente correcta. Nunca silencies warnings ni captures excepciones de manera genérica sin resolver la causa.
3. **Arquitectura de Entropía Cero (Zero-Entropy):** No se permite dejar archivos comprimidos (`.zip`), duplicados de respaldo, scripts de prueba sueltos en la raíz ni directorios vacíos. Git es la única máquina del tiempo. Toda la base de código debe ser limpia y simétrica.
4. **Idioma Único (Inglés Técnico):** Absolutamente todos los comentarios en línea de código, firmas de funciones, descripciones de campos Pydantic y docstrings de clases/métodos deben redactarse exclusivamente en un inglés técnico formal, preciso y aséptico.
5. **Verificación Empírica Obligatoria:** Nunca asumas el éxito de un cambio basándote únicamente en que el compilador no arrojó errores. Es obligatorio ejecutar la suite de pruebas unitarias (`pytest`) y comprobar empíricamente los resultados de ejecución antes de dar la tarea por concluida.

## Dónde escribir

- arquitectura: `docs/SYSTEM_ARCHITECTURE.md` o futura `docs/architecture/`
- contratos: `docs/contracts/`
- workflow con agentes: `docs/operations/agentic-development-workflow.md`
- orquestador product owner: `docs/operations/product-owner-orchestrator.md`
- calidad de implementación: `docs/operations/engineering-quality-gates.md`
- política documental: `docs/ai/documentation-governance.md`
- índice y estado: `docs/README.md` y `docs/documentation-map.yaml`

Los archivos específicos por agente, como `GEMINI.md`, `CHATGPT.md` o `.github/copilot-instructions.md`, solo adaptan esta misma base común.

---

## Checklist de Disciplina de Cambio para Agentes IA

Todo agente de IA (o desarrollador) que intervenga en el pipeline del Assessment Engine DEBE seguir estas reglas de seguridad operativa antes de dar por completado un cambio:

### 1. El contrato es lo primero (Contract-First)
- [x] El esquema Pydantic (`intelligence.py`) define claramente la jerarquía Holding -> Filial.
- [x] Se han añadido los campos `technical_stack` y `field_metrics` como blindaje de información técnica.

### 2. No a la regresión silenciosa
- [x] El motor de Inteligencia V16.1 ha sido verificado mediante la "Prueba de Fuego" desde cero.
- [x] Se ha verificado que marcas críticas como Siemens, ABB y Dynatrace no se diluyen (FidelitySentinel).
- [x] La atribución por sociedad (Reintel, Redinter, Red Eléctrica) es quirúrgica y veraz.

### 3. Si modificas MAPEOS O PAYLOADS
- [x] El payload resultante sigue el esquema ClientDossierV3.
- [x] Los tests de soberanía web (`zero-lockin-guard`) pasan en verde tras el saneamiento de seguridad.

### 4. Observabilidad y FinOps
- [x] El motor registra el consumo de tokens y el coste estimado en cada llamada a Vertex AI.
- [x] Los logs estructurados capturan la telemetría de los agentes.

### 5. Documentación
- [x] Se ha actualizado `docs/architecture/assessment_factory_flow.md` con los nuevos patrones de herencia y fidelidad atómica.
- [x] El validador de gobernanza de documentación ha certificado la integridad de los enlaces.

---

## Restricciones Negativas Explícitas (Anti-patterns)

Queda estrictamente prohibido que cualquier agente autónomo o desarrollador incurra en las siguientes prácticas:

1. **No escribirás pruebas de integración o de unidad que dependan de red externa:** Las pruebas que dependan de llamadas a APIs externas (como DuckDuckGo, Kroki o Google Grounding) deben aislarse como playgrounds en `tests/diagnostics/` bajo el prefijo `diag_*.py`, nunca incluirse en la suite automática de `pytest`.
2. **No silenciarás MyPy ni el linter mediante parches:** Prohibido el uso de `# type: ignore` o casts sintácticos (`Any`, `cast`) para silenciar errores de tipado sin una justificación de diseño comentada. Resuelve la causa raíz de forma tipada.
3. **No alterarás rutas mediante `sys.path` de forma manual:** Todas las importaciones de módulos deben resolverse mediante el namespace nativo absoluto (ej., `from assessment_engine.application...`). Nunca uses `sys.path.append` o `PYTHONPATH` locales.
4. **No dejarás código muerto comentado:** El código comentado en desuso debe ser eliminado físicamente de inmediato. Git es la única máquina del tiempo.

## Modos de Fallo Comunes y Autocuración (Troubleshooting)

Si la suite de pruebas o la ejecución fallan, sigue este protocolo de autocuración antes de solicitar intervención:

- **Error: `TemplateNotFound` (Jinja2):** Verifica que la plantilla existe físicamente bajo la carpeta `/templates/` de la raíz del repositorio y que la constante de ruta en `runtime_paths.py` apunta correctamente a ella.
- **Error: `TypeError: string indices must be integers`:** Ocurre si pasas traducciones en lugar de definiciones estructuradas de rango de madurez a la función de resolución. Asegura el mapeo del esquema.
- **Error: `ModuleNotFoundError` o `ImportError`:** Ocurre si el linter o el movimiento de carpetas dejó importaciones relativas obsoletas. Usa el espacio de nombres absoluto calificado `assessment_engine.application...` o `assessment_engine.infrastructure...`.
