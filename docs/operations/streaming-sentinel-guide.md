---
status: Verified
owner: docs-governance
source_of_truth:
- ../../docs/documentation-map.yaml
- ../../src/assessment_engine/infrastructure/streaming_sentinel.py
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: how_to
verification_mode: editorial
---
# Guía de Operación: Streaming Sentinel (On-Demand Mode)

Este documento detalla el diseño, la arquitectura y los comandos de operación del **Streaming Sentinel**, el motor de ingesta de evidencias en tiempo real del *Assessment Engine*. 

Para prevenir el riesgo de **agotamiento de cuotas y consumo excesivo de tokens de Vertex AI**, el sistema ha sido configurado para operar de forma estrictamente **Bajo Demanda (On-Demand)**. El daemon automático de segundo plano está desactivado por defecto, dándote a ti el control absoluto de la llave presupuestaria.

---

## 1. Arquitectura "Dual-Tier" (Zero-Lockin)

El sistema separa el flujo de información en dos capas de almacenamiento:
1.  **Capa "Hot" (Bajo Demanda - SQLite WAL):** Las evidencias entrantes se inyectan en un búfer local ultrarrápido y seguro (`working/redeia_v3/streaming_queue.db`) configurado en modo **WAL (Write-Ahead Logging)**. El coste financiero de esta capa es **0.00€** y consume recursos mínimos de disco local.
2.  **Capa "Cold" (La Bóveda RAG y el Grafo Bayesiano):** Al activar la sincronización, las evidencias pendientes de la capa "Hot" se procesan, se eliminan duplicados y se vuelcan a la base RAG de forma incremental, recalculando las metas de madurez del cliente.

---

## 2. Los Cuatro "Escudos" de Ciberseguridad y Protección Financiera

Para garantizar que el sistema nunca colapse bajo ataques de red (OOM/Path Traversal) ni consuma tokens innecesarios de Vertex AI, el Sentinel implementa cuatro filtros automáticos en la CPU antes de proceder a la ingesta:

```
                            [ NUEVA EVIDENCIA ENTRANTE ]
                                         │
                                         ▼
                 [ ESCUDO 1: Límite OOM de Payload Pydantic ] ──► (Excede 5MB) ──► [ HTTP 422 REJECT ]
                                         │
                                         ▼
                 [ ESCUDO 2: Hash Sintáctico SHA-256 ] ──► (Duplicado) ──► [ DESCARTE (0 Tokens) ]
                                         │
                                         ▼
                 [ ESCUDO 3: Filtro Semántico Jaccard ] ──► (Overlap > 75%) ──► [ DESCARTE (0 Tokens) ]
                                         │
                                         ▼
                 [ ESCUDO 4: Programador Amortiguado ] ──► (Espera silencio) ──► [ PROCESADO SEGURO ]
```

*   **Escudo 1 (Anti-OOM Payload Guardrail):** Los esquemas de Pydantic bloquean de forma tajante `content` > 5MB y `source_url` > 2048 caracteres, previniendo inyecciones de *Out-Of-Memory* que tumbarían el servidor.
*   **Escudo 2 (SHA-256 Hashing):** Si entra un documento con el mismo contenido sintáctico exacto, se bloquea y se ignora al instante.
*   **Escudo 3 (Semantic Jaccard Filter):** Si un documento está ligeramente reescrito pero comparte más del **$75\%$** de sus tokens con fragmentos existentes, el motor lo clasifica como duplicado semántico y lo descarta de inmediato.
*   **Escudo 4 (Dampened Batching Scheduler):** El motor acumula peticiones y solo reconstruye el árbol RAG de forma asíncrona (con `asyncio.run()`) en un hilo de fondo cuando se acumula un lote de 5 elementos nuevos o tras 10 segundos de silencio, protegiendo tu API key.
*   *(Extra) Defense-in-Depth:* Una validación estricta de rutas (`is_relative_to`) evita ataques de **Local File Inclusion (Path Traversal)**, garantizando que el streaming jamás sobrescriba archivos fuera del directorio sandbox del cliente.

---

## 3. Resiliencia de Nivel Principal (Concurrencia Multi-Worker y Hardware)

El Sentinel está diseñado para resistir las peores condiciones de hardware y despliegues en red:

1.  **Distributed OS Mutex (Multi-Worker Safe):** En despliegues con Gunicorn o múltiples workers de Uvicorn, el Sentinel implementa un candado atómico de sistema de archivos (`.sentinel_lock`) basado en la creación de directorios. Garantiza que solo un worker escriba en el archivo RAG `evidence_vault.json` a la vez. Las colisiones en SQLite están prevenidas mediante `threading.Lock()` y `cursor.rowcount`.
2.  **I/O Atómico POSIX:** Todo archivo físico (incluyendo `evidence_vault.json` y los chunks de streaming) se escribe primero en un archivo `.tmp` efímero. Solo cuando el *flush* en disco es exitoso, se ejecuta un reemplazo atómico a nivel de sistema operativo (`os.replace()`), erradicando la posibilidad de que un corte de luz repentino corrompa la base de datos (Power-Loss Corruption).
3.  **Saneamiento a Largo Plazo (WAL Bloat):** El daemon aplica explícitamente `contextlib.closing` a los cursores para evitar fugas de memoria, y lanza operaciones `PRAGMA wal_checkpoint(PASSIVE)` durante periodos inactivos, truncando el archivo de transacciones SQLite `.db-wal` para evitar que el disco se llene tras meses de ejecución 24/7.
4.  **Integración de Ciclo de Vida FastAPI:** El loop del daemon asíncrono está directamente atado al evento de `lifespan` (Context Manager) de FastAPI. Se inicia y detiene con gracia a la vez que el servidor web.

---

## 4. Manual de Operación y Comandos

### Paso 1: Alimentar la Cola de Ingesta (Modo Pasivo - Gratis)
Puedes seguir enviando noticias, alertas regulatorias de NIS2 o informes de Redeia a la cola local en cualquier momento. Puedes hacerlo mediante el script Python desde tu consola:

```python
from assessment_engine.infrastructure.streaming_sentinel import StreamingSentinel

sentinel = StreamingSentinel(client_id="redeia_v3")
sentinel.enqueue_evidence(
    source_url="https://www.boe.es/directiva-nis2-cambios",
    content="Contenido o texto de la evidencia regulatoria que deseas inyectar de forma pasiva..."
)
```

### Paso 2: Ejecutar la Sincronización (Bajo Demanda - Tú controlas la API)
Cuando desees incorporar todas las evidencias acumuladas, actualizar tu RAG, recalcular la Red Bayesiana cíclica y obtener los nuevos reportes consolidados con sus Single Points of Failure (SPOF) basados en PageRank, simplemente ejecuta la sincronización manual:

```bash
# Sincroniza e indexa en un solo bloque rápido y controlado todas las evidencias pendientes
.venv/bin/python -m assessment_engine.application.tools.sync_sentinel
```

*(Nota: Crearemos esta utilidad JIT de sincronización rápida a continuación).*

### Paso 3: Lanzar la Auto-Calibración Causal (Backpropagation)
Si detectas que la madurez real auditada del cliente difiere de tus metas teóricas, puedes ejecutar el algoritmo de auto-aprendizaje por descenso de gradiente para que el grafo "aprenda" y corrija de forma autónoma los pesos de `epistemic_dependencies.json`:

```python
from assessment_engine.infrastructure.epistemic_graph_service import EpistemicGraphService

service = EpistemicGraphService(industry_profile="critical_infrastructure")
# Compara targets con auditorías y actualiza el JSON de políticas al vuelo reduciendo el error MSE
report = service.backpropagate_audit_feedback(intrinsic_maturities, audited_maturities, lr=0.05)
print("MSE de la Red Bayesiana optimizado a:", report["epoch_mse"])
```

---

## 4. Recuperación de Emergencia (Rollback)

Si por cualquier motivo el nuevo análisis de riesgos de la Red Bayesiana o del RAG no te convence, o si deseas restaurar tu copia de seguridad limpia original que dejamos guardada a un lado:

```bash
# Comando de un solo paso para borrar la ejecución actual y restaurar tu backup intacto
rm -rf working/redeia_v3 && cp -r working/redeia_v3_backup working/redeia_v3
```
Esto dejará tu entorno de trabajo exactamente como estaba antes de iniciar cualquier prueba de relanzamiento.
