#!/bin/bash
set -e

# --- CONFIGURACIÓN DE RUTAS ---
CLIENT_NAME="REDEIA2"
SLUG="redeia2"
WORKING_DIR="working/${SLUG}"
PYTHON_BIN="./.venv/bin/python"

# Configurar entorno
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
export GOOGLE_APPLICATION_CREDENTIALS=/home/jsanchhi/.secrets/sa-key.json

echo "🚀 REANUDANDO GENERACIÓN REDEIA2 (Fases Finales)..."

# --- 3. FASE 3: CONSOLIDACIÓN GLOBAL ---
echo "🌍 FASE 3: Ejecutando Consolidación Global..."
$PYTHON_BIN -m application.run_global_pipeline "${SLUG}"

# --- 4. FASE 4: REFINADO COMERCIAL Y ACCOUNT PLAN ---
echo "💼 FASE 4: Ejecutando Refinado Comercial..."
$PYTHON_BIN -m application.run_commercial_pipeline "${SLUG}"

# --- 5. FASE 5: DASHBOARD WEB INTERACTIVO ---
echo "🖥️ FASE 5: Generando Dashboard Web..."
$PYTHON_BIN -m adapters.render_web_presentation "${SLUG}"

echo "==========================================================="
echo "✅ PROCESO DE REANUDACIÓN FINALIZADO CON ÉXITO"
echo "📂 Resultados finales disponibles en: ${WORKING_DIR}"
echo "==========================================================="
