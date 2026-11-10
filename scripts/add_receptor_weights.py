import json
from pathlib import Path

path = Path("engine_config/taxonomy_actuarial_archetypes.json")
data = json.loads(path.read_text(encoding="utf-8"))

data["receptor_weights"] = {
    "AVAILABILITY_OUTAGE": {
        "vector_alpha_weight": 0.40,
        "vector_beta_weight": 0.35,
        "vector_gamma_weight": 0.25
    },
    "CAPITAL_INEFFICIENCY": {
        "vector_alpha_weight": 0.50,
        "vector_beta_weight": 0.30,
        "vector_gamma_weight": 0.20
    },
    "PRODUCTIVITY_TOIL": {
        "vector_alpha_weight": 0.45,
        "vector_beta_weight": 0.35,
        "vector_gamma_weight": 0.20
    },
    "REGULATORY_AND_BREACH": {
        "vector_alpha_weight": 0.55,
        "vector_beta_weight": 0.25,
        "vector_gamma_weight": 0.20
    }
}

path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
