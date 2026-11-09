# RFC 071: Universal Multi-Tenant Decoupling & Dynamic SSOT Binding

**Status:** Approved for Immediate Implementation  
**Target Subsystem:** Consolidated & Per-Tower AST Compilation Engine (`tomo_asis_ast_compiler.py`, `payload_to_ast.py`, `engine_config/locales.json`)  
**Authors:** Chief Distributed Systems Architect & Lead Actuary  
**Enforcement Level:** Mandatory / Zero-Tolerance Gate  

---

## 1. Core Architectural Principles & Tenant Boundary Model

To guarantee that the assessment platform scales across any industry vertical (e.g., Commercial Banking, Healthcare, Heavy Manufacturing, Retail), revenue scale ($10M to $100B+), currency (`USD`, `EUR`, `JPY`, `GBP`), and target locale (`en`, `es`, `pt`, `fr`, `de`, `ja`), the engine enforces a strict **Three-Plane Isolation Model**.

```text
+-----------------------------------------------------------------------------------+
|                        PLANE 1: TENANT DATA SSOT (Runtime)                        |
|  Source: case_input.json -> Actuarial Engine -> tower_payloads + global_payload   |
|  Contains: Client Name, Currency, Sector Profile, Active Domains (1..N),          |
|            Asset Inventories, Subpillar Scores, Forensic Findings, VaR Figures.   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | Strict Schema Binding (Read-Only)
                                          v
+-----------------------------------------------------------------------------------+
|                     PLANE 2: AST COMPILATION & RECONCILIATION                     |
|  Components: TomoAsisASTCompiler, PayloadToASTCompiler, ActuarialReconciler       |
|  Invariants:                                                                      |
|    - 100% Technical English identifiers, docstrings, and fallback logic.          |
|    - Zero domain-count assumptions (Iterates strictly over active 1..N domains).  |
|    - Penny-exact Largest Remainder reconciliation across N active domains.        |
|    - Strict vertical budget clamping for OpenXML single-page containers.          |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | Token Interpolation ({token_key})
                                          v
+-----------------------------------------------------------------------------------+
|                  PLANE 3: LINGUISTIC FRAMING CATALOG (Static)                     |
|  Source: engine_config/locales.json                                               |
|  Contains: Pure grammatical structures, structural headings, table headers,       |
|            and sector-neutral parameterized narrative templates.                  |
|  FORBIDDEN: Proper nouns, specific vendors, cities, headcount, hourly rates,      |
|             or industry-specific machinery (e.g., weighbridges, bagging lines).   |
+-----------------------------------------------------------------------------------+
```

### 1.1 Invariant Contract Across Planes
1. **Data Authority (`tower_payloads` & `global_payload`):** The single source of truth for *what* exists in the client environment. If a client contracts 3 domains (`CLOUD`, `CYBER`, `DATA`), the engine processes exactly 3 domains.
2. **Linguistic Authority (`locales.json`):** The single source of truth for *how* structural phrases are translated into target human languages. It is strictly stateless regarding tenant assets.
3. **Zero Silent Borrowing:** If a tenant payload omits an optional telemetry field (e.g., `inventory` or `strengths`), the compiler must synthesize a deterministic, mathematically consistent statement derived from the domain's actual maturity score and financial exposure—never falling back to another tenant's static snapshot.

---

## 2. Catalog Decoupling Specification (`engine_config/locales.json`)

All tenant-specific literals, geographic sites, vendor contract dates, and manufacturing equipment references are purged from `engine_config/locales.json`. The legacy static key `tomo_tower_forensic_catalog` is **deprecated and removed**.

### 2.1 Before vs. After Catalog Remediation

#### Vector A: Executive & Archetype Narrative Templates
* **BEFORE (Contaminated with Single-Tenant Literals):**
  ```json
  "archetype_physical_t1_es": "La caída del centro de datos en Sant Vicenç dels Horts o de los 6 nodos HPE SimpliVity detiene las básculas de pesaje y líneas de ensacado en 18 países, con un impacto de 5.000 EUR/h tras la adquisición de Secil."
  ```
* **AFTER (Universal, Sector-Agnostic Parameterized Template):**
  ```json
  "archetype_infrastructure_physical": {
    "en": "Within {domain_title}, critical operational dependencies center on {inventory_summary}. A severe availability degradation across {facility_scope} directly disrupts {core_business_processes}, generating an estimated annualized operational risk exposure of {annualized_exposure} (95% VaR tail impact: {var_95_exposure}) weighted by a domain maturity index of {maturity_score}/5.00.",
    "es": "Dentro de {domain_title}, las dependencias operativas críticas se concentran en {inventory_summary}. Una degradación severa de disponibilidad en {facility_scope} interrumpe directamente {core_business_processes}, generando una exposición anualizada estimada al riesgo operativo de {annualized_exposure} (impacto de cola VaR 95%: {var_95_exposure}), ponderada por un índice de madurez de dominio de {maturity_score}/5.00."
  }
  ```

#### Vector B: Chapter 4 Forensic Domain Diagnostics
* **BEFORE (Contaminated Static Dictionary in `locales.json`):**
  ```json
  "tomo_tower_forensic_catalog": {
    "T1": {
      "inventory": "6 nodos HPE SimpliVity, cabinas NetApp, contrato VMware vence mayo 2027",
      "strengths": ["Consolidación tras compra de Secil"],
      "findings": ["Riesgo de parada en básculas de pesaje a 5.000 EUR/h"]
    }
  }
  ```
* **AFTER (Purged; Replaced by Dynamic Extraction Templates):**
  ```json
  "forensic_domain_templates": {
    "inventory_fallback": {
      "en": "Scoped technological estate for {domain_code} ({domain_title}), encompassing {subpillar_count} evaluated control subpillars under {sector_name} operational parameters.",
      "es": "Parque tecnológico evaluado para {domain_code} ({domain_title}), abarcando {subpillar_count} subpilares decontrol bajo parámetros operativos del sector {sector_name}."
    },
    "strength_fallback": {
      "en": "Established baseline operational continuity in {highest_subpillar_name} (maturity index {highest_subpillar_score}/5.00), containing immediate mean-time-to-recovery degradation.",
      "es": "Continuidad operativa base establecida en {highest_subpillar_name} (índice de madurez {highest_subpillar_score}/5.00), conteniendo la degradación inmediata del tiempo medio de recuperación."
    },
    "finding_fallback": {
      "en": "Structural control deficit in {lowest_subpillar_name} (maturity index {lowest_subpillar_score}/5.00), driving an expected annual loss allocation of {domain_eal} and requiring priority remediation.",
      "es": "Déficit estructural de control en {lowest_subpillar_name} (índice de madurez {lowest_subpillar_score}/5.00), generando una pérdida anual esperada de {domain_eal} que requiere remediación prioritaria."
    }
  }
  ```

### 2.2 Universal Archetype Token Schema

All narrative synthesizers must resolve tokens strictly from the runtime `TokenContext` data class:

| Token Key | Source Path in Runtime SSOT | Deterministic Fallback (If Omitted in Input) |
| :--- | :--- | :--- |
| `{client_name}` | `global_payload.metadata.client_name` | `"Enterprise Organization"` / `"Organización Empresarial"` |
| `{sector_name}` | `global_payload.metadata.industry_sector` | `"General Enterprise"` / `"Empresa General"` |
| `{facility_scope}` | `case_input.organization.facility_summary` | `"primary operational sites and distributed service delivery nodes"` |
| `{core_business_processes}` | `industry_profile.core_processes` | `"mission-critical transactional and operational workflows"` |
| `{inventory_summary}` | `tower_payload.inventory.summary` | `"core domain infrastructure, platform services, and control planes"` |
| `{annualized_exposure}` | `tower_payload.financials.eal_formatted` | Formatted `tower_payload.eal` in tenant currency |
| `{var_95_exposure}` | `tower_payload.financials.var_95_formatted` | Formatted `tower_payload.var_95` in tenant currency |
| `{maturity_score}` | `tower_payload.maturity_score` | `"2.50"` (formatted to 2 decimal places) |

---

## 3. Compiler Refactoring Blueprint (`tomo_asis_ast_compiler.py`)

This section provides the complete, production-ready refactoring of the consolidated AS-IS AST compiler. It eliminates the rigid 10-tower loop, removes all references to `tomo_tower_forensic_catalog`, and enforces penny-exact dynamic reconciliation across $N$ active domains.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class SubpillarDiagnostic:
    """Immutable representation of an evaluated domain subpillar."""
    code: str
    name: str
    score: float
    weight: float
    primary_finding: str


@dataclass(frozen=True)
class DomainForensicRecord:
    """Normalized, tenant-isolated forensic record for a single active domain."""
    domain_code: str
    domain_title: str
    archetype: str
    maturity_score: float
    risk_level: str
    eal_amount: Decimal
    var_95_amount: Decimal
    weight_pct: Decimal
    inventory_summary: str
    strengths: Tuple[str, ...]
    findings: Tuple[str, ...]
    subpillars: Tuple[SubpillarDiagnostic, ...]


class ActuarialDomainReconciler:
    """
    Guarantees closed-form penny-exact reconciliation across an arbitrary
    number of active domains (1..N) using the Largest Remainder Method.
    """

    @staticmethod
    def reconcile_allocations(
        total_amount: Decimal,
        raw_domain_weights: Mapping[str, Decimal],
        quantum: Decimal = Decimal("0.01"),
    ) -> Dict[str, Decimal]:
        if not raw_domain_weights:
            return {}

        weight_sum = sum(raw_domain_weights.values())
        if weight_sum <= Decimal("0"):
            equal_share = Decimal("1") / Decimal(len(raw_domain_weights))
            normalized = {k: equal_share for k in raw_domain_weights}
        else:
            normalized = {k: (v / weight_sum) for k, v in raw_domain_weights.items()}

        exact_allocations: Dict[str, Decimal] = {
            k: total_amount * w for k, w in normalized.items()
        }
        floored_allocations: Dict[str, Decimal] = {
            k: (val // quantum) * quantum for k, val in exact_allocations.items()
        }

        remainder_pool = total_amount - sum(floored_allocations.values())
        steps = int((remainder_pool / quantum).to_integral_value(rounding=ROUND_HALF_UP))

        remainders: List[Tuple[str, Decimal]] = sorted(
            ((k, exact_allocations[k] - floored_allocations[k]) for k in raw_domain_weights),
            key=lambda item: (item[1], item[0]),
            reverse=True,
        )

        for idx in range(max(0, steps)):
            target_key = remainders[idx % len(remainders)][0]
            floored_allocations[target_key] += quantum

        return floored_allocations


class TomoAsisASTCompilerRefactored:
    """
    Multi-tenant Consolidated AS-IS AST Compiler.
    Strictly binds to runtime `tower_payloads` and `global_payload` without
    reading static tenant snapshots from `locales.json`.
    """

    def __init__(
        self,
        global_payload: Mapping[str, Any],
        tower_payloads: Mapping[str, Mapping[str, Any]],
        locales_catalog: Mapping[str, Any],
        language: str = "en",
    ) -> None:
        self.global_payload = global_payload
        self.tower_payloads = tower_payloads
        self.locales = locales_catalog
        self.language = language if language in ("en", "es", "pt", "fr", "de", "ja") else "en"
        self.currency_code = str(
            global_payload.get("metadata", {}).get("currency", "USD")
        ).upper()
        self.sector_name = str(
            global_payload.get("metadata", {}).get("industry_sector", "General Enterprise")
        )

    def _tr(self, catalog_key: str, **kwargs: Any) -> str:
        """Resolves a localized template and interpolates dynamic runtime tokens."""
        entry = self.locales.get("forensic_domain_templates", {}).get(catalog_key, {})
        if isinstance(entry, Mapping):
            template = str(entry.get(self.language) or entry.get("en") or "")
        else:
            template = str(entry)
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    def _format_currency(self, amount: Decimal) -> str:
        """Formats monetary figures according to tenant currency and locale."""
        quantized = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        formatted_num = f"{int(quantized):,}"
        if self.language in ("es", "pt", "de", "fr"):
            formatted_num = formatted_num.replace(",", ".")
        return f"{formatted_num} {self.currency_code}"

    def _resolve_domain_topology(self) -> List[DomainForensicRecord]:
        """
        Dynamically discovers and normalizes active domains (1..N) from runtime SSOT.
        Completely eliminates the legacy hardcoded T1..T10 loop.
        """
        heatmap_entries: Sequence[Mapping[str, Any]] = self.global_payload.get("heatmap", [])
        heatmap_by_code: Dict[str, Mapping[str, Any]] = {
            str(entry.get("domain_code") or entry.get("tower_code") or entry.get("id")): entry
            for entry in heatmap_entries
            if entry.get("domain_code") or entry.get("tower_code") or entry.get("id")
        }

        # Discover active domain codes preserving input topological order
        active_codes: List[str] = []
        for code in heatmap_by_code:
            if code not in active_codes:
                active_codes.append(code)
        for code in self.tower_payloads:
            if code not in active_codes:
                active_codes.append(code)

        if not active_codes:
            raise ValueError("Cannot compile Consolidated AS-IS AST: Zero active domains in SSOT.")

        # Reconcile total EAL and VaR95 across active domains
        total_eal = Decimal(str(self.global_payload.get("financials", {}).get("total_eal", "0")))
        total_var95 = Decimal(str(self.global_payload.get("financials", {}).get("total_var_95", "0")))

        raw_weights: Dict[str, Decimal] = {}
        for code in active_codes:
            t_payload = self.tower_payloads.get(code, {})
            h_entry = heatmap_by_code.get(code, {})
            raw_eal = Decimal(
                str(
                    t_payload.get("financials", {}).get("eal")
                    or t_payload.get("eal")
                    or h_entry.get("eal")
                    or "1"
                )
            )
            raw_weights[code] = max(Decimal("0.0001"), raw_eal)

        if total_eal <= Decimal("0"):
            total_eal = sum(raw_weights.values())
        if total_var95 <= Decimal("0"):
            total_var95 = (total_eal * Decimal("2.35")).quantize(Decimal("0.01"))

        reconciled_eal = ActuarialDomainReconciler.reconcile_allocations(total_eal, raw_weights)
        reconciled_var95 = ActuarialDomainReconciler.reconcile_allocations(total_var95, raw_weights)
        reconciled_pct = ActuarialDomainReconciler.reconcile_allocations(
            Decimal("100.00"), raw_weights, quantum=Decimal("0.01")
        )

        records: List[DomainForensicRecord] = []
        for code in active_codes:
            t_payload = self.tower_payloads.get(code, {})
            h_entry = heatmap_by_code.get(code, {})

            title = str(
                t_payload.get("domain_title")
                or t_payload.get("tower_name")
                or h_entry.get("domain_title")
                or h_entry.get("name")
                or f"Domain {code}"
            )
            archetype = str(
                t_payload.get("archetype")
                or h_entry.get("archetype")
                or "COMPUTE_PLATFORMS"
            )
            maturity_score = float(
                t_payload.get("maturity_score")
                or h_entry.get("maturity_score")
                or 2.50
            )
            risk_level = str(
                t_payload.get("risk_level")
                or h_entry.get("risk_level")
                or ("HIGH" if maturity_score < 2.5 else "MEDIUM" if maturity_score < 3.5 else "LOW")
            )

            subpillars = self._extract_subpillars(code, title, maturity_score, t_payload)
            inventory_summary = self._extract_inventory(code, title, t_payload, len(subpillars))
            strengths = self._extract_strengths(code, title, t_payload, subpillars)
            findings = self._extract_findings(
                code, title, t_payload, subpillars, reconciled_eal[code]
            )

            records.append(
                DomainForensicRecord(
                    domain_code=code,
                    domain_title=title,
                    archetype=archetype,
                    maturity_score=round(maturity_score, 2),
                    risk_level=risk_level,
                    eal_amount=reconciled_eal[code],
                    var_95_amount=reconciled_var95[code],
                    weight_pct=reconciled_pct[code],
                    inventory_summary=inventory_summary,
                    strengths=strengths,
                    findings=findings,
                    subpillars=subpillars,
                )
            )

        return records

    def _extract_subpillars(
        self,
        domain_code: str,
        domain_title: str,
        domain_score: float,
        payload: Mapping[str, Any],
    ) -> Tuple[SubpillarDiagnostic, ...]:
        """Extracts evaluated subpillars from `payload.pillars_analysis`."""
        raw_pillars = payload.get("pillars_analysis") or payload.get("subpillars") or []
        extracted: List[SubpillarDiagnostic] = []

        if isinstance(raw_pillars, Mapping):
            iterable = [
                {"code": k, **(v if isinstance(v, Mapping) else {"score": v})}
                for k, v in raw_pillars.items()
            ]
        elif isinstance(raw_pillars, Sequence):
            iterable = list(raw_pillars)
        else:
            iterable = []

        for idx, item in enumerate(iterable, start=1):
            if not isinstance(item, Mapping):
                continue
            sp_code = str(item.get("code") or item.get("id") or f"{domain_code}.{idx}")
            sp_name = str(item.get("name") or item.get("title") or f"{domain_title} Control {idx}")
            sp_score = float(item.get("score") or item.get("maturity_score") or domain_score)
            sp_weight = float(item.get("weight") or (1.0 / max(1, len(iterable))))

            raw_findings = item.get("findings") or item.get("key_finding") or []
            if isinstance(raw_findings, Sequence) and not isinstance(raw_findings, str) and raw_findings:
                primary_finding = str(raw_findings[0])
            elif isinstance(raw_findings, str) and raw_findings.strip():
                primary_finding = raw_findings.strip()
            else:
                primary_finding = (
                    f"Control maturity evaluated at {sp_score:.2f}/5.00 under {self.sector_name} benchmark."
                )

            extracted.append(
                SubpillarDiagnostic(
                    code=sp_code,
                    name=sp_name,
                    score=round(sp_score, 2),
                    weight=round(sp_weight, 4),
                    primary_finding=primary_finding,
                )
            )

        if not extracted:
            # Deterministic structural fallback derived purely from domain score
            extracted.append(
                SubpillarDiagnostic(
                    code=f"{domain_code}.1",
                    name=f"{domain_title} Core Controls",
                    score=round(domain_score, 2),
                    weight=1.0,
                    primary_finding=f"Aggregate domain control baseline measured at {domain_score:.2f}/5.00.",
                )
            )

        return tuple(extracted)

    def _extract_inventory(
        self,
        domain_code: str,
        domain_title: str,
        payload: Mapping[str, Any],
        subpillar_count: int,
    ) -> str:
        """Extracts dynamic asset inventory from payload without static catalog fallback."""
        raw_inv = payload.get("inventory") or payload.get("asset_inventory")
        if isinstance(raw_inv, str) and raw_inv.strip():
            return raw_inv.strip()
        if isinstance(raw_inv, Mapping):
            summary = raw_inv.get("summary") or raw_inv.get("description")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()
            items = raw_inv.get("items") or raw_inv.get("assets")
            if isinstance(items, Sequence) and items:
                return ", ".join(str(x) for x in items[:8])
        if isinstance(raw_inv, Sequence) and raw_inv:
            return ", ".join(str(x) for x in raw_inv[:8])

        return self._tr(
            "inventory_fallback",
            domain_code=domain_code,
            domain_title=domain_title,
            subpillar_count=subpillar_count,
            sector_name=self.sector_name,
        )

    def _extract_strengths(
        self,
        domain_code: str,
        domain_title: str,
        payload: Mapping[str, Any],
        subpillars: Sequence[SubpillarDiagnostic],
    ) -> Tuple[str, ...]:
        """Extracts validated domain strengths or synthesizes from highest-scoring subpillars."""
        raw_strengths = payload.get("strengths") or payload.get("operational_strengths")
        if isinstance(raw_strengths, Sequence) and not isinstance(raw_strengths, str):
            cleaned = [str(s).strip() for s in raw_strengths if str(s).strip()]
            if cleaned:
                return tuple(cleaned[:4])

        highest = max(subpillars, key=lambda sp: sp.score)
        fallback = self._tr(
            "strength_fallback",
            domain_code=domain_code,
            domain_title=domain_title,
            highest_subpillar_name=highest.name,
            highest_subpillar_score=f"{highest.score:.2f}",
        )
        return (fallback,)

    def _extract_findings(
        self,
        domain_code: str,
        domain_title: str,
        payload: Mapping[str, Any],
        subpillars: Sequence[SubpillarDiagnostic],
        domain_eal: Decimal,
    ) -> Tuple[str, ...]:
        """Extracts forensic findings from payload or synthesizes from lowest-scoring subpillars."""
        raw_findings = payload.get("findings") or payload.get("forensic_findings")
        if isinstance(raw_findings, Sequence) and not isinstance(raw_findings, str):
            cleaned = []
            for item in raw_findings:
                if isinstance(item, Mapping):
                    text = item.get("description") or item.get("title") or item.get("finding")
                    if text:
                        cleaned.append(str(text).strip())
                elif str(item).strip():
                    cleaned.append(str(item).strip())
            if cleaned:
                return tuple(cleaned[:5])

        lowest = min(subpillars, key=lambda sp: sp.score)
        fallback = self._tr(
            "finding_fallback",
            domain_code=domain_code,
            domain_title=domain_title,
            lowest_subpillar_name=lowest.name,
            lowest_subpillar_score=f"{lowest.score:.2f}",
            domain_eal=self._format_currency(domain_eal),
        )
        return (fallback,)

    def _build_chapter_4_forensic_domains(self) -> List[Dict[str, Any]]:
        """
        Builds the Chapter 4 AST node tree strictly from live `tower_payloads`.
        Zero dependency on `tomo_tower_forensic_catalog`.
        """
        domain_records = self._resolve_domain_topology()
        ast_nodes: List[Dict[str, Any]] = []

        for record in domain_records:
            ast_nodes.append(
                {
                    "node_type": "ForensicDomainSection",
                    "domain_code": record.domain_code,
                    "domain_title": record.domain_title,
                    "archetype": record.archetype,
                    "metrics": {
                        "maturity_score": f"{record.maturity_score:.2f}/5.00",
                        "risk_level": record.risk_level,
                        "eal_formatted": self._format_currency(record.eal_amount),
                        "var_95_formatted": self._format_currency(record.var_95_amount),
                        "portfolio_Share_pct": f"{record.weight_pct:.2f}%",
                    },
                    "inventory_block": {
                        "node_type": "Paragraph",
                        "style": "ForensicInventoryBody",
                        "text": record.inventory_summary,
                    },
                    "strengths_list": [
                        {"node_type": "BulletItem", "text": s} for s in record.strengths
                    ],
                    "findings_list": [
                        {"node_type": "BulletItem", "text": f} for f in record.findings
                    ],
                    "subpillars_table": {
                        "node_type": "Table",
                        "style": "ForensicSubpillarGrid",
                        "columns": ["Code", "Subpillar", "Maturity", "Weight", "Primary Diagnostic"],
                        "rows": [
                            [
                                sp.code,
                                sp.name,
                                f"{sp.score:.2f}",
                                f"{sp.weight * 100:.1f}%",
                                sp.primary_finding,
                            ]
                            for sp in record.subpillars
                        ],
                    },
                }
            )

        return ast_nodes
```

---

## 4. Per-Tower Narrative Synthesizer Remediation (`payload_to_ast.py`)

In `payload_to_ast.py`, `ExecutiveNarrativeSynthesizer.synthesize_chapter_one_paragraphs` previously branched on `INFRASTRUCTURE_PHYSICAL` to inject hardcoded cement plant, weighbridge, and HPE SimpliVity narratives for towers `T1`, `T4`, and `T5`.

### 4.1 Refactored Sector-Aware Archetype Synthesizer

```python
from decimal import Decimal
from typing import Any, Dict, List, Mapping


class IndustryProfileRegistry:
    """Provides sector-specific operational terminology without tenant contamination."""

    PROFILES: Mapping[str, Mapping[str, Mapping[str, str]]] = {
        "BANKING": {
            "en": {
                "facility_scope": "core banking data centers, clearing gateways, and branch distribution channels",
                "core_business_processes": "real-time payment settlement, ledger reconciliation, and regulatory liquidity reporting",
            },
            "es": {
                "facility_scope": "centros de datos de core bancario, pasarelas de compensación y canales de distribución",
                "core_business_processes": "liquidación de pagos en tiempo real, conciliación contable y reportes regulatorios de liquidez",
            },
        },
        "HEALTHCARE": {
            "en": {
                "facility_scope": "clinical hospital campuses, diagnostic imaging networks, and EHR hosting tiers",
                "core_business_processes": "electronic health record access, clinical telemetry, and pharmacy dispensation workflows",
            },
            "es": {
                "facility_scope": "campus hospitalarios clínicos, redes de diagnóstico por imagen y niveles de alojamiento HCE",
                "core_business_processes": "acceso a historias clínicas electrónicas, telemetría clínica y flujos de dispensación farmacéutica",
            },
        },
        "RETAIL": {
            "en": {
                "facility_scope": "omnichannel e-commerce clusters, POS networks, and automated fulfillment centers",
                "core_business_processes": "point-of-sale checkout authorization, inventory synchronization, and warehouse dispatch",
            },
            "es": {
                "facility_scope": "clústeres de comercio electrónico omnicanal, redes POS y centros logísticos automatizados",
                "core_business_processes": "autorización de cobro en punto de venta, sincronización de inventario y despacho logístico",
            },
        },
        "GENERAL_ENTERPRISE": {
            "en": {
                "facility_scope": "primary enterprise facilities, cloud landing zones, and distributed operational nodes",
                "core_business_processes": "mission-critical transactional workflows, enterprise resource planning, and service delivery",
            },
            "es": {
                "facility_scope": "instalaciones empresariales principales, zonas de aterrizaje cloud y nodos operativos distribuidos",
                "core_business_processes": "flujos transaccionales críticos, planificación de recursos empresariales y entrega de servicios",
            },
        },
    }

    @classmethod
    def resolve_context(
        cls,
        sector_key: str,
        language: str,
        case_overrides: Mapping[str, Any],
    ) -> Dict[str, str]:
        normalized_sector = sector_key.upper().replace(" ", "_")
        profile = cls.PROFILES.get(normalized_sector, cls.PROFILES["GENERAL_ENTERPRISE"])
        lang_bundle = profile.get(language, profile["en"])

        return {
            "facility_scope": str(
                case_overrides.get("facility_summary") or lang_bundle["facility_scope"]
            ),
            "core_business_processes": str(
                case_overrides.get("core_workloads") or lang_bundle["core_business_processes"]
            ),
        }


class ExecutiveNarrativeSynthesizer:
    """
    Synthesizes Chapter 1 executive narratives dynamically using the domain
    archetype, live actuarial metrics, and sector-aware operational context.
    """

    ARCHETYPE_TEMPLATE_KEYS: Mapping[str, str] = {
        "INFRASTRUCTURE_PHYSICAL": "archetype_infrastructure_physical",
        "COMPUTE_PLATFORMS": "archetype_compute_platforms",
        "SECURITY_GOVERNANCE": "archetype_security_governance",
        "DATA_APPLICATIONS": "archetype_data_applications",
    }

    @classmethod
    def synthesize_chapter_one_paragraphs(
        cls,
        tower_payload: Mapping[str, Any],
        global_metadata: Mapping[str, Any],
        locales_catalog: Mapping[str, Any],
        language: str = "en",
    ) -> List[str]:
        archetype = str(tower_payload.get("archetype", "COMPUTE_PLATFORMS")).upper()
        template_key = cls.ARCHETYPE_TEMPLATE_KEYS.get(
            archetype, "archetype_compute_platforms"
        )

        sector_key = str(global_metadata.get("industry_sector", "GENERAL_ENTERPRISE"))
        sector_ctx = IndustryProfileRegistry.resolve_context(
            sector_key=sector_key,
            language=language,
            case_overrides=global_metadata.get("organization_context", {}),
        )

        domain_title = str(
            tower_payload.get("domain_title")
            or tower_payload.get("tower_name")
            or tower_payload.get("domain_code")
            or "Evaluated Domain"
        )
        maturity_score = float(tower_payload.get("maturity_score", 2.50))
        currency = str(global_metadata.get("currency", "USD")).upper()

        eal_val = Decimal(str(tower_payload.get("financials", {}).get("eal", "0")))
        var95_val = Decimal(str(tower_payload.get("financials", {}).get("var_95", "0")))

        inventory_raw = tower_payload.get("inventory")
        if isinstance(inventory_raw, Mapping) and inventory_raw.get("summary"):
            inventory_summary = str(inventory_raw["summary"])
        elif isinstance(inventory_raw, str) and inventory_raw.strip():
            inventory_summary = inventory_raw.strip()
        else:
            inventory_summary = (
                f"scoped {domain_title} technological assets and control infrastructure"
            )

        tokens = {
            "domain_title": domain_title,
            "inventory_summary": inventory_summary,
            "facility_scope": sector_ctx["facility_scope"],
            "core_business_processes": sector_ctx["core_business_processes"],
            "annualized_exposure": f"{int(eal_val):,} {currency}",
            "var_95_exposure": f"{int(var95_val):,} {currency}",
            "maturity_score": f"{maturity_score:.2f}",
        }

        template_bundle = locales_catalog.get(template_key, {})
        raw_template = str(
            template_bundle.get(language)
            or template_bundle.get("en")
            or (
                "Within {domain_title}, critical operational dependencies center on "
                "{inventory_summary} across {facility_scope}, impacting {core_business_processes}. "
                "Annualized risk exposure reaches {annualized_exposure} (95% VaR: {var_95_exposure}) "
                "at a maturity index of {maturity_score}/5.00."
            )
        )

        return [raw_template.format(**tokens)]
```

---

## 5. Multi-Tenant Verification & Zero-Leak Quality Gate

To mathematically and forensically prove that zero single-tenant bias remains, the CI/CD pipeline enforces the following automated test suite (`tests/test_rfc071_multitenant_isolation.py`).

### 5.1 Automated Forensic Verification Suite

```python
import json
import pytest
from decimal import Decimal
from typing import Any, Dict

# Forbidden single-tenant contamination literals (Case-Insensitive)
FORBIDDEN_CONTAMINATION_LITERALS = (
    "sant vicenç",
    "hort",
    "secil",
    "molins",
    "simplivity",
    "netapp",
    "báscula",
    "bascula",
    "weighbridge",
    "ensacado",
    "bagging",
    "5.000 eur/h",
    "5,000 eur/h",
    "mayo 2027",
    "may 2027",
    "18 países",
    "18 countries",
)


def assert_zero_contamination(serialized_ast: str) -> None:
    lowered = serialized_ast.lower()
    leaked = [token for token in FORBIDDEN_CONTAMINATION_LITERALS if token in lowered]
    assert not leaked, f"CRITICAL TENANT LEAK DETECTED in AST: {leaked}"


def test_3_domain_tokyo_fintech_bank_jpy() -> None:
    """
    Verifies that a 3-domain Japanese FinTech Bank assessment in JPY:
    1. Renders exactly 3 domains in Chapter 4 (no phantom T4..T10).
    2. Binds 100% to live banking inventory and findings.
    3. Reconciles JPY EAL penny-exact across the 3 domains.
    4. Contains zero cement/Catalonia contamination literals.
    """
    global_payload: Dict[str, Any] = {
        "metadata": {
            "client_name": "Tokyo FinTech Bank Corp",
            "industry_sector": "BANKING",
            "currency": "JPY",
        },
        "financials": {
            "total_eal": "450000000",
            "total_var_95": "1120000000",
        },
        "heatmap": [
            {"domain_code": "DOM_CLOUD", "domain_title": "Core Cloud Ledger", "maturity_score": 2.15, "eal": "200000000"},
            {"domain_code": "DOM_CYBER", "domain_title": "Zero-Trust & Payment Security", "maturity_score": 1.85, "eal": "150000000"},
            {"domain_code": "DOM_DATA", "domain_title": "Real-Time Settlement Data", "maturity_score": 2.90, "eal": "100000000"},
        ],
    }

    tower_payloads: Dict[str, Dict[str, Any]] = {
        "DOM_CLOUD": {
            "domain_title": "Core Cloud Ledger",
            "archetype": "COMPUTE_PLATFORMS",
            "maturity_score": 2.15,
            "inventory": "Multi-region Kubernetes payment clusters across Tokyo and Osaka availability zones",
            "strengths": ["Automated container image signing in CI/CD"],
            "findings": ["Single-region state lock dependency on primary Tokyo transit gateway"],
            "pillars_analysis": [
                {"code": "CLD.1", "name": "Multi-AZ Resilience", "score": 1.90, "weight": 0.6, "findings": ["Cross-region failover exceeds 15-minute BOJ RPO target"]},
                {"code": "CLD.2", "name": "Immutable Infrastructure", "score": 2.50, "weight": 0.4, "findings": ["Manual drift remediation in production namespaces"]},
            ],
        },
        "DOM_CYBER": {
            "domain_title": "Zero-Trust & Payment Security",
            "archetype": "SECURITY_GOVERNANCE",
            "maturity_score": 1.85,
            "inventory": "HSM payment encryption modules, SWIFT gateway firewalls, and privileged PAM vaults",
            "strengths": ["Hardware-backed FIPS 140-3 Level 3 key rotation"],
            "findings": ["Incomplete micro-segmentation between SWIFT messaging zone and internal API gateway"],
            "pillars_analysis": [
                {"code": "CYB.1", "name": "Cryptographic Key Custody", "score": 1.85, "weight": 1.0, "findings": ["HSM quorum ceremonies lack automated dual-custody telemetry"]},
            ],
        },
        "DOM_DATA": {
            "domain_title": "Real-Time Settlement Data",
            "archetype": "DATA_APPLICATIONS",
            "maturity_score": 2.90,
            "inventory": "Distributed CockroachDB settlement ledgers and Kafka event streaming backbones",
            "strengths": ["Synchronous raft consensus across 3 metropolitan nodes"],
            "findings": ["Absence of automated schema-registry poison-pill quarantine"],
            "pillars_analysis": [
                {"code": "DAT.1", "name": "Transactional Integrity", "score": 2.90, "weight": 1.0, "findings": ["Dead-letter replay requires manual DBA intervention"]},
            ],
        },
    }

    compiler = TomoAsisASTCompilerRefactored(
        global_payload=global_payload,
        tower_payloads=tower_payloads,
        locales_catalog={},
        language="en",
    )

    ch4_nodes = compiler._build_chapter_4_forensic_domains()
    serialized = json.dumps(ch4_nodes, ensure_ascii=False)

    # Gate 1: Exact domain topology count (3 domains, no T1..T10 padding)
    assert len(ch4_nodes) == 3
    assert [n["domain_code"] for n in ch4_nodes] == ["DOM_CLOUD", "DOM_CYBER", "DOM_DATA"]

    # Gate 2: Dynamic SSOT binding verification
    assert "Tokyo and Osaka availability zones" in serialized
    assert "SWIFT gateway firewalls" in serialized
    assert "CockroachDB settlement ledgers" in serialized

    # Gate 3: Zero single-tenant contamination
    assert_zero_contamination(serialized)

    # Gate 4: Closed-form actuarial reconciliation (Sum == 100.00% and 450,000,000 JPY)
    records = compiler._resolve_domain_topology()
    assert sum(r.eal_amount for r in records) == Decimal("450000000.00")
    assert sum(r.weight_pct for r in records) == Decimal("100.00")
```

### 5.2 Summary of Architectural Guarantees Delivered
1. **Complete Eradication of Catalog Pollution:** `engine_config/locales.json` is stripped of all proper nouns, cities, vendors, contract dates, and manufacturing equipment.
2. **Elimination of Split-Brain Compilation:** `TomoAsisASTCompiler` binds 100% to `tower_payloads` and `global_payload`, ensuring every client's real inventory, strengths, findings, and subpillar scores render faithfully in Chapter 4.
3. **Elastic $N$-Domain Topology:** `_resolve_domain_topology` scales seamlessly from 1 domain to $N$ custom domains without injecting phantom towers.
4. **Closed-Form Financial Integrity:** `ActuarialDomainReconciler` enforces penny-exact Largest Remainder reconciliation across any arbitrary domain count and currency.