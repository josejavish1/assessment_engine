# BRIEFING DE ARQUITECTURA DE SISTEMAS: Motor Neurosimbólico Dinámico y Agnóstico de Ontologías

**De:** `gemini-4-argon`, Principal Enterprise Architect  
**Para:** Stakeholders de Ingeniería y Liderazgo Técnico  
**Asunto:** Rediseño Arquitectónico Radical: Inyección Dinámica de Ontologías, Metaprogramación de Gramáticas y Aislamiento Léxico Absoluto  

---

## 1. Autocrítica Arquitectónica: La Falacia de los `Enums` Estáticos

Acepto la crítica sin reservas. Nuestra propuesta anterior contenía un defecto de diseño crítico que violaba el mandato de universalidad: **acoplamiento ontológico estático**.

Definir estructuras en el código fuente como `class TowerID(StrEnum): T1_INFRA, T2_APPS...` o `class DomainTarget(StrEnum): FINANCE, LEGAL...` constituye un antipatrón severo cuando se diseña un motor de propósito general (Universal Core Engine). 

### ¿Por qué el Hardcoding de `Enums` destruye la escalabilidad multi-vertical?
1. **Acoplamiento Semántico al Código Fuente:** Si los dominios de negocio viven en el código Python, el motor deja de ser una plataforma y se convierte en un script de propósito específico (p. ej., sirve para auditorías de TI, pero es inútil para clasificación de triaje médico en Salud, análisis de riesgo crediticio en Banca o evaluación de talento en RRHH).
2. **Violación del Principio Abierto/Cerrado (OCP):** Bajo el diseño anterior, agregar un nuevo vertical de industria o modificar una taxonomía para un cliente Tier-1 requería modificar el código fuente, alterar los tipos estáticos, recompilar y redesplegar el núcleo del sistema.
3. **Contaminación Lingüística:** Al atar los identificadores del código a conceptos específicos de un negocio o idioma en tiempo de diseño, se imposibilita la internacionalización nativa (i18n) de enlace tardío (late-binding).

Para lograr un sistema verdaderamente **Universal, Multi-Tenant, Multi-Vertical y Multi-Idioma**, el motor no debe saber *qué* está clasificando; solo debe saber *cómo* navegar un espacio topológico de reglas y nodos abstractos inyectados en tiempo de ejecución.

---

## 2. La Nueva Arquitectura SOTA: Inyección Dinámica de Ontologías y Metaprogramación

Para cumplir al 100% con el mandato ("Cero Hardcoding", "Cualquier Vertical", "Cualquier Idioma", "100% Código en Inglés"), elevamos la arquitectura a un **Motor Neurosimbólico Guiado por Metadatos (Metadata-Driven Neurosymbolic Engine)**.

El sistema se divide en tres pilares fundamentales: **El Dominio Hermético Abstracto**, **El Compilador Dinámico de Gramáticas (Bootstrap)** y **La Capa de Localización de Enlace Tardío (Late-Binding i18n)**.

```
[Ontología JSON Externa] ──(Bootstrap)──> [Metaprogramación Pydantic] ──> [Gramática LLM Dinámica (GBNF)]
                                                    │
                                                    ▼
[Input Multi-Idioma] ──> [Inferencia Neurosimbólica] ──> [IDs Canónicos Abstractos] ──(i18n)──> [UI Localizada]
```

---

### Pilar 1: El Dominio Hermético y Abstracto (100% Inglés Técnico)

El núcleo del sistema (Domain Layer) se purga de cualquier referencia a "Torres", "TI", "Finanzas" o cualquier término en español. El código fuente, los *docstrings*, los logs de sistema y los esquemas internos están escritos estrictamente en **Inglés Técnico Estándar**.

El dominio opera exclusivamente sobre grafos matemáticos y conceptos taxonómicos abstractos:

*   **`TaxonomySpace`**: El contenedor raíz que representa el universo de discurso de un cliente o vertical específico (antes "El Assessment").
*   **`OntologyNode`**: Una entidad abstracta dentro del espacio taxonómico (antes "Torre" o "Dominio"). Posee un `canonical_id` inmutable (ej. `node_a1b2`, `category_01`), un vector de reglas simbólicas y metadatos de enrutamiento.
*   **`SymbolicRule`**: Condiciones lógicas deterministas evaluadas sobre atributos abstractos, sin conocimiento del significado semántico humano de dichos atributos.

```python
# 100% English Codebase - Zero Business Vertical Coupling
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass(frozen=True)
class OntologyNode:
    canonical_id: str
    semantic_directive: str  # Injected in English for the LLM prompt
    deterministic_keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TaxonomySpace:
    space_id: str
    version: str
    nodes: Dict[str, OntologyNode]
```

---

### Pilar 2: Fase de Bootstrap y Compilación Dinámica de Gramáticas (Metaprogramación)

El desafío técnico más complejo de eliminar los `Enums` estáticos es mantener el **Structured Outputs (Constrained Decoding)** del LLM. Si no tenemos un esquema Pydantic escrito en el archivo `.py`, ¿cómo forzamos al LLM a responder solo con nodos válidos sin alucinar?

**Solución:** Utilizamos **Metaprogramación en Python (`pydantic.create_model` y construcción dinámica de tipos `Literal`)** durante la fase de arranque (*Bootstrap*) o por cada contexto de ejecución (*Tenant Context*).

1. **Ingesta de Ontología:** El motor lee la configuración de la base de datos o un archivo declarativo (`ontology_schema.json`) perteneciente al cliente/vertical activo.
2. **Síntesis de Tipos en Tiempo de Ejecución:** El motor extrae todos los `canonical_id` activos del JSON y construye en memoria un tipo `Enum` o `Literal` dinámico.
3. **Compilación del Esquema Pydantic:** Se invoca `pydantic.create_model` inyectando el tipo dinámico. Esto genera en memoria RAM la clase exacta que se enviará a la API del LLM para compilar la gramática libre de contexto (CFG / GBNF).

```python
from enum import Enum
from typing import Type
from pydantic import BaseModel, Field, create_model

class DynamicGrammarCompiler:
    """
    Compiles strict LLM output schemas at runtime from abstract ontology definitions.
    Zero hardcoded business domains.
    """
    
    @staticmethod
    def compile_classification_schema(taxonomy: TaxonomySpace) -> Type[BaseModel]:
        # 1. Dynamically construct an Enum in memory from loaded JSON keys
        valid_node_ids = {node_id: node_id for node_id in taxonomy.nodes.keys()}
        DynamicNodeEnum = Enum("DynamicNodeEnum", valid_node_ids, type=str)
        
        # 2. Build the semantic description dynamically to guide the LLM attention mechanism
        routing_guide = "\n".join(
            [f"- {n.canonical_id}: {n.semantic_directive}" for n in taxonomy.nodes.values()]
        )
        
        # 3. Synthesize the Pydantic model at runtime using metaprogramming
        DynamicClassificationModel = create_model(
            "DynamicClassificationOutput",
            reasoning_trace=(
                str, 
                Field(description="Step-by-step analytical reasoning in English.")
            ),
            target_node_id=(
                DynamicNodeEnum, 
                Field(description=f"Strict canonical target ID. Valid options:\n{routing_guide}")
            ),
            confidence_score=(
                float, 
                Field(ge=0.0, le=1.0, description="Calibrated probability score.")
            )
        )
        
        return DynamicClassificationModel
```

**Impacto Arquitectónico:** Si mañana el sistema es contratado por un hospital en Japón para clasificar síntomas en 50 especialidades médicas, o por una minera en Chile para clasificar riesgos operacionales en 12 categorías, **no se toca ni una sola línea de código Python**. El motor lee el JSON del hospital o de la minera, sintetiza el `DynamicClassificationOutput` en milisegundos y bloquea la gramática del LLM a esos 50 o 12 nodos exactos.

---

### Pilar 3: Internacionalización de Enlace Tardío (Late-Binding i18n)

Para que el motor sirva a cualquier compañía en cualquier idioma sin contaminar el código con cadenas de texto en español, aplicamos el patrón **Canonical ID Routing + Late-Binding Localization**.

1. **Procesamiento Políglota Transparente:** Los LLMs modernos son inherentemente multilingües en su espacio latente. El input del usuario puede entrar en español, alemán, japonés o inglés.
2. **Razonamiento e Identificación Canónica:** Las directivas del sistema (`semantic_directive`) y el esquema compilado exigen que el motor opere internamente en inglés técnico y emita únicamente el `canonical_id` (ej. `node_042`). El motor nunca emite texto de negocio como `"Torre de Aplicaciones"`.
3. **Traducción en la Frontera (Presentation Layer):** Solo cuando el resultado abandona el motor neurosimbólico para ser renderizado en un dashboard, reporte o API hacia el cliente, la capa de presentación intercepta el `node_042` y lo cruza con el catálogo de localización (`locales.json`) según el `Accept-Language` del usuario:

```json
// locales.json (External Configuration - Not in Python Code)
{
  "node_042": {
    "en-US": "Application Infrastructure & Cloud",
    "es-ES": "Infraestructura de Aplicaciones y Nube",
    "pt-BR": "Infraestrutura de Aplicações e Nuvem",
    "de-DE": "Anwendungsinfrastruktur & Cloud"
  }
}
```

---

## 3. Verificación de Cumplimiento del Mandato (Compliance Matrix)

| Mandato del Usuario | Estado | Solución Arquitectónica Aplicada |
| :--- | :---: | :--- |
| **Cero Hardcoding** | **CUMPLIDO** | Eliminación total de `StrEnum` estáticos de negocio. Todo nace de configuraciones externas inyectadas en el *Bootstrap*. |
| **Cualquier Vertical (Agnóstico)** | **CUMPLIDO** | El dominio opera sobre `TaxonomySpace` y `OntologyNode`. Sirve para TI, Legal, Medicina, Manufactura, Retail o Banca. |
| **Escala (SME a Top Tier-1)** | **CUMPLIDO** | Diseño *Multi-Tenant* sin estado (Stateless). Los esquemas Pydantic se compilan por *Tenant* y se cachean en memoria (`lru_cache`). |
| **Cualquier Idioma (Global)** | **CUMPLIDO** | Entrada multilingüe procesada en el espacio latente del LLM; enrutamiento interno por IDs canónicos; salida localizada vía *Late-Binding i18n*. |
| **Código 100% en Inglés** | **CUMPLIDO** | Prohibición estricta por *Linter/CI* de caracteres o palabras no inglesas en el repositorio de código. Todo el español vive en archivos `.json` de configuración externa. |

---

## 4. Conclusión Ejecutiva

La arquitectura anterior era una solución táctica excelente para un proyecto único, pero **insuficiente para un producto de software global de clase empresarial**. 

Al reemplazar la definición estática de tipos por **Metaprogramación de Esquemas en Tiempo de Ejecución** y abstraer el dominio hacia la **Teoría de Grafos Ontológicos**, hemos transformado el sistema. Ya no estamos construyendo una herramienta de evaluación fija; estamos construyendo un **Motor de Inferencia y Clasificación Universal**, 100% escrito en inglés técnico impecable, capaz de adaptarse camaleónicamente a cualquier industria y lenguaje del mundo mediante la simple inyección de un archivo JSON.