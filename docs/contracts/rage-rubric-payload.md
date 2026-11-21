---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain/schemas/rubric.py
- engine_config/frameworks
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical technical specification of the declarative RAGE framework rubric JSON contract.
---
# RAGE Framework Rubric JSON Contract

Canonical data contract specification for declarative regulatory framework rubrics consumed by the **Runtime Agentic Grounding & Evaluation (RAGE)** engine (`agentic_benchmarker.py`).

All regulatory framework definitions stored under `engine_config/frameworks/` (e.g., `google_dora.json`, `ens_alta.json`, `dama_dmbok.json`) MUST strictly adhere to this schema, validated by the Pydantic model `FrameworkRubric` (`src/assessment_engine/domain/schemas/rubric.py`).

---

## 1. Schema Hierarchy & Structure

A framework rubric organizes empirical evaluation criteria across three levels:

```
[ FrameworkRubric (Root) ]
├── framework_id: str                (Unique slug identifier, e.g., "google_dora")
├── framework_name: str              (Official display title)
├── description: Optional[str]       (Contextual scope and regulatory mandate)
└── rules: List[RubricRule]          (List of technology tower evaluation rules)
    ├── tower_id: str                (Target tower code, e.g., "T1")
    ├── query_template: str          (OSINT search template parameterized by context)
    ├── evaluation_variable: str     (Metric extracted from evidence, default: "adoption")
    ├── default_score: float         (Fallback maturity score upon evaluation degradation)
    └── thresholds: List[ThresholdMapping]
        ├── condition: str           (Deterministic Python expression, e.g., "adoption >= 65.0")
        └── score: float             (Quantitative CMMI score assigned upon satisfaction)
```

---

## 2. Pydantic Model Attribute Specifications

### A. Root Model: `FrameworkRubric`

| Field | Type | Required | Invariant & Description |
|---|---|:---:|---|
| `framework_id` | `str` | **Yes** | Unique snake_case identifier matching filename (e.g., `google_dora`, `ens_alta`). |
| `framework_name` | `str` | **Yes** | Formal institutional title of the standard. |
| `description` | `Optional[str]` | No | Explanatory notes detailing applicability and regulatory scope. |
| `rules` | `List[RubricRule]` | **Yes** | Ordered evaluation rules mapped to specific technology towers. |

### B. Rule Model: `RubricRule`

| Field | Type | Required | Invariant & Description |
|---|---|:---:|---|
| `tower_id` | `str` | **Yes** | Target technology tower code (e.g., `T1`, `T2`, `T3`, `T5`). |
| `query_template` | `str` | **Yes** | Grounded query string template dispatched to Vertex AI Google Search. |
| `evaluation_variable` | `str` | No (default: `"adoption"`) | Variable name parsed from evidence texts to test against threshold conditions. |
| `thresholds` | `List[ThresholdMapping]` | **Yes** | Ordered list of condition-score mappings evaluated sequentially. |
| `default_score` | `float` | No (default: `3.0`) | Baseline score assigned if no threshold condition evaluates to `True`. |

### C. Condition Model: `ThresholdMapping`

| Field | Type | Required | Invariant & Description |
|---|---|:---:|---|
| `condition` | `str` | **Yes** | Mathematical comparison expression evaluated by pure-Python AST parser (e.g., `"adoption >= 65.0"`). |
| `score` | `float` | **Yes** | Quantitative maturity score $\in [1.0, 5.0]$ assigned when condition is satisfied. |

---

## 3. Validated Reference Payload Example

The following JSON illustrates a fully compliant framework rubric matching `engine_config/frameworks/google_dora.json`:

```json
{
  "framework_id": "google_dora",
  "framework_name": "Google DORA (DevOps Research and Assessment)",
  "description": "De facto standard measuring software delivery operational stability and engineering velocity.",
  "rules": [
    {
      "tower_id": "T1",
      "query_template": "Google DORA report utilities deployment frequency percentage",
      "evaluation_variable": "adoption",
      "thresholds": [
        {
          "condition": "adoption >= 65.0",
          "score": 4.5
        },
        {
          "condition": "adoption >= 45.0",
          "score": 4.0
        },
        {
          "condition": "adoption >= 25.0",
          "score": 3.5
        }
      ],
      "default_score": 3.0
    }
  ]
}
```

---

## 4. Evaluation Engine Invariants

1. **Deterministic Sequential Matching:** The RAGE evaluator checks `thresholds` in the declared array order. The first condition evaluating to `True` terminates evaluation and assigns `score`.
2. **Safe Python Evaluation:** Expressions in `condition` parse strictly through Python's `ast` module; execution of arbitrary Python code via `eval()` is strictly prohibited.
3. **Bounded Scoring:** All `score` and `default_score` values must satisfy $1.0 \le \text{score} \le 5.0$.
