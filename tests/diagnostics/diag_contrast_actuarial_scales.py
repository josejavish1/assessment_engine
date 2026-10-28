import json
import os
import shutil
from pathlib import Path

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine


def run_test_client(client_id: str, annual_revenue: float, digital_dependency: float, fine_ratio: float):
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id
    os.environ["ASSESSMENT_INDUSTRY"] = "Technology & Infrastructure"

    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"

    hourly_cost = (annual_revenue * digital_dependency) / 8760.0
    custom_profile_path.write_text(
        json.dumps({
            "annual_revenue_eur": annual_revenue,
            "digital_dependency_factor": digital_dependency,
            "hourly_downtime_cost_eur": hourly_cost,
            "regulatory_fine_cap_ratio": fine_ratio,
            "capability_calibrations": {
                "CI_CD_AUTOMATION": {
                    "typology": "OPERATIONAL_FRICTION",
                    "annual_waste_eur": annual_revenue * 0.005,
                },
                "PERIMETER_GATEWAY": {
                    "typology": "CATASTROPHIC_SYSTEMIC",
                    "exposure_vector": "INTERNET_FACING",
                    "exposure_factor": 1.0,
                },
            },
        }),
        encoding="utf-8",
    )

    try:
        graph = EpistemicGraph(client_id=client_id)
        engine = SovereignPolicyEngine(graph)

        payload = {
            "document_meta": {
                "client_name": client_id,
                "tower_code": "T2",
                "tower_name": "Platforms",
                "tower_id": "T2",
            },
            "pillars_analysis": [
                {
                    "pilar_id": "T2.P1",
                    "pilar_name": "Core Platforms",
                    "current_maturity": 2.0,
                    "projects_todo": [],
                    "health_check_asis": [
                        {
                            "finding": "Proceso manual de despliegue de infraestructura sin automatización CI/CD",
                            "impact": "Sobrecoste operativo recurrente del equipo de ingeniería",
                            "capability": "CI_CD_AUTOMATION",
                        },
                        {
                            "finding": "Vulnerabilidad crítica sin parchear expuesta a internet en el gateway perimetral",
                            "impact": "Riesgo de brecha de datos e interrupción del servicio",
                            "capability": "PERIMETER_GATEWAY",
                        },
                    ],
                }
            ],
        }

        compiled = engine.compile(payload)
        return compiled["pillars_analysis"][0]["health_check_asis"], hourly_cost
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))


if __name__ == "__main__":
    print("=" * 80)
    print("  SIMULACIÓN ACTUARIAL COMPARATIVA: PYME (5M €) VS CORPORACIÓN (1.000M €)")
    print("=" * 80)

    # 1. Pyme 5M €
    pyme_results, pyme_hourly = run_test_client("pyme_5m", 5_000_000.0, 0.5, 0.04)
    # 2. Corporación 1.000M €
    corp_results, corp_hourly = run_test_client("corp_1000m", 1_000_000_000.0, 0.5, 0.02)

    for idx, (pyme_f, corp_f) in enumerate(zip(pyme_results, corp_results), start=1):
        print(f"\n[{idx}] Hallazgo: {pyme_f['finding'][:65]}...")
        print(f"    Tipología: {pyme_f.get('typology')}")
        print("-" * 80)
        print(f"    PYME (Facturación: 5 M€ | Coste parada: {pyme_hourly:,.2f} €/h):")
        print(f"      - ALE (Pérdida Anual Esperada): {pyme_f.get('fair_ale_score', 0):>12,.2f} €")
        print(f"      - P90 (Exposición Extrema):     {pyme_f.get('fair_p90_score', 0):>12,.2f} €")
        print(f"      - Rango Pérdida (Min - Max):   {pyme_f.get('fair_min_score', 0):>12,.2f} € a {pyme_f.get('fair_max_score', 0):>12,.2f} €")
        print()
        print(f"    CORPORACIÓN (Facturación: 1.000 M€ | Coste parada: {corp_hourly:,.2f} €/h):")
        print(f"      - ALE (Pérdida Anual Esperada): {corp_f.get('fair_ale_score', 0):>12,.2f} €")
        print(f"      - P90 (Exposición Extrema):     {corp_f.get('fair_p90_score', 0):>12,.2f} €")
        print(f"      - Rango Pérdida (Min - Max):   {corp_f.get('fair_min_score', 0):>12,.2f} € a {corp_f.get('fair_max_score', 0):>12,.2f} €")
        
        ratio = corp_f.get('fair_ale_score', 1) / max(1.0, pyme_f.get('fair_ale_score', 1))
        print(f"    >> Factor de Escala Real (Corp / Pyme): {ratio:,.1f}x (Ratio Facturación: 200x)")
