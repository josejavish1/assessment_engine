"""Consult gemini-4-argon: Forensic evaluation of external Tier-1 adversarial review."""

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

EXTERNAL_CRITIQUE = """
Un revisor Tier 1 diría: “RECHAZADO como modelo actuarial para decisiones financieras, regulatorias o de consejo. Aceptable como prototipo exploratorio si las cifras se presentan como escenarios heurísticos.”

Sí habéis corregido defectos reales, pero el núcleo de validez actuarial sigue sin resolverse.

### Hallazgos críticos

1. La salida presentada no procede realmente del motor probabilístico.
   El flujo asigna primero ALE mediante pesos 10.0 / 4.5 / 1.8 / 0.8 y calcula P90 multiplicando esa asignación por un ratio fijo (tower_payload_hydrator.py:998). Después ejecuta el motor bayesiano, pero solo reemplaza ALE/P90 si esos campos están vacíos (tower_payload_hydrator.py:1406). Como ya están rellenos, la simulación no se convierte en la fuente de verdad.
   Los compiladores consumen precisamente esos valores heurísticos (in_memory_asis_compiler.py:598). El nuevo ledger SSOT, el asignador continuo y el motor polimórfico no tienen consumidores de producción.

2. Hay un bug dimensional grave en P90.
   t_score acumula pérdidas monetarias (tower_payload_hydrator.py:904), pero después se pasa como maturity_score, cuyo dominio debería ser 1–5 (tower_payload_hydrator.py:1038). La función lo recorta a 5, así que casi siempre genera el mismo ratio de “alta madurez” (actuarial_calibration_engine.py:181).
   Si existen domain_weights explícitos, t_score ni siquiera se inicializa: el flujo puede terminar en UnboundLocalError.

3. El P90 de cartera continúa siendo incorrecto.
   Se suman los P90 individuales (tower_payload_hydrator.py:1050). Eso equivale a asumir dependencia perfecta. El motor ya calcula un portfolio_var_90 con dependencias, pero esa cifra queda en un resumen paralelo. VaR no se agrega sumando percentiles marginales salvo supuestos muy específicos.

4. No existe calibración empírica ni validación externa.
   Los parámetros sectoriales —frecuencias, elasticidades, ratios de gasto y probabilidades— están declarados sin fuente, muestra, fecha, error de estimación o versión de calibración (taxonomy_actuarial_archetypes.json:168). No se encontró: backtesting, validación fuera de muestra, cobertura real P90/P95, ni curvas de calibración.

5. La actualización denominada “bayesiana” no tiene una likelihood defendible.
   Se convierten documentos, gaps y strengths de auditoría en “fallos” y “ensayos”, y después se tratan como eventos Poisson/Binomial sobre un año ficticio (fair_risk.py:412). Un hallazgo documental no es un incidente observado ni un año de exposición.

6. El tratamiento de colas reduce artificialmente el riesgo.
   La distribución se corta en su propio P99 antes de calcular ALE y Expected Shortfall (fair_risk.py:827). Además, el comentario sobre el “Infinite Mean Paradox” de la lognormal es falso: una lognormal con sigma finita tiene media finita (fair_risk.py:72).

7. Hay errores regulatorios y etiquetado de falsa precisión.
   La sanción máxima se calcula con min(20M, 4% turnover) (calculators.py:193), cuando GDPR/NIS2 utilizan formulaciones de “el importe superior” (whichever is higher).
   Los intervalos de confianza del 95% son multiplicadores fijos como ALE × 0.40 y ALE × 2.30 (calculators.py:65).

8. El expediente de auditoría sería rechazado por model risk.
   El dossier llama CVaR al campo P90 (actuarial_ledger_generator.py:48) y declara cumplimiento SR 11-7 sin evidencias suficientes.
"""

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, Fellow of the Open FAIR Institute, and Master of Model Risk Governance (SR 11-7 / TRIM / Solvency II).

We have received an adversarial peer-review critique from an external Tier-1 AI auditor on our Assessment Engine codebase.
Here is the verbatim text of the external critique:

```markdown
{EXTERNAL_CRITIQUE}
```

OUR EMPIRICAL CODEBASE VERIFICATION OF THE CITATIONS:
1. `tower_payload_hydrator.py:998`: Confirmed. Hardcoded weights `10.0 / 4.5 / 1.8 / 0.8` allocate domain ALE before the Bayesian simulation runs.
2. `tower_payload_hydrator.py:1406`: Confirmed. Line 1406 has `if payload.get("total_fair_ale") is None:` which evaluates to False because line 1050 already filled it with heuristic sums. The standalone Bayesian ALE/P90/P99 are dropped!
3. `tower_payload_hydrator.py:904` & `1038`: Confirmed. `t_score` accumulates `ale` in EUR, and is then passed into `calculate_dynamic_p90_ratio(maturity_score=t_score)` which expects CMMI score [1.0, 5.0], clamping it to 5.0 always!
4. `tower_payload_hydrator.py:1050`: Confirmed. `payload["total_fair_p90"] = sum(hc["fair_p90_score"] for hc in all_findings)` - linear sum of 90th percentiles!
5. `fair_risk.py:827`: Confirmed. `p99_limit = float(np.percentile(loss_per_run, 99.0))` and `np.clip(loss_per_run, a_min=None, a_max=p99_limit)` truncates the top 1% tail.
6. `calculators.py:193`: Confirmed. `min(20_000_000.0, turnover * 0.04)` caps fine at 20M EUR instead of using GDPR/NIS2 statutory rule "whichever is higher" (max).
7. `actuarial_ledger_generator.py:48`: Confirmed. `cvar = finding.get("fair_p90_score", 0.0)` labeled as `Conditional Value-at-Risk (CVaR - P90)`.

YOUR MANDATE:
Deliver an authoritative, unflinching, mathematical, and forensic ruling on this external review:
1. Forensic Accuracy: Is the external review accurate? Evaluate each of the 8 findings (Concur, Partially Concur, Dissent) with rigorous mathematical and actuarial justification.
2. The Brutal Truth about the Tier-1 Verdict: Is the external reviewer's verdict ("REJECTED as an actuarial model for financial, regulatory, or board decisions; acceptable as an exploratory heuristic prototype") technically sound and justified under SR 11-7 model risk standards?
3. Architectural Diagnosis of the Split-Brain: How did this architecture develop a state-of-the-art engine (Bayesian copulas, polymorphic baselines, continuous allocators) that is bypassed by legacy procedural glue code?
4. Concrete, Phased Remediation Blueprint: Provide the definitive architectural master plan to eliminate the heuristic bypass, wire the authentic Bayesian/Copula simulation as the sole SSOT to the deliverables, fix the dimensional and mathematical errors, and achieve genuine Tier-1 actuarial rigor.

Respond in 100% Technical English with supreme precision, rigorous mathematical clarity, and absolute zero sycophancy.
"""


def main() -> None:
    print(f"Submitting External Critique Analysis to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_EXTERNAL_CRITIQUE_RULING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nRuling written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:2000] + ("\n... [TRUNCATED]" if len(ruling) > 2000 else ""))


if __name__ == "__main__":
    main()
