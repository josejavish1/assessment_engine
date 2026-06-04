#!/usr/bin/env bash
set -e

# --- CONFIGURACIÓN DE RUTAS ---
CLIENT_NAME="REDEIA"
SLUG="redeia_test"
WORKING_DIR="working/${SLUG}"
PYTHON_BIN="./.venv/bin/python"

# --- 1. PREPARACIÓN ---
echo "🧹 Preparando entorno de test..."
mkdir -p "${WORKING_DIR}"
rm -rf "${WORKING_DIR}/T"*
rm -f "${WORKING_DIR}"/*.docx "${WORKING_DIR}"/*.html "${WORKING_DIR}"/*.png "${WORKING_DIR}"/*.json

echo "📥 Asegurando archivos de inteligencia y contexto..."
# Copiamos desde REDEIA original
cp -r "working/REDEIA/client_intelligence.json" "${WORKING_DIR}/" || echo "⚠️ client_intelligence.json no copiado"
cp -r "working/REDEIA/260601 Documento de contexto Redeia 2.docx" "${WORKING_DIR}/" || echo "⚠️ Doc de contexto no copiado"
cp -r "working/REDEIA/260601 Respuestas Test Redeia 2.txt" "${WORKING_DIR}/" || echo "⚠️ Doc de test no copiado"

CONTEXT_FILE="${WORKING_DIR}/260601 Documento de contexto Redeia 2.docx"
RESPONSES_FILE="${WORKING_DIR}/260601 Respuestas Test Redeia 2.txt"

export PYTHONPATH="src"
export ASSESSMENT_CLIENT_ID="${SLUG}"

# --- HEARTBEAT FUNCTION ---
start_heartbeat() {
    local message="$1"
    while true; do
        sleep 30
        echo "⏳ [Heartbeat] $message sigo trabajando..."
    done &
    HEARTBEAT_PID=$!
}

stop_heartbeat() {
    if [ -n "$HEARTBEAT_PID" ]; then
        kill $HEARTBEAT_PID 2>/dev/null || true
    fi
}
# --------------------------


# --- 2. FASE 2: TORRES TÉCNICAS (Testeando solo T2) ---
echo "🏗️ FASE 2: Generando Torre T2 para test..."
start_heartbeat "Torre T2"
$PYTHON_BIN -m application.run_tower_pipeline   --tower T2   --client "${CLIENT_NAME}"   --context-file "${CONTEXT_FILE}"   --responses-file "${RESPONSES_FILE}"

stop_heartbeat

# --- 3. FASE 3: CONSOLIDACIÓN GLOBAL ---
echo "🌍 FASE 3: Ejecutando Consolidación Global..."
start_heartbeat "Consolidación Global"
$PYTHON_BIN -m application.run_global_pipeline "${SLUG}"

stop_heartbeat

# --- 4. FASE 4: REFINADO COMERCIAL Y ACCOUNT PLAN ---
echo "💼 FASE 4: Ejecutando Refinado Comercial..."
start_heartbeat "Refinado Comercial"
$PYTHON_BIN -m application.run_commercial_pipeline "${SLUG}"

stop_heartbeat

echo "==========================================================="
echo "✅ PROCESO FINALIZADO CON ÉXITO"
echo "📂 Resultados disponibles en: ${WORKING_DIR}"
stop_heartbeat

echo "==========================================================="
