#!/bin/bash
set -e

CLIENT="ivirma"
WORKING_DIR="working/${CLIENT}"

echo "1/4 Generando datos mockeados basados en OSINT..."
.venv/bin/python -c "
import json
import random
from pathlib import Path

client_dir = Path('${WORKING_DIR}')
client_dir.mkdir(parents=True, exist_ok=True)

towers = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9']
responses_lines = []

tower_targets = {
    'T2': (3.0, 4.0), # Cómputo: Tienen migración fuerte a Azure y DevOps. Bien posicionados.
    'T3': (1.5, 2.5), # Redes: Crecimiento inorgánico (comprando clínicas) fragmenta la red. (Bajo)
    'T4': (3.0, 4.0), # Datos: Inversión en Data Scientists y Machine Learning (Azure SQL/PowerBI). (Alto)
    'T5': (1.5, 2.5), # Resiliencia: Riesgo crítico en sector salud con RGPD/NIS2 y ransomware (Bajo)
    'T6': (1.5, 2.5), # Seguridad: Igual que resiliencia, sector crítico y crecimiento M&A dificulta control (Bajo)
    'T7': (2.0, 3.0), # ITSM: Operativa mejorable (Medio)
    'T8': (2.0, 3.0), # Estrategia/FinOps: Tienen estrategia cloud, pero la gobernanza en M&A es difícil (Medio)
    'T9': (2.0, 3.0)  # Puesto de trabajo (Medio)
}

root = Path('.')
for t in towers:
    def_file = root / 'engine_config' / 'towers' / t / f'tower_definition_{t}.json'
    if def_file.exists():
        data = json.loads(def_file.read_text(encoding='utf-8'))
        min_s, max_s = tower_targets[t]
        for p in data.get('pillars', []):
            for k in p.get('kpis', []):
                score = round(random.uniform(min_s, max_s), 1)
                responses_lines.append(f\"{k['kpi_id']}.PR1: {score}\")

responses_path = client_dir / 'responses.txt'
responses_path.write_text('\n'.join(responses_lines), encoding='utf-8')

context_text = \"\"\"Notas de la reunión de Assessment Tecnológico de IVIRMA.

Contexto de Negocio y Estrategia:
La compañía, bajo la dirección de Javier Sánchez-Prieto tras la adquisición por KKR, tiene el mandato de duplicar la facturación a 1.300M€ en 5 años. Este crecimiento será fuertemente inorgánico (M&A) con foco en Asia y EE. UU.
El desafío principal es cómo integrar tecnológicamente estas nuevas clínicas sin ralentizar el 'time-to-market' de la compra ni comprometer los estándares clínicos.

Tecnología y Datos:
Existe una fuerte apuesta por el ecosistema Microsoft (Azure, .NET, PowerBI). Han migrado cargas a Azure, usando PaaS (App Services, Functions) y DevOps, lo que les da agilidad en desarrollo.
Se está invirtiendo masivamente en Data Science (Python/R) para medicina de precisión. 
El ecosistema corporativo se apoya en SAP (ERP) y Salesforce (CRM). Sin embargo, el crecimiento por M&A está generando una red de comunicaciones y un puesto de trabajo muy fragmentados.

Seguridad, Riesgo y Cumplimiento:
El CISO destaca la máxima criticidad del dato (datos de salud, embriones, historiales). Están sujetos a RGPD estricto y a la nueva directiva NIS2 como sector esencial (Sanidad).
La rápida integración de clínicas compradas introduce riesgos de ciberseguridad. No hay garantías consistentes de recuperación (Vaults inmutables) ante un ataque de ransomware sistémico en las nuevas adquisiciones.

Operaciones:
La operativa tecnológica (ITSM) no está estandarizada a nivel global, dificultando el soporte uniforme a médicos e investigadores en los distintos países. Faltan modelos de gobernanza automatizados que eviten cuellos de botella.\"\"\"

context_path = client_dir / 'context.txt'
context_path.write_text(context_text.strip(), encoding='utf-8')
print('Datos generados.')
"

echo "2/4 Procesando las 8 Torres Técnicas..."
for t in T2 T3 T4 T5 T6 T7 T8 T9; do
  echo ">>> Iniciando Torre $t..."
  .venv/bin/python -m assessment_engine.scripts.run_tower_pipeline --tower $t --client ${CLIENT} --context-file ${WORKING_DIR}/context.txt --responses-file ${WORKING_DIR}/responses.txt
done

echo "3/4 Ejecutando Consolidación Global..."
.venv/bin/python -m assessment_engine.scripts.run_global_pipeline ${CLIENT}

echo "4/4 Ejecutando Refinado Comercial y Account Action Plan..."
.venv/bin/python -m assessment_engine.scripts.run_commercial_pipeline ${CLIENT}

echo "=== ✅ PIPELINE COMPLETADO PARA IVIRMA ==="
