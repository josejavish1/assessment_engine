---
status: Verified
owner: docs-governance
source_of_truth:
- docs/audits/AUDIT_RESULTS.md
- src/assessment_engine/application/cli.py
- src/assessment_engine/infrastructure/auditor/scanner.py
- src/assessment_engine/infrastructure/auditor/models.py
last_verified_against: '2026-06-26'
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: explanation
verification_mode: editorial
---
# Marco Operativo de Auditoría Unificada (Soverik Quality Engine)

Este documento describe la arquitectura, especificación de sondas, algoritmo de puntuación y artefactos generados por el comando de auditoría integral del proyecto:

```bash
python -m assessment_engine.application.cli audit
```

---

## 1. Propósito y Filosofía del Comando Unificado

Históricamente, la certificación del repositorio requería ejecutar múltiples herramientas aisladas (`pytest --cov`, `scripts/audit_neurosymbolic_codebase.py`, linters estáticos, scripts de mutación y análisis de grafos). 

El comando `cli audit` unifica **todas las dimensiones de calidad del código, seguridad, cobertura y arquitectura** en un único ejecutable sin fricción (`Single Pane of Glass`), diseñado para satisfacer las auditorías corporativas y procesos de Due Diligence de Nivel 1 (Tier-1 Enterprise Standards).

### Sintaxis y Opciones CLI:

```bash
python -m assessment_engine.application.cli audit [--target RUTA_PROYECTO] [--output-dir RUTA_SALIDA]
```

- `--target`: Directorio raíz a auditar (por defecto: raíz del workspace actual).
- `--output-dir`: Directorio donde se persisten los informes de salida (por defecto: `docs/audits`).

---

## 2. Ciclo de Vida de Ejecución

Cuando se invoca `python -m assessment_engine.application.cli audit`, el sistema ejecuta la siguiente secuencia determinista:

```
[CLI audit] ──> [SoverikQualityEngine.audit_project()]
                     ├── 1. Recorrido AST y detección segura de archivos (excluyendo .git, .venv, etc.)
                     ├── 2. Ejecución secuencial de las 21 sondas automatizadas
                     ├── 3. Ponderación matemática del score global (0.0% a 100.0%)
                     ├── 4. Asignación de Grado de Certificación (A+, A, B, C, F)
                     ├── 5. Generación y serialización de AUDIT_REPORT.json
                     ├── 6. Renderizado de AUDIT_CERTIFICATE.html (certificado interactivo)
                     └── 7. Sincronización con el informe maestro AUDIT_RESULTS.md
```

---

## 3. Catálogo de las 21 Sondas Automatizadas

El motor evalúa 21 sondas agrupadas en 6 dimensiones críticas:

| ID Sonda | Nombre / Dimensión | Peso | Estándar / Umbral Tier-1 | Descripción y Comportamiento |
| :--- | :--- | :---: | :--- | :--- |
| `security_sast` | Seguridad SAST & Secretos | 8% | CWE-798, OWASP Top 10 | Escaneo AST de inyecciones SQL/comandos y cálculo de entropía Shannon para cazar credenciales hardcodeadas. |
| `security_dast` | Dynamic Red Team DAST | 8% | OWASP DAST | Simulación de vectores de ataque dinámicos y comprobación de exposición de puertos o rutas no autorizadas. |
| `test_coverage` | Cobertura de Tests Productivos | 8% | Tier-1 Core >= 65.0% | Medición dinámica de líneas y ramas de código productivo activo (filtrando herramientas offline según `.coveragerc`). |
| `assertion_quality` | Calidad de Aserciones | 6% | Tier-1 Ratio >= 80.0% | Análisis AST sobre tests para exigir invariantes exactos (igualdad, esquemas Pydantic, magic bytes) frente a checks complacientes. |
| `mutation_gate` | Resistencia a Mutaciones | 8% | ISO/IEC/IEEE 29119 | Inyección sintáctica de mutantes (ROR, LCR, COR) en lógica viva para verificar que los tests fallan ante corrupciones de código. |
| `neurosymbolic_topology` | Topología AST & Código Muerto | 6% | Zero-Entropy Architecture | Construcción del grafo de importaciones NetworkX para clasificar núcleo canónico y detectar módulos huérfanos (blast radius = 0). |
| `ast_complexity` | Complejidad Ciclomática | 8% | ISO 25010 & Sonar S3776 | Inspección de ramas y anidamiento AST. Exige CC <= 10 (Zona Verde) en el 85%+ del código y 0 funciones Grado F en capa activa. |
| `code_hygiene` | Higiene de Excepciones | 2% | CWE-391 | Detección y erradicación de bloques `except Exception: pass` ciegos que enmascaren fallos silenciosos en producción. |
| `sre_observability` | Observabilidad y Logs | 5% | SRE OBS-001 | Prohibición estricta de `print()` en código productivo; verificación de logging estructurado con `logging.getLogger`. |
| `legal_compliance` | Cumplimiento Legal & IA | 5% | EU AI Act & Liability | Verificación de avisos de confidencialidad, límites de responsabilidad (liability caps) y exenciones de auditoría contable en Monte Carlo. |
| `supply_chain` | Seguridad Cadena de Suministro | 8% | NIST SP 800-218 | Generación de manifiesto SBOM CycloneDX (`docs/audits/SBOM_CYCLONEDX.json`) y verificación de dependencias sin vulnerabilidades críticas. |
| `performance_finops` | Rendimiento & FinOps | 4% | FinOps Foundation | Control de timeouts asíncronos y presupuestos de latencia en llamadas a APIs de razonamiento y renderizado de documentos. |
| `browser_accessibility` | Accesibilidad Web | 4% | WCAG 2.1 AA | Comprobación de semántica HTML en plantillas Jinja2 y portales interactivos (etiquetas alt, contrastes y roles ARIA). |
| `contract_drift` | Deriva de Contratos | 4% | Pydantic V2 Strict | Verificación de coincidencia exacta entre los contratos Pydantic del dominio y los payloads JSON persistidos en disco. |
| `resilience_chaos` | Resiliencia & Fallbacks | 4% | Chaos Engineering | Comprobación de existencia y activación determinista de fallbacks seguros cuando un servicio externo o LLM no responde. |
| `ai_safety_llm` | Seguridad en Prompts de IA | 4% | OWASP LLM01/02 | Verificación de encapsulamiento XML estricto y delimitadores de seguridad anti-inyección en todos los registros de prompts YAML. |
| `concurrency_stress` | Concurrencia y Thread Safety | 4% | Deterministic Concurrency | Verificación de generadores locales thread-safe de números pseudoaleatorios y semillas reproducibles en simulaciones FAIR. |
| `hardcoded_artifacts` | Aislamiento de Artefactos | 2% | Zero-Entropy Policy | Garantiza que no existen rutas absolutas locales ni clientes hardcodeados en el código fuente de producción. |
| `comment_quality` | Calidad de Comentarios | 2% | Clean Code Standards | Ratio de documentación técnica en docstrings y erradicación de emojis informales en comentarios de código productivo. |
| `documentation_quality` | Calidad Documental | 2% | Diátaxis Framework | Validación de metadatos frontmatter YAML, trazabilidad bidireccional y enlaces cruzados en el árbol `docs/`. |
| `structural_smells` | Olores Estructurales | 2% | Anti-Pattern Prevention | Detección de acoplamientos circulares, clases dios (God Objects) y violaciones de separación de capas en arquitectura limpia. |

---

## 4. Algoritmo de Calificación y Asignación de Grados

La puntuación global (`global_score`) es la media ponderada de las 21 sondas, acotada estrictamente entre 0.0% y 100.0%:

$$\text{Global Score} = \sum_{i=1}^{21} (\text{Score Sonda}_i \times \text{Peso}_i)$$

### Asignación de Grados Formales:

- **Grado A+ (Platinum):** `global_score >= 90.0%` y **el 100% de las sondas aprobadas** (`passed == True` en todas).
- **Grado A (Gold):** `global_score >= 80.0%` sin fallos críticos de seguridad (SAST y DAST aprobados).
- **Grado B (Silver):** `global_score >= 70.0%` sin fallos críticos de seguridad.
- **Grado C (Needs Improvement):** `global_score >= 50.0%`.
- **Grado F (Failed):** `global_score < 50.0%` o presencia de vulnerabilidades críticas de seguridad no subsanadas.

---

## 5. Artefactos Generados

Cada ejecución de `cli audit` actualiza de forma atómica y sincronizada los siguientes artefactos en `docs/audits/`:

1. **`AUDIT_REPORT.json`:** Expediente técnico serializado con todas las métricas, listas de hallazgos, severidades y recomendaciones para consumo de pipelines CI/CD o herramientas de gobernanza.
2. **`AUDIT_CERTIFICATE.html`:** Certificado ejecutivo con diseño formal responsive y modo oscuro, renderizado para directores de tecnología (CTOs) y auditores externos de Due Diligence.
3. **`AUDIT_RESULTS.md`:** Informe técnico consolidado en Markdown, alineado con el sistema de gobernanza documental del repositorio.
4. **`SBOM_CYCLONEDX.json`:** Manifiesto estándar CycloneDX de inventario de componentes y dependencias de la cadena de suministro.

---

## 6. Códigos de Salida para CI/CD

El comando devuelve códigos de salida deterministas para integración en pipelines de integración continua:

- **Código `0` (Success):** El proyecto obtiene Grado **A+**, **A** o **B**.
- **Código `1` (Failure):** El proyecto obtiene Grado **C** o **F**, bloqueando automáticamente el pase a producción en GitHub Actions.
