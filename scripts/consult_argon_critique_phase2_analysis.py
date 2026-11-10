"""Consult gemini-4-argon: Forensic evaluation of external Tier-1 adversarial review Phase 2."""

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
He re-auditado el nuevo `main` en `ff7b337`. **Las correcciones son reales y la nota mejora, pero un auditor Tier 1 todavía rechazaría el modelo para uso financiero, regulatorio o de consejo.**

Su dictamen probable sería:
> “El motor tiene una arquitectura cuantitativa prometedora y mayor coherencia matemática, pero todavía no cumple los requisitos de validación, linaje y consistencia semántica necesarios para denominarlo modelo actuarial validado o conforme con SR 11-7.”

## Lo que sí habéis corregido
- El motor de cópula ahora reemplaza incondicionalmente ALE, P90 y P99 de los hallazgos.
- Se corrigió la llamada de P90 para utilizar `cmmi_u` en vez de una cantidad monetaria.
- La simulación principal ya calcula VaR90 real.
- Se eliminó el truncamiento previo en el P99.
- Se corrigió `max(20M, 4% turnover)` en el calculador regulatorio nuevo.
- El ledger distingue nominalmente VaR90 de CVaR.
- El núcleo pasa **116/116 tests** y las integraciones seleccionadas **7/7**.

## Bloqueadores que siguen activos

### 1. El SSOT todavía no cierra matemáticamente
El total de torre se escribe con `standalone_ale`, mientras los hallazgos reciben `portfolio_allocated_ale` (tower_payload_hydrator.py:1396).
En una prueba adversarial mínima obtuve: `tower.total_fair_ale` = 13.924,97 vs Suma de `finding.fair_ale_score` = 13.122,65 vs `portfolio_allocated_ale` = 13.122,65.
El compilador define `total_fair_ale` como ALE integrado y subaditivo (run_tower_blueprint_engine.py:989), pero recibe el standalone. Por tanto, tabla detallada, total de torre y cartera pueden presentar cifras diferentes.

### 2. P90 cambia de significado según el pipeline
El motor nuevo escribe VaR90 en `total_fair_p90`. Sin embargo, `FairRiskPolicy` sigue escribiendo Expected Shortfall 97,5% dentro del mismo campo (fair_risk.py:971).
El propio esquema lo describe ambiguamente como `"CVaR / P90"` (blueprint.py:628). Son medidas distintas. Un campo no puede representar ambas según la ruta de ejecución.

### 3. CVaR sigue mezclando motores
El motor de cópula no produce `fair_cvar_score`. El ledger toma el CVaR dejado por el motor anterior o inventa `P90 × 1,15` (actuarial_ledger_generator.py:48).
Una misma fila puede contener: ALE del motor de cópula, P90 del motor de cópula, CVaR de `FairRiskPolicy` o de un multiplicador fijo, P99 etiquetado a partir de otro campo.

### 4. La nueva “calibración empírica” es metadata, no calibración reproducible
Se han añadido fuentes, tamaños muestrales y métodos (taxonomy_actuarial_archetypes.json). Pero no existen datos reales, código de ajuste ni backtesting real. Más grave: `UniversalActuarialCalibrationEngine`, que carga esa metadata, no tiene consumidores en producción. El motor activo utiliza los priors fijos de severidad, TEF, RTO, correlación definidos en el hidratador (tower_payload_hydrator.py:1140). La metadata documenta un modelo; producción ejecuta otro.

### 5. El motor SSOT vuelve a convertir riesgos heterogéneos en horas de interrupción
El `PolymorphicActuarialEngine` tampoco está conectado a producción. El motor activo deriva la pérdida secundaria como múltiplos de la tasa horaria para todos los dominios (línea 1262). Esto significa que sanción regulatoria, pérdida de productividad e ineficiencia cloud terminan parametrizadas con la misma mecánica.

### 6. La distribución anual no simula realmente el número de eventos
El motor calcula `LEF = TEF × vulnerabilidad` y `pérdida anual = LEF × severidad`, pero no genera un conteo anual de eventos Poisson/Binomial Negativa (bayesian_fair_copula_engine.py:393).

### 7. El error regulatorio continúa en el motor activo
Aunque se corrigió el calculador polimórfico, `FairRiskPolicy` todavía dice “whichever is higher” y ejecuta `min(base_fine, turnover_fine)` (fair_risk.py:736).

### 8. La validación dimensional no es estricta
El código dice que CMMI debe estar entre 1 y 5, pero acepta valores entre 0,5 y 6, recortándolos silenciosamente (actuarial_calibration_engine.py:181).

### 9. El supuesto expediente SR 11-7 no reproduce producción
El script de auditoría promete reproducibilidad exacta, pero ejecuta una lognormal genérica con `sigma=1.5`, una Poisson genérica y no reproduce la cópula, zonas, RTO ni vulnerabilidad (actuarial_ledger_generator.py:75). Incluso utiliza un `logger` no definido.
"""

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, Fellow of the Open FAIR Institute, and Master of Model Risk Governance (SR 11-7 / TRIM / Solvency II).

We have received a Phase 2 adversarial peer-review critique from an external Tier-1 AI auditor on our Assessment Engine codebase, responding to our latest commit (ff7b337).

Here is the verbatim text of the external critique:

```markdown
{EXTERNAL_CRITIQUE}
```

YOUR MANDATE:
Deliver an authoritative, unflinching, mathematical, and forensic ruling on this Phase 2 external review:
1. Forensic Accuracy: Is the external review accurate for Phase 2? Evaluate each of the 9 findings with rigorous mathematical and architectural justification. Look at our codebase.
2. The Brutal Truth about the Tier-1 Verdict: Is the external reviewer's updated verdict technically sound and justified under SR 11-7 model risk standards?
3. Concrete, Phased Remediation Blueprint: Provide the definitive architectural master plan to eliminate the 9 blockers, specifically detailing how to fix the SSOT math closure, align P90/CVaR semantics, connect the Polymorphic engine, fix the Poisson simulation, and correct the SR 11-7 ledger script. Give me the EXACT phases I need to execute right now.

Respond in 100% Technical English with supreme precision, rigorous mathematical clarity, and absolute zero sycophancy.
"""


def main() -> None:
    print(f"Submitting Phase 2 External Critique Analysis to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_EXTERNAL_CRITIQUE_PHASE2_RULING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nRuling written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:2000] + ("\n... [TRUNCATED]" if len(ruling) > 2000 else ""))


if __name__ == "__main__":
    main()
