"""Consult gemini-4-argon: Forensic evaluation of external Tier-1 adversarial review Phase 3 (commit 5ed7eec)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

EXTERNAL_CRITIQUE_3 = """
He revisado el nuevo `main` en `5ed7eec`. **Sí habéis corregido una parte importante de los problemas anteriores.** El dictamen cambia: ya no veo un modelo conceptualmente roto, sino un motor prometedor con varios defectos estadísticos y de trazabilidad concretos que deben corregirse antes de confiar en sus cifras.

### Bloqueadores críticos restantes

1. La simulación Poisson está sesgada.
   El mismo uniforme de la cópula se utiliza para generar TEF y para invertir la Poisson (bayesian_fair_copula_engine.py:404). Eso introduce dependencia artificial entre la intensidad y el conteo (+39,03% de sesgo). Se necesita un uniforme independiente para el conteo condicional.

2. CVaR está mal calculado cuando VaR es cero.
   La implementación selecciona `arr >= VaR` (línea 399). En distribuciones discretas con más de 90% de años sin pérdidas, VaR90 es cero y esa condición incluye toda la distribución (incluyendo los ceros). ALE=4.12, VaR90=0, CVaR90 actual=4.12, cuando debería ser ~41.20.

3. El supuesto backtesting Kupiec no certifica el modelo.
   El nuevo test calcula `passed`, pero nunca ejecuta `assert passed` (test_actuarial_kupiec_backtesting.py:126). Solo exige menos de 200 excedencias, aunque el objetivo nominal sea 100. Con significancia del 5% se rechazaría.

4. El expediente actuarial audita el motor equivocado.
   El ledger se genera inmediatamente después de `FairRiskPolicy` (run_tower_blueprint_engine.py:1233), mientras el motor de cópula se ejecuta posteriormente en el hidratador. El script de reproducción solo crea el motor y muestra un print.

5. La ruta polimórfica introduce estado entre hallazgos.
   Para disponibilidad se consulta `'rating_key' in locals()` (tower_payload_hydrator.py:1303). Debe inicializarse explícitamente en cada iteración. Además, el ajuste SPOF sobreescribe pérdidas de productividad, FinOps o regulatorias por múltiplos de coste horario (línea 1308), rompiendo la separación polimórfica.

6. Los nuevos campos no forman parte del contrato tipado.
   `fair_cvar_score`, `total_fair_cvar_90`, CVaR99 y `standalone_fair_ale` no aparecen en los esquemas Pydantic. El esquema todavía describe `total_fair_p90` como `"CVaR / P90"` (blueprint.py:628). Además, los CVaR globales no se copian a `global_payload["portfolio_summary"]`.

7. Falta todavía el ledger de variables.
   El expediente no muestra los parámetros reales utilizados por la cópula: TEF min/moda/max, RTO min/moda/max, coste horario, pérdida secundaria, arquetipo, fuente, confianza y confirmación del cliente.

8. Hay una regresión de integración con torres dinámicas.
   El hidratador falla con torres dinámicas como `D_FAC` porque el registro actuarial solo admite `T1…T10`.
"""

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, Fellow of the Open FAIR Institute, and Master of Model Risk Governance (SR 11-7 / TRIM / Solvency II).

We have received a Phase 3 adversarial peer-review critique from an external Tier-1 AI auditor on our Assessment Engine codebase at commit `5ed7eec`.
Here is the verbatim text of the external critique:

```markdown
{EXTERNAL_CRITIQUE_3}
```

OUR EMPIRICAL CODEBASE VERIFICATION:
1. `bayesian_fair_copula_engine.py:404`: Confirmed. `u_copula[:, idx]` was reused to invert `stats.poisson.ppf(u_copula[:, idx], mu=lambda_rates)`, introducing severe intensity-frequency collinearity (+39% bias).
2. `bayesian_fair_copula_engine.py:399`: Confirmed. `_cvar` uses `arr[arr >= v]`. When `v == 0.0`, it selects the whole array including zeroes, yielding ALE instead of the true conditional tail mean!
3. `test_actuarial_kupiec_backtesting.py:126`: Confirmed. `passed` was unpacked but never asserted with `assert passed`.
4. `run_tower_blueprint_engine.py:1233`: Confirmed. `generate_actuarial_ledger` was called in standalone compilation before `tower_payload_hydrator` executed the copula.
5. `tower_payload_hydrator.py:1303`: Confirmed. `'rating_key' in locals()` leaked loop state, and `spof_flag` collapsed polymorphic secondary losses back to `derived_hourly_rate * 2.65`.
6. `blueprint.py:628`: Confirmed. `total_fair_cvar_90` etc. are missing from Pydantic schema, and description says `"CVaR / P90"`.
7. `archetype_registry.py:74`: Confirmed. `get_mapping_for_tower` raises `KeyError` on dynamic tower IDs like `D_FAC`.

YOUR MANDATE:
Deliver an authoritative, unflinching, mathematical ruling:
1. Forensic Evaluation of the 8 Blockers: Concur / Dissent on each blocker with mathematical rigor.
2. The Verdict on Global Multi-Enterprise Scalability: How do we fix these 8 blockers so the engine works flawlessly for any enterprise worldwide (from SMBs to Global 500s)?
3. Concrete Phased Fix Specification: Provide the exact code-level requirements to resolve all 8 blockers in order of priority.

Respond in 100% Technical English with supreme precision and absolute zero sycophancy.
"""


def main() -> None:
    print(f"Submitting Phase 3 External Critique Analysis to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_EXTERNAL_CRITIQUE_PHASE3_RULING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nRuling written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:2000] + ("\n... [TRUNCATED]" if len(ruling) > 2000 else ""))


if __name__ == "__main__":
    main()
