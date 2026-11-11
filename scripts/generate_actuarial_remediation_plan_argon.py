"""Script to consult gemini-4-argon and generate an exhaustive implementation plan for the actuarial core."""

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

AUDIT_TEXT = """
Auditoría del núcleo actuarial en 41d4c2d:

## Correcciones verificadas
- La invariancia al orden está corregida: los findings se ordenan canónicamente antes del RNG.
- La colisión entre sedes por zone_id está corregida mediante canonical_scoped_key.
- Los conflictos de parámetros dentro de la misma scoped zone fallan explícitamente.
- Las 18 pruebas dirigidas del kernel, invariancia y orquestador pasan.

## P0 — Parameter pack decorativo; los números siguen hardcodeados
El archivo engine_config/actuarial/parameter_packs/legacy_generic_v1.json no tiene ningún consumidor en src/. Los mismos valores están duplicados en:
- canonical_risk_orchestrator.py:118-145
- input_resolver.py:154-275
- defaults del constructor de bayesian_fair_copula_engine.py:202-218
Censo AST: 176 literales numéricos no triviales en la ruta primaria (resolver: 34, kernel: 119, orquestador: 23).
Remediación: crear modelo Pydantic del pack, loader único, inyectarlo en resolver/kernel, eliminar duplicados Python y grabar pack_id, versión y SHA-256 en el manifiesto.

## P0 — El resolver sigue reparando silenciosamente inputs inválidos
input_resolver.py:
- TEF negativa se reemplaza por 0.30.
- RTO negativo se reemplaza por 4.0.
- PERT inválido se reordena silenciosamente.
- CMMI fuera de rango se clampa.
- alpha=0 se convierte en 0.60 por 'or'.
- rho=0 se convierte en 0.30.
- k_failures > n_trials modifica n_trials.
- booleano 'garbage' se interpreta como False, pero se marca ASSESSMENT_PAYLOAD/HIGH.
El kernel posteriormente clampa replacement a cero y descarta secondary loss negativa.
Remediación: distinguir ausente de inválido; preservar ceros válidos; rechazar explícitos fuera de rango; no reparar PERT; validar counts; hacer que FindingTelemetry valide invariantes en __post_init__; prohibir clamps que diverjan del vector.

## P0 — El contexto sigue siendo opcional y el FX no se aplica
canonical_risk_orchestrator.py crea un contexto legacy cuando falta contexto.
Se acepta source_currency=USD, reporting_currency=EUR, sin snapshots FX. Nunca se llama a normalize_monetary_amount().
Remediación: contexto obligatorio para producción; model validator que exija FX cuando las monedas difieran; convertir cada input monetario antes del vector; añadir moneda original, rate y snapshot al linaje.

## P0 — Versionado de manifiesto incorrecto
- manifest_schema_version='1.0.0'
- actuarial_model_version='2026.Q1.v1'
- risk_scope sigue siendo opcional y assessment_period conserva default.
- No hay pack ID/hash ni context hash.
Remediación: bump de schema/model a 2.0.0 / 2026.Q4.v2, campos obligatorios, pack hash en fingerprint.

## P1 — QUANTIFIED no significa evidencia suficiente
El estado sólo comprueba si TEF y RTO fueron explícitos.
Remediación: matriz de evidencia por arquetipo. Si cualquier input material procede del pack, utilizar ESTIMATED_LOW_CONFIDENCE. Corregir bug de composición donde dominio custom solo termina INSUFFICIENT_EVIDENCE y junto a T1 termina NOT_QUANTIFIED.

## P1 — Hipótesis del kernel sin calibración versionada
11 hiperparámetros del constructor hardcodeados: vuln_min, vuln_max, gamma, kappa, copula_df, intra_tower_boost, secondary_loss_cv, spof_cmmi_penalty, max_dependence_loading, max_copula_correlation, rto_cmmi_degradation_slope, rto_spof_multiplier, catastrophic_tail_quantile.
Remediación: mover a KernelCalibrationPack versionado.

## P1 — Semántica actuarial sobrevendida
Aclarar terminología: weighted_maturity_adjustment, p95_single_event_stress_loss, three_year_undiscounted_baseline_expected_loss.

## P1 — Múltiples modelos actuariales (código muerto)
actuarial_calibration_engine.py, actuarial_ledger.py, calculators.py, calibration_engine.py, continuous_risk_allocator.py, vectors.py (1.058 LOC). Confirmar y purgar.

## P2 — Fingerprint no representa el vector exacto
Serializa floats redondeados a 2 o 4 decimales.
Remediación: serialización canónica JSON de valores exactos con SHA-256 completo.

## Cobertura insuficiente
Faltan tests directos para ActuarialInputResolver (ceros válidos, negativos, PERT invertido, booleanos inválidos, FX ausente, parameter pack consumido).
"""

PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, Fellow of the Open FAIR Institute, and Master of Zero-Defect Systems Engineering.

The human user has requested:
"quiero que gemini-4-argon nos genere un plan superexahustivo en uno o varios ficheros para que gemini 3.8 luego pueda programarlo sin problemas."

We have audited the actuarial core of `josejavish1/assessment_engine` at commit `41d4c2d`. Here is the exact forensic audit:

{AUDIT_TEXT}

YOUR TASK:
Generate an exhaustive, infallible, step-by-step master implementation plan designed specifically so that an automated coding agent (like `gemini-3.8-flash`) can execute it flawlessly without getting stuck, without breaking existing tests, without hallucinating, and without suppressing exceptions.

The plan MUST provide:
1. Exact File Paths for every new or modified file.
2. Complete Pydantic Models and Data Contracts (with exact fields, types, and model_validators):
   - `ActuarialParameterPack` schema and loader.
   - `KernelCalibrationPack` schema.
   - Updated `FindingTelemetry` with strict `__post_init__` invariant assertions (rejecting negative numbers, clamping, etc.).
   - Updated `ActuarialInputResolver` logic:
     * Differentiating explicitly between `None` (missing -> resolve via pack as `ESTIMATED_LOW_CONFIDENCE`) vs invalid numbers (< 0 -> raise `ValueError`).
     * Preserving valid `0.0` (e.g. `direct_replacement_cost=0.0`, `audit_k_failures=0`).
     * Strict PERT ordering assertion (`min <= mode <= max`) without silent auto-reordering.
     * Strict boolean parser (raising `ValueError` on garbage strings like `"invalid_bool"`).
   - Mandatory FX conversion in `CanonicalRiskOrchestrator` before vector creation, recording `source_currency`, `reporting_currency`, `fx_rate`, and `fx_snapshot_id` in parameter lineage.
   - Manifest Schema 2.0.0 and Actuarial Model 2026.Q4.v2 with full canonical JSON serialization for 256-bit SHA-256 fingerprinting.
   - Dead code removal list with verified confirmation.
3. Step-by-Step Implementation Sequence (Phases 1 to 7):
   - For each phase, specify: Exact file, exact code changes, exact pitfalls to avoid, and exact verification test commands.
4. Comprehensive Unit Test Specifications:
   - Exhaustive test cases for `tests/unit/domain/actuarial/test_input_resolver.py`.
   - Comprehensive test cases for `tests/unit/domain/actuarial/test_parameter_pack_loading.py`.
   - Comprehensive test cases for `tests/unit/domain/actuarial/test_fx_currency_consolidation.py`.
5. Failure Prevention Checklist:
   - The top 5 failure modes of `gemini-3.8-flash` and how to preempt them.

Write this plan in 100% Technical English with supreme precision and zero conversational filler.
"""


def main() -> None:
    print(f"Submitting Actuarial Core Master Plan Request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    plan_text = response.text
    out_file = REPO_ROOT / "PROMPT_REMEDIACION_NUCLEO_ACTUARIAL_SR11_7.md"
    out_file.write_text(plan_text, encoding="utf-8")

    print(f"\nMaster Plan written to: {out_file}\n")
    print("=" * 80)
    print(plan_text[:3000] + ("\n... [TRUNCATED]" if len(plan_text) > 3000 else ""))


if __name__ == "__main__":
    main()
