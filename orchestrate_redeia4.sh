#!/bin/bash
set -e

# --- CONFIGURACIÓN DE RUTAS ---
CLIENT_NAME="REDEIA"
SLUG="redeia4"
WORKING_DIR="working/${SLUG}"
PYTHON_BIN="./.venv/bin/python"

# --- 1. PREPARACIÓN Y LIMPIEZA ---
echo "🧹 Preparando carpeta ${WORKING_DIR}..."
mkdir -p "${WORKING_DIR}"
rm -rf "${WORKING_DIR}/T"*
rm -f "${WORKING_DIR}"/*.docx "${WORKING_DIR}"/*.html "${WORKING_DIR}"/*.png "${WORKING_DIR}"/*.json

# Restaurar archivos base desde la carpeta original (usamos la carpeta REDEIA como origen de confianza de inputs)
echo "📥 Asegurando archivos de inteligencia y contexto..."
cp "working/REDEIA/client_intelligence.json" "${WORKING_DIR}/"
cp "working/REDEIA/260601 Documento de contexto Redeia 2.docx" "${WORKING_DIR}/"
cp "working/REDEIA/260601 Respuestas Test Redeia 2.txt" "${WORKING_DIR}/"

# Modificar el client_intelligence.json para forzar el nombre del cliente a redeia4 para evitar colisiones y asegurar trazabilidad
PYTHONPATH=src $PYTHON_BIN -m application.tools.sign_dossier "${WORKING_DIR}/client_intelligence.json" "REDEIA4"

CONTEXT_FILE="${WORKING_DIR}/260601 Documento de contexto Redeia 2.docx"
RESPONSES_FILE="${WORKING_DIR}/260601 Respuestas Test Redeia 2.txt"

# Configurar entorno para ejecución post-refactor
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
export GOOGLE_APPLICATION_CREDENTIALS=/home/jsanchhi/.secrets/sa-key.json

# --- 2. FASE 2: TORRES TÉCNICAS (CON INTELIGENCIA ESTRATÉGICA) ---
echo "🏗️ FASE 2: Generando Torres Técnicas (Elite Intelligence)..."
# Ejecutamos las torres principales para la comparación
for t in T2 T4 T5 T6 T7 T8 T10; do
  echo ">>> Procesando Torre $t..."
  PYTHONPATH=src $PYTHON_BIN -m application.run_tower_pipeline \
    --tower $t \
    --client "${SLUG}" \
    --context-file "${CONTEXT_FILE}" \
    --responses-file "${RESPONSES_FILE}"
done

# --- 3. FASE 3: CONSOLIDACIÓN GLOBAL ---
echo "🌍 FASE 3: Ejecutando Consolidación Global..."
PYTHONPATH=src $PYTHON_BIN -m application.run_global_pipeline "${SLUG}"

# --- 4. FASE 4: REFINADO COMERCIAL Y ACCOUNT PLAN ---
echo "💼 FASE 4: Ejecutando Refinado Comercial (Elite Refactor)..."
PYTHONPATH=src $PYTHON_BIN -m application.run_commercial_pipeline "${SLUG}"

# --- 5. FASE 5: DASHBOARD WEB INTERACTIVO ---
echo "🖥️ FASE 5: Generando Dashboard Web..."
PYTHONPATH=src $PYTHON_BIN -m adapters.render_web_presentation "${SLUG}"

echo "==========================================================="
echo "✅ PROCESO FINALIZADO CON ÉXITO (REDEIA4 - ELITE MODE)"
echo "📂 Resultados disponibles en: ${WORKING_DIR}"
echo "==========================================================="
