---
status: Verified
owner: architecture-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-07
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: editorial
---
### 1. Candid Architectural Assessment: Is Compiler String Interception a Patch?

**Yes. Unequivocally, intercepting `"HIGH."` at the AST rendering layer (`payload_to_ast.py`) is an architectural anti-pattern—specifically, a "Shotgun Surgery / Defensive String Patch" that masks upstream schema corruption.**

In a Tier-1 engineering organization (Google Staff, Stripe, Anthropic), a rendering compiler (`payload_to_ast.py`) must adhere to the **Parse, Don't Validate** and **Single Responsibility** principles. Its sole responsibility is to project a verified, strongly-typed intermediate representation (IR) into an Abstract Syntax Tree (AST). 

Here is why the string-interception approach fails a Tier-1 design review:

1. **Semantic Conflation (Type Pollution):** The pipeline currently overloads the token `"impact"` to mean two fundamentally orthogonal concepts:
   * **Actuarial Severity Tier (Ordinal Enum):** `LOW | MEDIUM | HIGH | CRITICAL` (used for risk matrices, heatmap coordinates, and sorting).
   * **Operational Impact Narrative (Causal Prose):** A qualitative explanation of *how* the failure mode degrades continuity, SLA compliance, or financial performance.
2. **Broken Fallback Coalescing:** In `in_memory_asis_compiler.py` (Line 69), the expression `hc.get("business_risk") or hc.get("impact")` violates type safety by coalescing a `NarrativeString` with a `SeverityEnum`. When `business_risk` is `None`, the enum leaks across the type boundary into a prose field.
3. **Late-Stage Masking (Silent Data Degradation):** If `payload_to_ast.py` intercepts `"HIGH."` and replaces it with a generic boilerplate sentence at the final mile, the system hides the fact that the upstream Hydration/Synthesis engine failed to compute the actual operational consequence of that specific KPI deficit.

---

### 2. The Tier-1 Root-Cause Architecture

A world-class distributed systems and actuarial engineering team resolves this by enforcing **Strict Domain Disambiguation**, **Upstream Causal Synthesis**, and **Compiler Invariant Gates**:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: DOMAIN CONTRACT (Pydantic V2 Strict Schema)                         │
│ • Disambiguates `impact_severity: SeverityEnum` from                         │
│   `business_risk: CausalNarrative` (min_length=25, rejects bare enums).      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: UPSTREAM HYDRATION (`_generate_canonical_kpi_finding`)              │
│ • Computes deterministic, telemetry-grounded causal narratives at the source │
│   using observed vs. target KPI deltas, domain taxonomy, and SLA exposure.   │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: IR COMPILER (`in_memory_asis_compiler.py`)                          │
│ • Eliminates cross-type fallback coalescing (`business_risk or impact`).     │
│ • Maps `impact_severity` strictly to ordinal metadata and `business_risk`    │
│   strictly to narrative slots.                                               │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: AST INVARIANT GATE (`payload_to_ast.py`)                            │
│ • Enforces a structural contract assertion (Guard Clause) rather than silent │
│   string patching. Raises a telemetry violation or invokes deterministic     │
│   structural synthesis from the node's own metrics if legacy payloads enter. │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

### 3. Production-Grade Implementation (100% Technical English)

#### Component A: Domain Contract Disambiguation (`domain/contracts/finding_schema.py`)

We establish a strict boundary between categorical severity ratings and qualitative causal narratives using Pydantic V2 validators.

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class SeverityTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Forbidden bare tokens that indicate an Enum leaked into a narrative field
_ENUM_LEAK_TOKENS = frozenset({
    "LOW", "MEDIUM", "HIGH", "CRITICAL",
    "LOW.", "MEDIUM.", "HIGH.", "CRITICAL.",
    "N/A", "NONE", "NULL", "UNKNOWN", "TBD"
})


class CanonicalFindingContract(BaseModel):
    """
    Tier-1 Domain Contract for AS-IS Diagnostic Findings.
    Strictly decouples ordinal severity from qualitative operational narratives.
    """
    finding_id: str = Field(..., min_length=3)
    domain: str = Field(..., min_length=2)
    title: str = Field(..., min_length=5)
    
    # 1. Categorical / Ordinal Severity (Used for heatmaps, sorting, badges)
    impact_severity: SeverityTier = Field(
        default=SeverityTier.HIGH,
        description="Categorical actuarial severity rating."
    )
    
    # 2. Qualitative Narratives (Used for executive prose and AST tables)
    description: str = Field(
        ...,
        min_length=20,
        description="Technical root-cause description of the observed deficit."
    )
    business_risk: str = Field(
        ...,
        min_length=25,
        description="Causal narrative explaining impact on operations and continuity."
    )
    recommendation: Optional[str] = Field(
        default=None,
        description="Actionable architectural remediation."
    )

    @field_validator("business_risk", mode="before")
    @classmethod
    def reject_enum_leakage_in_narrative(cls, v: Optional[str]) -> str:
        """Invariant Gate: Prevents categorical enums from polluting narrative fields."""
        if not v or not isinstance(v, str):
            raise ValueError("business_risk narrative cannot be null or non-string.")
        cleaned = v.strip()
        if cleaned.upper() in _ENUM_LEAK_TOKENS or len(cleaned.split()) < 4:
            raise ValueError(
                f"Contract Violation: 'business_risk' received categorical token or "
                f"fragment '{cleaned}' instead of a causal operational narrative."
            )
        return cleaned

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_impact_field(cls, data: dict) -> dict:
        """
        Handles legacy dictionary payloads where 'impact' held 'HIGH'
        without polluting 'business_risk'.
        """
        if not isinstance(data, dict):
            return data
            
        raw_impact = str(data.get("impact") or "").strip()
        if raw_impact.upper() in SeverityTier.__members__:
            data.setdefault("impact_severity", raw_impact.upper())
            
        # Promote primary_impact to business_risk only if it is genuine prose
        primary_impact = str(data.get("primary_impact") or "").strip()
        if primary_impact and primary_impact.upper() not in _ENUM_LEAK_TOKENS:
            data.setdefault("business_risk", primary_impact)
            
        return data
```

---

#### Component B: Upstream Root-Cause Resolution in Hydration (`_generate_canonical_kpi_finding`)

Instead of emitting `"impact": "HIGH"` with no narrative, the hydrator deterministically synthesizes the causal operational risk directly from the KPI's telemetry (metric name, current value, target benchmark, and functional domain) at creation time.

```python
from typing import Dict, Any


def _derive_kpi_operational_impact(
    kpi_name: str,
    domain_label: str,
    current_val: Any,
    target_val: Any,
    severity: str,
    lang: str = "es"
) -> str:
    """
    Deterministically synthesizes a telemetry-grounded operational impact narrative
    from the KPI performance gap, eliminating empty or enum-polluted risk fields.
    """
    kpi_clean = str(kpi_name or "el indicador operativo").strip().rstrip(".")
    domain_clean = str(domain_label or "la operación").strip().rstrip(".")
    cur_str = str(current_val).strip() if current_val not in (None, "", "N/A") else None
    tgt_str = str(target_val).strip() if target_val not in (None, "", "N/A") else None

    if lang == "es":
        if cur_str and tgt_str:
            return (
                f"La desviación en {kpi_clean} (registro actual de {cur_str} frente al umbral "
                f"objetivo de {tgt_str}) degrada la capacidad de respuesta en {domain_clean}, "
                f"incrementando la exposición a incumplimientos de nivel de servicio (SLA) y "
                f"fricción operativa sostenida."
            )
        if cur_str:
            return (
                f"El desempeño observado en {kpi_clean} ({cur_str}) carece de acotamiento "
                f"frente a un umbral objetivo formal en {domain_clean}, reduciendo la "
                f"previsibilidad operativa y la capacidad de detección temprana de fallos."
            )
        return (
            f"La ausencia de instrumentación verificable sobre {kpi_clean} impide auditar "
            f"el rendimiento real en {domain_clean}, exponiendo la continuidad operativa a "
            f"cuellos de botella no detectados y decisiones reactivas."
        )

    # English fallback for multi-locale pipelines
    if cur_str and tgt_str:
        return (
            f"Variance in {kpi_clean} (observed at {cur_str} against a target threshold of "
            f"{tgt_str}) degrades execution predictability across {domain_clean}, elevating "
            f"SLA breach exposure and operational friction."
        )
    return (
        f"Uninstrumented performance across {kpi_clean} within {domain_clean} obscures "
        f"capacity bottlenecks and impairs proactive continuity management."
    )


def _generate_canonical_kpi_finding(
    kpi_node: Dict[str, Any],
    domain_context: str,
    lang: str = "es"
) -> Dict[str, Any]:
    """
    Produces a strictly disambiguated Canonical Finding dictionary from a KPI deficit.
    Guarantees both ordinal severity (`impact_severity`) and causal prose (`business_risk`).
    """
    kpi_id = str(kpi_node.get("id") or kpi_node.get("kpi_id") or "KPI-UNSPECIFIED").strip()
    kpi_name = str(kpi_node.get("name") or kpi_node.get("label") or kpi_id).strip()
    current_val = kpi_node.get("current_value") or kpi_node.get("value")
    target_val = kpi_node.get("target_value") or kpi_node.get("benchmark")
    
    raw_severity = str(kpi_node.get("severity") or kpi_node.get("impact") or "HIGH").upper().strip()
    severity_tier = raw_severity if raw_severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "HIGH"

    # Extract explicit narrative if provided upstream; validate it is not a leaked enum
    explicit_risk = str(
        kpi_node.get("business_risk") or kpi_node.get("primary_impact") or ""
    ).strip()
    
    if explicit_risk.upper() in {"LOW", "MEDIUM", "HIGH", "CRITICAL", "LOW.", "MEDIUM.", "HIGH.", "CRITICAL.", ""}:
        operational_narrative = _derive_kpi_operational_impact(
            kpi_name=kpi_name,
            domain_label=domain_context,
            current_val=current_val,
            target_val=target_val,
            severity=severity_tier,
            lang=lang,
        )
    else:
        operational_narrative = explicit_risk

    return {
        "finding_id": kpi_id,
        "domain": domain_context,
        "title": kpi_name,
        "impact_severity": severity_tier,          # Explicit Categorical Enum
        "impact": severity_tier,                   # Retained strictly for backward-compatible sorting
        "business_risk": operational_narrative,    # Guaranteed Causal Narrative
        "primary_impact": operational_narrative,   # Guaranteed Causal Narrative
        "description": str(kpi_node.get("description") or operational_narrative).strip(),
    }
```

---

#### Component C: Eliminating Type Coalescing in `in_memory_asis_compiler.py`

In `in_memory_asis_compiler.py` (around Line 69), we remove the toxic `hc.get("business_risk") or hc.get("impact")` fallback that conflated the two types.

```python
# in_memory_asis_compiler.py

_SEVERITY_ENUM_TOKENS = frozenset({
    "LOW", "MEDIUM", "HIGH", "CRITICAL",
    "LOW.", "MEDIUM.", "HIGH.", "CRITICAL.",
    "BAJO", "MEDIO", "ALTO", "CRÍTICO", "CRITICO"
})


def _extract_verified_business_risk(hc: dict, domain_label: str, lang: str = "es") -> str:
    """
    Extracts the qualitative operational risk narrative from a finding node.
    Strictly forbids falling back to the categorical 'impact' severity enum.
    """
    for candidate_key in ("business_risk", "primary_impact", "operational_impact"):
        candidate = str(hc.get(candidate_key) or "").strip()
        if candidate and candidate.upper() not in _SEVERITY_ENUM_TOKENS and len(candidate.split()) >= 4:
            return candidate

    # If legacy cached payloads (e.g., pre-hydrated blueprint_t1_payload.json on disk)
    # lack `business_risk`, synthesize deterministically from the node's own title & description
    title = str(hc.get("title") or hc.get("name") or "el control evaluado").strip().rstrip(".")
    desc = str(hc.get("description") or hc.get("finding") or "").strip().rstrip(".")
    
    if desc and desc.upper() not in _SEVERITY_ENUM_TOKENS and len(desc.split()) >= 6:
        return (
            f"La persistencia de esta condición sobre {title} compromete la estabilidad "
            f"operativa en {domain_label}, elevando el riesgo de interrupciones en el flujo "
            f"de servicio y sobrecoste de remediación correctiva."
        )

    return _derive_kpi_operational_impact(
        kpi_name=title,
        domain_label=domain_label,
        current_val=hc.get("current_value") or hc.get("value"),
        target_val=hc.get("target_value") or hc.get("benchmark"),
        severity=str(hc.get("impact_severity") or hc.get("impact") or "HIGH"),
        lang=lang,
    )
```

Within the compiler loop in `in_memory_asis_compiler.py`:
```python
# BEFORE (Buggy Type Conflation):
# business_risk = str(hc.get("business_risk") or hc.get("impact") or "").strip()

# AFTER (Tier-1 Disambiguated Extraction):
impact_severity = str(hc.get("impact_severity") or hc.get("impact") or "HIGH").upper().strip()
business_risk = _extract_verified_business_risk(hc, domain_label=domain_name, lang="es")
```

---

#### Component D: Compiler Invariant Gate in `payload_to_ast.py`

Finally, at Line 2698 of `payload_to_ast.py`, instead of a naive string replacement patch, we implement a **Compiler Invariant Gate**. It verifies that `raw_impact` satisfies narrative structural invariants before emitting AST nodes, and logs a structured schema telemetry warning if an unmigrated disk artifact bypassed upstream hydration.

```python
# payload_to_ast.py (around Line 2698)

_BARE_SEVERITY_TOKENS = frozenset({
    "LOW", "MEDIUM", "HIGH", "CRITICAL",
    "LOW.", "MEDIUM.", "HIGH.", "CRITICAL.",
    "BAJO", "MEDIO", "ALTO", "CRÍTICO", "CRITICO",
    "BAJO.", "MEDIO.", "ALTO.", "CRÍTICO.", "CRITICO."
})

raw_impact = str(hc.get("primary_impact") or hc.get("business_risk") or "").strip()

# Compiler Invariant Gate: Enforce that narrative slots never render bare ordinal enums
if not raw_impact or raw_impact.upper() in _BARE_SEVERITY_TOKENS or len(raw_impact.split()) < 4:
    logger.warning(
        "AST_CONTRACT_VIOLATION: Finding '%s' arrived at AST compiler with non-narrative "
        "impact token '%s'. Executing contextual synthesis from finding telemetry.",
        hc.get("id") or hc.get("title", "UNKNOWN"),
        raw_impact,
    )
    raw_impact = _extract_verified_business_risk(
        hc,
        domain_label=str(hc.get("domain") or section_title or " el dominio operativo").strip(),
        lang="es",
    )

impact_txt = raw_impact if raw_impact.endswith(".") else f"{raw_impact}."
```

---

### 4. Summary of Why This Is the Definitive Tier-1 Solution

| Architectural Dimension | Naive Patch (`if impact_txt == "HIGH."`) | Tier-1 Root-Cause Architecture |
| :--- | :--- | :--- |
| **Type Safety** | Leaves `"impact"` overloaded across the codebase. | Separates `impact_severity: SeverityTier` from `business_risk: CausalNarrative`. |
| **Point of Resolution** | Final-mile string interception in the AST renderer. | Solved at **Hydration source** (`_generate_canonical_kpi_finding`) + **IR Compiler** (`in_memory_asis_compiler.py`). |
| **Information Density** | Replaces `"HIGH."` with a static, repetitive boilerplate phrase across all tables. | Synthesizes a **telemetry-grounded narrative** using the specific KPI name, observed value, target benchmark, and domain context. |
| **Cached Artifact Resilience** | Masks corrupt JSON payloads silently. | Handles pre-existing `blueprint_t1_payload.json` artifacts on disk while emitting `AST_CONTRACT_VIOLATION` telemetry and enforcing Pydantic schema validation on new runs. |