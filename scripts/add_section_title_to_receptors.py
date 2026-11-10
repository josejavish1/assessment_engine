import json
from pathlib import Path

path = Path("engine_config/locales.json")
data = json.loads(path.read_text(encoding="utf-8"))

TITLES = {
    "en": {
        "AVAILABILITY_OUTAGE": "4.1. Estimated Cost of Service Disruption & Outages",
        "CAPITAL_INEFFICIENCY": "4.1. Capital Inefficiency & Structural Waste Model",
        "PRODUCTIVITY_TOIL": "4.1. Operational Toil & Workforce Productivity Model",
        "REGULATORY_AND_BREACH": "4.1. Regulatory Liability & Security Breach Model"
    },
    "es": {
        "AVAILABILITY_OUTAGE": "4.1. Coste Estimado por Indisponibilidad y Parada de Servicio",
        "CAPITAL_INEFFICIENCY": "4.1. Modelo de Ineficiencia de Capital y Desvío Presupuestario",
        "PRODUCTIVITY_TOIL": "4.1. Cuantificación de Toil Operativo y Fricción de Plantilla",
        "REGULATORY_AND_BREACH": "4.1. Modelo de Exposición a Brechas, Extorsión y Sanciones Regulatorias"
    },
    "pt": {
        "AVAILABILITY_OUTAGE": "4.1. Custo Estimado de Indisponibilidade e Parada de Serviço",
        "CAPITAL_INEFFICIENCY": "4.1. Modelo de Ineficiência de Capital e Desperdício de Infraestrutura",
        "PRODUCTIVITY_TOIL": "4.1. Quantificação de Toil Operacional e Fricção de Produtividade",
        "REGULATORY_AND_BREACH": "4.1. Modelo de Responsabilidade Regulatória e Violação de Segurança"
    },
    "fr": {
        "AVAILABILITY_OUTAGE": "4.1. Coût Estimé d'Indisponibilité et d'Interruption de Service",
        "CAPITAL_INEFFICIENCY": "4.1. Modèle d'Inefficacité du Capital et Gaspillage Structurel",
        "PRODUCTIVITY_TOIL": "4.1. Quantification du Toil Opérationnel et Friction de Productivité",
        "REGULATORY_AND_BREACH": "4.1. Modèle de Risque Réglementaire et Violation de Données"
    },
    "de": {
        "AVAILABILITY_OUTAGE": "4.1. Geschätzte Ausfallkosten & Betriebsunterbrechungsmodell",
        "CAPITAL_INEFFICIENCY": "4.1. Modell für Kapitalineffizienz & Infrastrukturverschwendung",
        "PRODUCTIVITY_TOIL": "4.1. Quantifizierung von operativem Toil & Produktivitätsverlusten",
        "REGULATORY_AND_BREACH": "4.1. Modell für regulatorische Haftung & Sicherheitsverletzungen"
    },
    "ja": {
        "AVAILABILITY_OUTAGE": "4.1. サービス停止およびダウンタイム損失推定モデル",
        "CAPITAL_INEFFICIENCY": "4.1. 資本非効率性およびインフラ浪費モデル",
        "PRODUCTIVITY_TOIL": "4.1. 運用トイルおよび生産性摩擦の定量化モデル",
        "REGULATORY_AND_BREACH": "4.1. 規制責任およびセキュリティ侵害リスクモデル"
    }
}

for lang, titles_map in TITLES.items():
    if lang in data and "annex_ch4_receptors" in data[lang]:
        for rec, title in titles_map.items():
            if rec in data[lang]["annex_ch4_receptors"]:
                data[lang]["annex_ch4_receptors"][rec]["section_title"] = title

path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("✓ Successfully injected localized section_title across all 6 languages.")
