# PLAN DE REMEDIACIÓN ARQUITECTÓNICA TIER-1: ERRADICACIÓN DE HEURÍSTICAS LÉXICAS E IMPLEMENTACIÓN DE ENRUTAMIENTO NEUROSIMBÓLICO

**Documento:** `docs/architecture/NEUROSYMBOLIC_ROUTER_AND_KEYWORD_ERADICATION_PLAN.md`  
**Autor:** `gemini-4-argon` (Lead Systems Architect & Principal Engineer)  
**Estado:** MANDATO EJECUTIVO DE IMPLEMENTACIÓN INMEDIATA  
**Objetivo:** Erradicación total de listas de palabras clave (keywords) y expresiones regulares para clasificación de dominios, reemplazándolas por un Motor de Enrutamiento Semántico Neurosimbólico universal y agnóstico al idioma.

---

## 1. ANÁLISIS FORENSE DE LA CAUSA RAÍZ: EL "PECADO ORIGINAL" ARQUITECTÓNICO

El motor de evaluación actual sufre de una falla estructural crítica en su capa de ingesta y clasificación: intenta resolver un problema de **Comprensión de Jurisdicción Ontológica** utilizando **Coincidencia Léxica Superficial (Substring/Regex Matching)**. Se han detectado más de 48 instancias de arreglos estáticos (`trigger_keywords`, `_TOWER_KEYWORDS`, `_ABSENCE_PATTERNS`) distribuidos en el código base y archivos JSON.

### 1.1 Por qué falla la Generación 1 (Keywords y Regex)
El lenguaje técnico empresarial es altamente contextual y polisémico. Un motor basado en `if any(kw in text for kw in keywords)` carece de comprensión sintáctica, pragmática y de dominio:
*   **Colisión Polisémica:** La cadena `"UPS"` activa reglas de energía (Uninterruptible Power Supply - Torre 1), incluso cuando el hallazgo describe integraciones logísticas con el proveedor de paquetería *United Parcel Service* (Torre 6/Aplicaciones).
*   **Ceguera de Jurisdicción Contextual:** El hallazgo *"Los servidores locales de la planta de concreto sufren corrosión por polvo"* contiene la palabra `"servidores"`. El motor léxico lo envía ciegamente a **T1 (Data Center)**. Sin embargo, semánticamente, la jurisdicción raíz y el riesgo operativo pertenecen a **T10 (OT / Industrial Plant)** debido al entorno físico industrial y la naturaleza del activo.
*   **Inviabilidad Multilingüe y Mantenimiento $O(N \times M)$:** Soportar inglés, español, portugués y alemán requiere multiplicar manualmente miles de términos técnicos, modismos regionales y errores tipográficos comunes. Es una arquitectura frágil que colapsa ante cualquier cliente nuevo fuera del conjunto de datos de entrenamiento manual.

### 1.2 Por qué falla la Generación 2 (Embeddings Vectoriales Puros / Cosine Similarity)
Podría existir la tentación de reemplazar los keywords con búsqueda vectorial densa (ej. `text-embedding-3-large` + distancia coseno contra descripciones de torres). **Esto está estrictamente prohibido para esta capa.**
*   **Difuminación Semántica (Semantic Blur):** Los modelos de embeddings comprimen el significado en un espacio continuo donde la co-ocurrencia temática domina sobre la causalidad. Un párrafo que dice *"El equipo de Ciberseguridad (T4) bloqueó el puerto del firewall, impidiendo que la base de datos de SAP (T6) replique hacia AWS (T2)"* tendrá vectores cercanos a T4, T6 y T2 simultáneamente. La similitud coseno no puede razonar sobre **quién es el propietario raíz del defecto (Root Cause Owner)** frente a **quién sufre el síntoma (Downstream Impact)**.

### 1.3 El Estándar Tier-1 (Noviembre 2026): Enrutamiento Semántico Neurosimbólico
La única solución universal, determinista en su estructura y cognitiva en su evaluación, es una arquitectura **Neurosimbólica**:
1.  **Capa Simbólica (El Contrato Ontológico):** Definición formal, declarativa e inmutable de los límites jurisdiccionales de cada Torre Tecnológica (qué activos gobierna, qué procesos ejecuta y, crucialmente, **límites de exclusión explícitos**).
2.  **Capa Neuronal (Razonamiento con Decodificación Restringida):** Uso de un LLM de alta velocidad e inteligencia (ej. `gemini-2.5-flash` o superior configurado en el motor) forzado mediante **Structured Outputs (Pydantic Schema / Constrained Decoding)** a evaluar el hallazgo contra las reglas de exclusión ontológica, determinando la causa raíz antes de emitir el código de la torre.

---

## 2. DISEÑO ARQUITECTÓNICO TIER-1: EL ENRUTADOR NEUROSIMBÓLICO

La nueva arquitectura desacopla totalmente las reglas del negocio del código Python. El código ya no "sabe" qué es un servidor o una planta industrial; el código simplemente ejecuta un motor de inferencia contra una Ontología Formal.

### 2.1 El Contrato Ontológico (`engine_config/ontology_taxonomies.json`)
Se reemplazará `tower_classification_keywords.json` por un esquema ontológico rico. Cada torre no se define por palabras sueltas, sino por **Principios de Jurisdicción, Inclusiones Semánticas y Reglas de Desambiguación (Exclusiones)**.

Estructura requerida para `engine_config/ontology_taxonomies.json`:
```json
{
  "version": "2.0.0-NEUROSYMBOLIC",
  "routing_principles": [
    "ROOT_CAUSE_JURISDICTION: Clasifique según el dominio propietario de la falla raíz, no por el sistema que sufre el síntoma.",
    "PHYSICAL_ENVIRONMENT_OVERRIDE: Activos de cómputo estándar ubicados físicamente en entornos hostiles de manufactura, minas o plantas industriales pertenecen a OT (T10), no a Data Center (T1).",
    "POLYSEMY_RESOLUTION: Analice la función del acrónimo en la oración (ej. UPS como batería vs UPS como logística; SAP como ERP vs SAP como proceso)."
  ],
  "towers": {
    "T1": {
      "id": "T1",
      "name": "Data Center & Physical Infrastructure",
      "core_jurisdiction": "Instalaciones dedicadas de TI (Core/Edge Data Centers corporativos), energía eléctrica ininterrumpida (UPS, generadores), climatización de precisión (HVAC/CRAC), cableado estructurado de campus y cómputo físico empresarial (racks, blades, storage arrays).",
      "explicit_exclusions": [
        "NO incluye hardware ubicado en líneas de producción industrial, plantas de concreto, minas o controladores de piso de planta (eso es jurisdicción exclusiva de T10 - OT).",
        "NO incluye infraestructura IaaS/PaaS en la nube pública (eso es T2).",
        "NO incluye la empresa de logística y envíos 'UPS'."
      ]
    },
    "T10": {
      "id": "T10",
      "name": "Operational Technology (OT) & Industrial Systems",
      "core_jurisdiction": "Sistemas ciberfísicos industriales, SCADA, PLC, DCS, sensores de planta, redes industriales (Modbus, Profinet), e infraestructura de TI rugerizada o desplegada directamente en plantas de manufactura, sitios de mezcla, energía o logística pesada.",
      "explicit_exclusions": [
        "NO incluye sistemas ERP corporativos o planificación financiera (eso es T6), a menos que la falla sea en la interfaz física del piso de planta."
      ]
    }
  }
}
```
*(Nota para el agente implementador: Debe poblar las 10 torres T1 a T10 siguiendo exactamente este rigor ontológico).*

### 2.2 Modelos de Datos Estrictos (Pydantic Constrained Decoding)
El LLM no devolverá texto libre. Se forzará la salida a nivel de token mediante el siguiente contrato en `src/core/schemas/routing_schemas.py`:

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class TowerID(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"
    T5 = "T5"
    T6 = "T6"
    T7 = "T7"
    T8 = "T8"
    T9 = "T9"
    T10 = "T10"
    UNCLASSIFIED = "UNCLASSIFIED"

class AbsenceSemanticEvaluation(BaseModel):
    is_absence_of_control: bool = Field(
        description="True si el hallazgo describe la inexistencia, falta o carencia total de una herramienta, proceso o control necesario (ej. 'No cuentan con DRP', 'Carecen de monitoreo'). False si el control existe pero funciona mal."
    )
    missing_capability: Optional[str] = Field(
        default=None,
        description="Si is_absence_of_control es True, describe canónicamente en el idioma del hallazgo qué capacidad falta."
    )

class SemanticRoutingDecision(BaseModel):
    finding_id: str = Field(description="ID único del hallazgo evaluado.")
    chain_of_thought_jurisdiction: str = Field(
        description="Razonamiento conciso (1-2 oraciones) que explica quién tiene la jurisdicción de la causa raíz y cómo se aplicaron las reglas de exclusión ontológica."
    )
    primary_tower: TowerID = Field(
        description="La torre tecnológica propietaria de la causa raíz del hallazgo."
    )
    secondary_impacted_towers: List[TowerID] = Field(
        default_factory=list,
        description="Otras torres que sufren síntomas derivados de este hallazgo, sin ser dueñas de la causa raíz."
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Nivel de certeza semántica de la clasificación (0.0 a 1.0)."
    )
    absence_evaluation: AbsenceSemanticEvaluation = Field(
        description="Evaluación semántica de si el hallazgo representa una brecha por inexistencia (reemplaza el antiguo _ABSENCE_PATTERNS)."
    )

class BatchSemanticRoutingResponse(BaseModel):
    decisions: List[SemanticRoutingDecision]
```

### 2.3 El Servicio de Enrutamiento (`DomainSemanticRouter`)
Para evitar cuellos de botella de latencia y costos por llamadas individuales (N+1 LLM calls), el `DomainSemanticRouter` operará mediante **Micro-Batching Asíncrono Consciente del Contexto** (procesando lotes de 15 a 25 hallazgos por llamada estructurada) y contará con un **Caché Determinista por Hash Semántico (SHA-256)** para evitar re-evaluar textos idénticos en ejecuciones repetidas.

---

## 3. MANDATO DE ERRADICACIÓN (LISTA DE DEMOLICIÓN)

El agente de implementación tiene la orden estricta de **ELIMINAR O REFACTORIZAR COMPLETAMENTE** los siguientes artefactos y patrones. Ningún rastro de clasificación por subcadenas puede sobrevivir en producción:

1.  **Archivos de Configuración a Eliminar:**
    *   `engine_config/tower_classification_keywords.json` -> **ELIMINAR ARCHIVO.** Reemplazar por `engine_config/ontology_taxonomies.json`.
2.  **Variables y Constantes Prohibidas (Buscar en todo el repositorio con `grep`/`ripgrep` y erradicar):**
    *   `_TOWER_KEYWORDS`
    *   `trigger_keywords`
    *   `legacy_cleaning_keywords`
    *   `_ABSENCE_PATTERNS` / `absence_keywords` (La detección de "ausencia de control" ahora la resuelve `AbsenceSemanticEvaluation` dentro del router neurosimbólico).
    *   `domain_keywords` / `keyword_weights`
3.  **Patrones de Código Prohibidos para Clasificación de Dominio:**
    *   Queda prohibido el uso de `re.search()`, `re.findall()`, `in text.lower()` o `difflib` para decidir a qué torre pertenece un hallazgo, determinar su severidad o detectar si un control está ausente. *(Nota: El uso de Regex sigue permitido ÚNICAMENTE para limpieza de formato puro, como quitar saltos de línea múltiples `\n+`, parsear fechas ISO o extraer IDs alfanuméricos como `F-001`).*

---

## 4. PLAN DE EJECUCIÓN PASO A PASO (GUÍA PARA GEMINI 3.8)

Ejecute este plan en orden secuencial estricto. No salte pasos ni deje código muerto comentado.

### FASE 1: Auditoría de Erradicación e Infraestructura Ontológica

#### Paso 1.1: Escaneo Forense Inicial
Ejecute una búsqueda global en el repositorio para listar todos los archivos que contienen las heurísticas actuales:
```bash
grep -rnE "(_TOWER_KEYWORDS|trigger_keywords|legacy_cleaning_keywords|_ABSENCE_PATTERNS|tower_classification_keywords)" src/ engine_config/ tests/
```
Anote cada archivo e línea. Todos deben quedar limpios al finalizar la Fase 3.

#### Paso 1.2: Creación del Contrato Ontológico
1. Elimine `engine_config/tower_classification_keywords.json`.
2. Cree `engine_config/ontology_taxonomies.json`.
3. Redacte las definiciones ontológicas completas para las 10 torres (`T1` a `T10`), asegurándose de incluir para cada una: `id`, `name`, `core_jurisdiction`, y `explicit_exclusions`. Asegúrese de cubrir casos borde clásicos (OT vs IT, Cloud vs On-Prem, Seguridad de Red vs Operaciones de Red, ERP vs Infraestructura de Base de Datos).

#### Paso 1.3: Creación de los Esquemas Pydantic
Cree el archivo `src/core/schemas/routing_schemas.py` e implemente exactamente las clases `TowerID`, `AbsenceSemanticEvaluation`, `SemanticRoutingDecision`, y `BatchSemanticRoutingResponse` definidas en la Sección 2.2 de este documento.

---

### FASE 2: Construcción del Motor `DomainSemanticRouter`

#### Paso 2.1: Implementación del Servicio de Enrutamiento
Cree `src/core/routing/neurosymbolic_router.py`. Este módulo debe cargar la ontología, construir el System Prompt neurosimbólico y ejecutar llamadas estructuradas al cliente LLM central del proyecto.

```python
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from src.core.schemas.routing_schemas import (
    BatchSemanticRoutingResponse,
    SemanticRoutingDecision,
    TowerID
)

logger = logging.getLogger(__name__)

class DomainSemanticRouter:
    """
    Motor de Enrutamiento Semántico Neurosimbólico Tier-1.
    Reemplaza todas las heurísticas basadas en keywords y regex por inferencia
    ontológica restringida mediante esquemas Pydantic.
    """

    def __init__(self, llm_client: Any, ontology_path: str = "engine_config/ontology_taxonomies.json", batch_size: int = 20):
        self.llm_client = llm_client
        self.batch_size = batch_size
        self.ontology_path = Path(ontology_path)
        self.ontology = self._load_ontology()
        self._routing_cache: Dict[str, SemanticRoutingDecision] = {}

    def _load_ontology(self) -> Dict[str, Any]:
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Contrato ontológico crítico no encontrado en: {self.ontology_path}")
        with open(self.ontology_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _compute_semantic_hash(self, text: str, context: str = "") -> str:
        normalized = f"{text.strip().lower()}||{context.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _build_system_prompt(self) -> str:
        principles = "\n".join([f"- {p}" for p in self.ontology.get("routing_principles", [])])
        towers_spec = json.dumps(self.ontology.get("towers", {}), indent=2, ensure_ascii=False)
        
        return f"""Eres un Arquitecto Principal de Sistemas Empresariales y Clasificador Ontológico Neurosimbólico.
Tu única misión es analizar hallazgos técnicos de infraestructura/TI (en cualquier idioma) y asignarlos a su Torre Tecnológica de jurisdicción raíz exacta.

PRINCIPIOS AXIOMÁTICOS DE ENRUTAMIENTO:
{principles}

CONTRATO ONTOLÓGICO DE TORRES (JURISDICCIONES Y EXCLUSIONES ESTRICTAS):
{towers_spec}

INSTRUCCIONES DE EJECUCIÓN:
1. Analiza la causalidad del hallazgo, no las palabras clave superficiales.
2. Verifica las 'explicit_exclusions' de la torre candidata antes de tomar una decisión.
3. Resuelve ambigüedades léxicas (polisemia) usando el contexto operativo de la oración.
4. Determina si el hallazgo representa la ausencia/inexistencia total de un control o capacidad (absence_evaluation).
5. Devuelve ÚNICAMENTE el objeto JSON estructurado que cumple con el esquema BatchSemanticRoutingResponse."""

    async def route_findings_batch(self, findings: List[Dict[str, str]]) -> Dict[str, SemanticRoutingDecision]:
        """
        Enruta una lista de hallazgos.
        Cada elemento de `findings` debe tener: {'id': str, 'text': str, 'context': Optional[str]}
        Retorna un diccionario mapeando `finding_id` -> `SemanticRoutingDecision`.
        """
        results: Dict[str, SemanticRoutingDecision] = {}
        to_evaluate: List[Dict[str, str]] = []

        # 1. Verificación en caché determinista en memoria
        for item in findings:
            f_id = item["id"]
            f_text = item["text"]
            f_ctx = item.get("context", "")
            s_hash = self._compute_semantic_hash(f_text, f_ctx)
            
            if s_hash in self._routing_cache:
                cached_decision = self._routing_cache[s_hash].model_copy(
                    update={"finding_id": f_id},
                    deep=True
                )
                results[f_id] = cached_decision
            else:
                to_evaluate.append(item)

        if not to_evaluate:
            return results

        # 2. Procesamiento por Micro-Batches vía Constrained Decoding
        system_prompt = self._build_system_prompt()
        
        for i in range(0, len(to_evaluate), self.batch_size):
            batch = to_evaluate[i : i + self.batch_size]
            user_payload = json.dumps(
                [{"finding_id": b["id"], "finding_text": b["text"], "source_context": b.get("context", "")} for b in batch],
                indent=2,
                ensure_ascii=False
            )

            # Invocación al wrapper LLM del motor forzando response_schema=BatchSemanticRoutingResponse
            batch_response: BatchSemanticRoutingResponse = await self.llm_client.generate_structured(
                system_prompt=system_prompt,
                user_prompt=f"Evalúa y enruta el siguiente lote de hallazgos:\n{user_payload}",
                response_model=BatchSemanticRoutingResponse,
                temperature=0.0  # Determinismo máximo para clasificación ontológica
            )

            for decision in batch_response.decisions:
                results[decision.finding_id] = decision
                # Guardar en caché para evitar llamadas duplicadas
                orig_item = next((x for x in batch if x["id"] == decision.finding_id), None)
                if orig_item:
                    s_hash = self._compute_semantic_hash(orig_item["text"], orig_item.get("context", ""))
                    self._routing_cache[s_hash] = decision

        return results
```

---

### FASE 3: Cirugía de Reemplazo y Limpieza de Código Legado

1.  **En los clasificadores e ingestores de hallazgos (ej. `tower_classifier.py`, `finding_processor.py`, `normalizer.py` o equivalentes detectados en el Paso 1.1):**
    *   Elimine todas las funciones que iteran sobre `_TOWER_KEYWORDS` o `trigger_keywords`.
    *   Inyecte `DomainSemanticRouter` en el pipeline de procesamiento de hallazgos.
    *   Reemplace los bucles de clasificación síncrona elemento-por-elemento por una llamada consolidada a `await router.route_findings_batch(...)`.
    *   Asigne `finding.tower = decision.primary_tower.value`, `finding.routing_justification = decision.chain_of_thought_jurisdiction` y `finding.is_absence = decision.absence_evaluation.is_absence_of_control`.

2.  **En los módulos de limpieza y sanitización (`legacy_cleaning_keywords`):**
    *   Si existían listas de keywords para descartar hallazgos inválidos o basura documental, mueva esa responsabilidad a la definición de `UNCLASSIFIED` dentro de `ontology_taxonomies.json` (ej. *"Si el texto es un encabezado de página, índice o texto sin contenido técnico evaluable, asigne UNCLASSIFIED"*).

---

### FASE 4: Suite de Validación Adversarial y Garantía de Cero Regresiones

El agente implementador debe crear el archivo de pruebas `tests/routing/test_neurosymbolic_router_adversarial.py` y asegurarse de que pase al 100% antes de dar por concluida la tarea.

#### Casos de Prueba Obligatorios (Adversarial Golden Dataset):
La prueba debe evaluar los siguientes casos trampa que destruían al motor anterior:

```python
ADVERSARIAL_TEST_CASES = [
    {
        "id": "ADV-001",
        "text": "La integración API con el proveedor logístico UPS falla al generar guías de despacho en el módulo SD del ERP.",
        "expected_tower": "T6",  # Aplicaciones/ERP, NUNCA T1 (Energía/UPS)
        "expected_absence": False
    },
    {
        "id": "ADV-002",
        "text": "Los servidores de control local ubicados en la planta mezcladora de concreto presentan reinicios por exceso de polvo y vibración en el piso de producción.",
        "expected_tower": "T10", # OT/Planta Industrial, NUNCA T1 (Data Center)
        "expected_absence": False
    },
    {
        "id": "ADV-003",
        "text": "No existe ningún procedimiento ni herramienta automatizada para la gestión de parches de seguridad en los endpoints corporativos.",
        "expected_tower": "T4",  # Ciberseguridad / Endpoint Security (o la torre definida para EUC/Sec en la ontología)
        "expected_absence": True # Debe detectar ausencia semántica sin usar regex
    },
    {
        "id": "ADV-004",
        "text": "Die Cloud-Datenbankinstanzen in AWS haben keine automatischen Snapshots konfiguriert.", # Alemán (Multilingüismo nativo)
        "expected_tower": "T2",  # Cloud Infrastructure
        "expected_absence": True
    }
]
```

#### Comandos de Verificación de Cumplimiento (Definition of Done):
Para certificar la erradicación total, el agente debe ejecutar y demostrar salida limpia en los siguientes comandos:

1. **Verificación de Erradicación Léxica (Debe retornar 0 coincidencias):**
   ```bash
   grep -rnE "(_TOWER_KEYWORDS|trigger_keywords|legacy_cleaning_keywords|_ABSENCE_PATTERNS|tower_classification_keywords)" src/ engine_config/
   ```
2. **Ejecución de Pruebas Unitarias y Adversariales:**
   ```bash
   pytest tests/routing/test_neurosymbolic_router_adversarial.py -v
   pytest tests/ -v
   ```

---
**FIN DEL MANDATO ARQUITECTÓNICO.** Proceda con la demolición del código legado y la construcción del enrutador neurosimbólico sin desviaciones.