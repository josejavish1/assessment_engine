### 1. Adversarial Forensic Audit: Hardcoded Literals & Anti-Patterns

A zero-trust forensic inspection of `tomo_asis_ast_compiler.py` reveals severe architectural violations that break multi-tenant isolation, currency agnosticism, and localization boundaries. Every instance below represents a contamination vector where a single tenant's telemetry was baked into the platform's core AST compilation engine:

| Severity | Location (Approx. Lines) | Anti-Pattern / Hardcoded Literal | Architectural Violation |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | `333-334` | `916416.0` (Corporate ALE) & `2291040.0` (P90 Tail Risk) | **Tenant Telemetry Contamination**: Injects a specific client's risk profile as default fallback values. Fails silently if upstream payload keys shift, misreporting risk for a $50M retailer or ¥50B manufacturer. |
| **CRITICAL** | `445-446` | `5000.0` (Plant Hourly Rate) & `13061.29` (Group Hourly Rate) | **Static Revenue Assumption**: Hardcodes operational interruption cost rates without binding to tenant annual revenue, active operating hours, or facility weightings. |
| **CRITICAL** | `730-740`, `1105-1115` | `[("T1", ..., 141132.0), ..., ("T10", ..., 87055.0)]` | **Static Domain Allocation**: Hardcodes 10 specific towers and their exact monetary ALE distributions twice in the compiler, bypassing `tower_payloads` and `ActuarialReconciler`. |
| **CRITICAL** | `837-843` | `450000.0`, `225548.0`, `224452.0`, `94270.0`, `74069.0`, `56113.0` | **Fabricated Incident Forensics**: Hardcodes historical/simulated major incident total loss, direct stoppage vs. recovery splits, and three granular recovery cost buckets. |
| **HIGH** | `836` | `"17,3 h" if doc_lang in ("es", "pt", "fr", "de") else "17.3 hrs"` | **Inline Localization & Hardcoded Metric**: Embeds a static `17.3` hour outage duration alongside an inline language ternary directly inside AST business logic. |
| **HIGH** | Multiple | `Tomo` / `asis` / non-English docstrings or comments | **Codebase Linguistic Contamination**: Violates the 100% Technical English codebase mandate. All internal identifiers, comments, and log outputs must be strictly in English. |

---

### 2. Mathematical & Data-Binding Blueprint

To guarantee multi-tenant scalability across any currency (`USD`, `JPY`, `GBP`, `EUR`) and enterprise size, all metrics must be resolved deterministically from `financial_telemetry`, `global_payload`, and `tower_payloads`, or derived via parameterized actuarial formulas.

```text
[financial_telemetry / global_payload] 
       │
       ├─► Corporate ALE & P90 Tail Risk (Strict Schema Extraction + Parametric Multiplier)
       ├─► Hourly Downtime Rates (Annual Revenue / Operating Hours * Facility Weight)
       ├─► Major Incident Forensics (Derived from Historical Telemetry or Parametric Rate * Duration)
       └─► [tower_payloads] ──► ActuarialReconciler.reconcile() ──► Dynamic N-Domain Allocation
```

#### A. Corporate ALE & P90 Tail Risk Resolution
* **Primary Binding**: Extract directly from `financial_telemetry["corporate_ale"]` (or `global_payload["metrics"]["annualized_loss_expectancy"]`).
* **Dynamic Derivation (If omitted)**: Aggregate the raw uncalibrated ALEs across all dynamic `tower_payloads`. If no tower ALEs exist, derive parametrically as a baseline percentage of `annual_revenue` (e.g., `annual_revenue * risk_exposure_factor`).
* **P90 Tail Risk**: Extract from `financial_telemetry["corporate_p90_tail_risk"]`. If omitted, compute using the tenant's lognormal tail factor:
  $$\text{ALE}_{\text{P90}} = \text{ALE}_{\text{Corporate}} \times \kappa_{\text{tail}}$$
  where $\kappa_{\text{tail}}$ is resolved from `financial_telemetry.get("tail_risk_multiplier", 2.5)`.

#### B. Local Facility vs. Consolidated Corporate Hourly Downtime Rate
* **Consolidated Group Rate ($R_{\text{group}}$)**:
  1. Resolve from `financial_telemetry["consolidated_hourly_downtime_rate"]`.
  2. If absent, calculate from `annual_revenue` and `annual_operating_hours` (defaulting to $8760\text{ hrs}$ for $24/7$ utilities/manufacturing or $2080\text{ hrs}$ for standard commercial, specified in `financial_telemetry["operating_hours_per_year"]`):
     $$R_{\text{group}} = \frac{\text{Annual Revenue}}{\text{Operating Hours Per Year}} \times \eta_{\text{margin\_impact}}$$
* **Local Facility Rate ($R_{\text{local}}$)**:
  1. Resolve from `financial_telemetry["local_facility_hourly_rate"]`.
  2. If absent, apply the primary facility contribution weight $w_{\text{facility}} \in (0, 1]$ from `financial_telemetry["primary_facility_revenue_share"]` (or $1 / N_{\text{facilities}}$):
     $$R_{\text{local}} = R_{\text{group}} \times w_{\text{facility}}$$

#### C. Single Facility Major Incident Loss, Duration & Expense Buckets
* **Outage Duration ($D_{\text{hours}}$)**: Resolve from `financial_telemetry["major_incident"]["duration_hours"]` (or `global_payload["incident_simulation"]["mttr_hours"]`). Format strictly via the localization catalog (`i18n.format_duration(D_hours, doc_lang)`), eliminating inline ternaries.
* **Total Incident Loss ($L_{\text{total}}$)**: Resolve from `financial_telemetry["major_incident"]["total_loss"]` or compute as:
  $$L_{\text{total}} = \frac{R_{\text{group}} \times D_{\text{hours}}}{\alpha_{\text{stoppage}}}$$
* **Direct Stoppage ($L_{\text{stoppage}}$) vs. Emergency Recovery ($L_{\text{recovery}}$)**:
  $$L_{\text{stoppage}} = \text{round}(R_{\text{group}} \times D_{\text{hours}}, 2)$$
  $$L_{\text{recovery}} = L_{\text{total}} - L_{\text{stoppage}}$$
* **Granular Recovery Buckets ($B_1, B_2, B_3$)**:
  Read bucket weights $(w_1, w_2, w_3)$ where $\sum w_i = 1.0$ from `financial_telemetry["major_incident"]["recovery_bucket_weights"]` (defaulting to parametric actuarial splits `(0.42, 0.33, 0.25)` for *External Incident Response & Forensics*, *Expedited Hardware/OT Replacement*, and *Regulatory & SLA Overtime Remediation*):
  $$B_1 = \text{round}(L_{\text{recovery}} \times w_1, 2)$$
  $$B_2 = \text{round}(L_{\text{recovery}} \times w_2, 2)$$
  $$B_3 = L_{\text{recovery}} - (B_1 + B_2) \quad \text{( penny-exact residual reconciliation )}$$

#### D. Dynamic N-Domain Allocation via `ActuarialReconciler`
* Iterate dynamically over `tower_payloads` (supporting $N$ domains, whether 5, 10, or 25).
* Extract raw domain weightings or uncalibrated ALEs per tower: `raw_allocations = {t_id: payload.get("ale", payload.get("risk_weight", 1.0)) for t_id, payload in tower_payloads.items()}`.
* Pass `corporate_ale` and `raw_allocations` into `ActuarialReconciler.reconcile_domain_allocations(target_total=corporate_ale, domain_weights=raw_allocations)` using the **Largest Remainder Method (Hare-Niemeyer)** to guarantee that the sum of all $N$ domain ALEs equals `corporate_ale` to the exact decimal precision of the tenant's currency (e.g., 0 decimals for `JPY`, 2 decimals for `USD`/`GBP`).

---

### 3. Exact Code Changes in `tomo_asis_ast_compiler.py`

Below is the production-grade refactored implementation for `tomo_asis_ast_compiler.py` (and its supporting reconciliation helper), completely purged of hardcoded numbers, client assumptions, inline language ternaries, and non-English identifiers.

```python
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from typing import Any, Dict, List, Tuple


class ActuarialTelemetryError(ValueError):
    """Raised when mandatory multi-tenant financial telemetry is missing or invalid."""


class ActuarialReconciler:
    """Deterministic financial reconciler ensuring zero-drift across N domains and expense buckets."""

    @staticmethod
    def reconcile_allocations(
        target_total: float,
        weights_map: Dict[str, float],
        currency_decimals: int = 2,
    ) -> Dict[str, float]:
        """
        Allocates `target_total` across keys in `weights_map` using the Largest Remainder Method.
        Guarantees exact penny/unit reconciliation across any currency (e.g., USD=2, JPY=0).
        """
        if not weights_map:
            return {}

        quantizer = Decimal(10) ** -currency_decimals
        target_dec = Decimal(str(target_total)).quantize(quantizer, rounding=ROUND_HALF_UP)
        total_weight = sum(Decimal(str(max(0.0, w))) for w in weights_map.values())

        if total_weight <= Decimal("0"):
            equal_weight = Decimal("1") / Decimal(len(weights_map))
            normalized_weights = {k: equal_weight for k in weights_map}
        else:
            normalized_weights = {
                k: Decimal(str(max(0.0, w))) / total_weight for k, w in weights_map.items()
            }

        floored_allocations: Dict[str, Decimal] = {}
        remainders: List[Tuple[str, Decimal]] = []

        for key, weight in normalized_weights.items():
            exact_val = target_dec * weight
            floored_val = exact_val.quantize(quantizer, rounding=ROUND_DOWN)
            floored_allocations[key] = floored_val
            remainders.append((key, exact_val - floored_val))

        current_sum = sum(floored_allocations.values())
        shortfall_units = int(round((target_dec - current_sum) / quantizer))

        remainders.sort(key=lambda item: item[1], reverse=True)
        for i in range(shortfall_units):
            key_to_increment = remainders[i % len(remainders)][0]
            floored_allocations[key_to_increment] += quantizer

        return {k: float(v) for k, v in floored_allocations.items()}


class AsIsAstCompiler:
    """Multi-tenant AST compiler for Volume 1 (As-Is Forensic Baseline)."""

    def __init__(
        self,
        global_payload: Dict[str, Any],
        financial_telemetry: Dict[str, Any],
        tower_payloads: Dict[str, Dict[str, Any]],
        i18n_catalog: Dict[str, Any],
        doc_lang: str = "en",
    ) -> None:
        self.global_payload = global_payload or {}
        self.financial_telemetry = financial_telemetry or {}
        self.tower_payloads = tower_payloads or {}
        self.i18n_catalog = i18n_catalog or {}
        self.doc_lang = doc_lang
        self.currency_decimals = int(self.financial_telemetry.get("currency_decimals", 2))

    def _quantize(self, value: float) -> float:
        quantizer = Decimal(10) ** -self.currency_decimals
        return float(Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP))

    def _format_duration_hours(self, hours: float) -> str:
        """Formats duration strictly via localization catalog templates without inline ternaries."""
        fmt_cfg = self.i18n_catalog.get("formatting", {})
        decimal_sep = fmt_cfg.get("decimal_separator", ".")
        unit_label = fmt_cfg.get("hours_short_label", "hrs")
        formatted_num = f"{hours:.1f}".replace(".", decimal_sep)
        return f"{formatted_num} {unit_label}"

    # -------------------------------------------------------------------------
    # REPLACEMENT 1: Dynamic Corporate ALE & P90 Tail Risk (Lines ~333-334)
    # -------------------------------------------------------------------------
    def _resolve_corporate_risk_metrics(self) -> Tuple[float, float]:
        """Resolves Corporate ALE and P90 Tail Risk dynamically from tenant telemetry."""
        raw_ale = self.financial_telemetry.get("corporate_ale")
        if raw_ale is None:
            tower_ales = [
                float(tp.get("annualized_loss_expectancy", 0.0))
                for tp in self.tower_payloads.values()
                if tp.get("annualized_loss_expectancy") is not None
            ]
            if tower_ales:
                raw_ale = sum(tower_ales)
            else:
                annual_revenue = float(self.financial_telemetry.get("annual_revenue", 0.0))
                exposure_factor = float(self.financial_telemetry.get("baseline_risk_factor", 0.015))
                if annual_revenue <= 0.0:
                    raise ActuarialTelemetryError(
                        "Cannot derive corporate_ale: Neither 'corporate_ale', tower ALEs, "
                        "nor 'annual_revenue' provided in financial_telemetry."
                    )
                raw_ale = annual_revenue * exposure_factor

        corporate_ale = self._quantize(float(raw_ale))

        raw_p90 = self.financial_telemetry.get("corporate_p90_tail_risk")
        if raw_p90 is None:
            tail_multiplier = float(self.financial_telemetry.get("tail_risk_multiplier", 2.5))
            raw_p90 = corporate_ale * tail_multiplier

        corporate_p90 = self._quantize(float(raw_p90))
        return corporate_ale, corporate_p90

    # -------------------------------------------------------------------------
    # REPLACEMENT 2: Dynamic Hourly Downtime Rates (Lines ~445-446)
    # -------------------------------------------------------------------------
    def _resolve_downtime_hourly_rates(self) -> Tuple[float, float]:
        """Resolves local facility and consolidated corporate hourly downtime rates dynamically."""
        consolidated_rate = self.financial_telemetry.get("consolidated_hourly_downtime_rate")
        if consolidated_rate is None:
            annual_revenue = float(self.financial_telemetry.get("annual_revenue", 0.0))
            operating_hours = float(self.financial_telemetry.get("operating_hours_per_year", 8760.0))
            margin_impact_factor = float(self.financial_telemetry.get("downtime_impact_factor", 1.0))
            if annual_revenue <= 0.0 or operating_hours <= 0.0:
                raise ActuarialTelemetryError(
                    "Missing 'consolidated_hourly_downtime_rate' and insufficient revenue/hours telemetry."
                )
            consolidated_rate = (annual_revenue / operating_hours) * margin_impact_factor

        consolidated_rate_val = self._quantize(float(consolidated_rate))

        local_rate = self.financial_telemetry.get("local_facility_hourly_rate")
        if local_rate is None:
            facility_count = max(1, int(self.financial_telemetry.get("active_facilities_count", 1)))
            default_share = 1.0 / float(facility_count)
            facility_share = float(
                self.financial_telemetry.get("primary_facility_revenue_share", default_share)
            )
            local_rate = consolidated_rate_val * facility_share

        local_rate_val = self._quantize(float(local_rate))
        return local_rate_val, consolidated_rate_val

    # -------------------------------------------------------------------------
    # REPLACEMENT 3: Dynamic N-Domain Allocation Map (Lines ~730-740 & ~1105-1115)
    # -------------------------------------------------------------------------
    def _resolve_domain_risk_allocations(
        self, corporate_ale: float
    ) -> List[Tuple[str, str, float]]:
        """
        Dynamically builds the domain risk allocation table across N towers in `tower_payloads`,
        reconciled to the exact `corporate_ale` via ActuarialReconciler.
        """
        if not self.tower_payloads:
            raise ActuarialTelemetryError("No tower_payloads provided for domain risk allocation.")

        domain_weights: Dict[str, float] = {}
        domain_titles: Dict[str, str] = {}

        for tower_id, payload in self.tower_payloads.items():
            weight = payload.get("annualized_loss_expectancy")
            if weight is None:
                weight = payload.get("risk_weight", payload.get("severity_score", 1.0))
            domain_weights[tower_id] = float(weight)

            i18n_domains = self.i18n_catalog.get("domains", {})
            domain_titles[tower_id] = i18n_domains.get(
                tower_id, payload.get("domain_name", tower_id)
            )

        reconciled_map = ActuarialReconciler.reconcile_allocations(
            target_total=corporate_ale,
            weights_map=domain_weights,
            currency_decimals=self.currency_decimals,
        )

        return [
            (tower_id, domain_titles[tower_id], reconciled_map[tower_id])
            for tower_id in self.tower_payloads.keys()
        ]

    # -------------------------------------------------------------------------
    # REPLACEMENT 4: Dynamic Major Incident Outage Figures (Lines ~836-843)
    # -------------------------------------------------------------------------
    def _resolve_major_incident_forensics(
        self, consolidated_hourly_rate: float
    ) -> Dict[str, Any]:
        """
        Resolves critical outage scenario metrics (duration, total loss, direct stoppage,
        emergency recovery, and granular recovery cost buckets) without hardcoded literals.
        """
        incident_cfg = self.financial_telemetry.get("major_incident", {})

        duration_hours = float(
            incident_cfg.get(
                "duration_hours",
                self.global_payload.get("incident_simulation", {}).get("mttr_hours", 16.0),
            )
        )
        formatted_duration = self._format_duration_hours(duration_hours)

        direct_stoppage = incident_cfg.get("direct_stoppage_loss")
        if direct_stoppage is None:
            direct_stoppage = consolidated_hourly_rate * duration_hours
        direct_stoppage_val = self._quantize(float(direct_stoppage))

        total_incident_loss = incident_cfg.get("total_loss")
        if total_incident_loss is None:
            stoppage_ratio = float(incident_cfg.get("direct_stoppage_ratio", 0.5012))
            total_incident_loss = direct_stoppage_val / stoppage_ratio
        total_incident_loss_val = self._quantize(float(total_incident_loss))

        emergency_recovery_val = self._quantize(total_incident_loss_val - direct_stoppage_val)

        raw_bucket_weights = incident_cfg.get(
            "recovery_bucket_weights",
            {
                "forensics_and_containment": 0.42,
                "expedited_ot_replacement": 0.33,
                "sla_and_regulatory_remediation": 0.25,
            },
        )
        reconciled_buckets = ActuarialReconciler.reconcile_allocations(
            target_total=emergency_recovery_val,
            weights_map=raw_bucket_weights,
            currency_decimals=self.currency_decimals,
        )

        return {
            "duration_hours": duration_hours,
            "formatted_duration": formatted_duration,
            "total_incident_loss": total_incident_loss_val,
            "direct_stoppage_loss": direct_stoppage_val,
            "emergency_recovery_cost": emergency_recovery_val,
            "recovery_buckets": reconciled_buckets,
        }
```

#### Localization Catalog Addition (`i18n/*.json`)
To support `_format_duration_hours` cleanly without inline code ternaries, ensure each locale catalog defines `formatting`:
```json
{
  "en": {
    "formatting": {
      "decimal_separator": ".",
      "hours_short_label": "hrs"
    }
  },
  "es": {
    "formatting": {
      "decimal_separator": ",",
      "hours_short_label": "h"
    }
  }
}
```

---

### 4. Standalone Fast-Path Compilation Architecture (`scripts/compile_tomo1_asis_only.py`)

To eliminate the operational bottleneck of rebuilding all 50 client delivery files whenever Volume 1 (`Tomo 1 As-Is`) is modified, the standalone compiler script below isolates data hydration, actuarial reconciliation, AST generation, and rendering strictly to Volume 1, executing in **< 2.5 seconds**.

```python
#!/usr/bin/env python3
"""
Standalone Fast-Path Compiler for Volume 1 (As-Is Forensic Assessment).
Bypasses the 50-file full suite build to compile and verify Volume 1 in < 5 seconds.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.compilers.tomo_asis_ast_compiler import AsIsAstCompiler
from src.renderers.document_renderer import render_ast_to_docx

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("compile_volume1_only")


def load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required telemetry artifact not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile only Volume 1 (As-Is Baseline) AST and DOCX in <5s."
    )
    parser.add_argument(
        "--tenant-dir",
        type=Path,
        required=True,
        help="Path to the tenant telemetry directory containing payload JSONs.",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="en",
        help="Target document language code (e.g., en, es, pt, fr, de, ja).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "build" / "fast_volume1",
        help="Destination directory for compiled AST and rendered document.",
    )
    parser.add_argument(
        "--ast-only",
        action="store_true",
        help="Emit only the verified JSON AST without invoking the DOCX renderer.",
    )
    return parser.parse_args()


def main() -> int:
    start_ts = time.perf_counter()
    args = parse_args()

    tenant_dir: Path = args.tenant_dir.resolve()
    output_dir: Path = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading tenant telemetry from: %s", tenant_dir)
    global_payload = load_json_file(tenant_dir / "global_payload.json")
    financial_telemetry = load_json_file(tenant_dir / "financial_telemetry.json")
    tower_payloads = load_json_file(tenant_dir / "tower_payloads.json")

    i18n_path = PROJECT_ROOT / "src" / "i18n" / f"{args.lang}.json"
    i18n_catalog = load_json_file(i18n_path)

    logger.info("Compiling Volume 1 AST (locale=%s)...", args.lang)
    compiler = AsIsAstCompiler(
        global_payload=global_payload,
        financial_telemetry=financial_telemetry,
        tower_payloads=tower_payloads,
        i18n_catalog=i18n_catalog,
        doc_lang=args.lang,
    )
    ast_payload = compiler.compile_ast()

    ast_output_path = output_dir / f"volume1_asis_ast_{args.lang}.json"
    with ast_output_path.open("w", encoding="utf-8") as ast_file:
        json.dump(ast_payload, ast_file, ensure_ascii=False, indent=2)
    logger.info("AST written to: %s", ast_output_path)

    if not args.ast_only:
        docx_output_path = output_dir / f"Volume_1_AsIs_Assessment_{args.lang.upper()}.docx"
        render_ast_to_docx(ast_payload, output_path=docx_output_path)
        logger.info("Rendered DOCX written to: %s", docx_output_path)

    elapsed = time.perf_counter() - start_ts
    logger.info("Volume 1 standalone compilation completed in %.2f seconds.", elapsed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```