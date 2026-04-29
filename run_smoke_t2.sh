#!/bin/bash
set -e
export PYTHONPATH=src
echo "1/5 Generando datos de entrada mockeados..."
.venv/bin/python -m assessment_engine.scripts.tools.generate_smoke_data

echo "2/5 Ejecutando Minuto Cero (Inteligencia OSINT)..."
.venv/bin/python -m assessment_engine.scripts.run_intelligence_harvesting smoke_ivirma

echo "3/5 Procesando solo la Torre T2 (Prueba Ágil)..."
t="T2"
echo ">>> Iniciando Torre $t..."
.venv/bin/python -m assessment_engine.scripts.run_tower_pipeline --tower $t --client smoke_ivirma --context-file working/smoke_ivirma/context.txt --responses-file working/smoke_ivirma/responses.txt

echo "4/5 Ejecutando Consolidación Global..."
.venv/bin/python -m assessment_engine.scripts.run_global_pipeline smoke_ivirma

echo "5/5 Ejecutando Refinado Comercial y Account Action Plan..."
.venv/bin/python -m assessment_engine.scripts.run_commercial_pipeline smoke_ivirma

echo "=== ✅ SIMULACIÓN ÁGIL (T2) COMPLETADA ==="
