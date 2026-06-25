#!/bin/bash
set -e

# --- CONFIGURACIÓN DE RUTAS ---
CLIENT_NAME="redeia_test"
SLUG="redeia_test"
WORKING_DIR="working/${SLUG}"
PYTHON_BIN="./.venv/bin/python"

# --- 1. PREPARACIÓN Y LIMPIEZA ---
echo "🧹 Limpiando entorno para asegurar regeneración limpia..."
rm -rf "${WORKING_DIR}"
mkdir -p "${WORKING_DIR}"

# Restaurar archivos base desde la carpeta original
echo "📥 Asegurando archivos de inteligencia y contexto..."
cp "working/REDEIA/client_intelligence.json" "${WORKING_DIR}/"
cp "working/REDEIA/260601 Documento de contexto Redeia 2.docx" "${WORKING_DIR}/"
cp "working/REDEIA/260601 Respuestas Test Redeia 2.txt" "${WORKING_DIR}/"

CONTEXT_FILE="${WORKING_DIR}/260601 Documento de contexto Redeia 2.docx"
RESPONSES_FILE="${WORKING_DIR}/260601 Respuestas Test Redeia 2.txt"

# --- 2. FASE 2: TORRES TÉCNICAS (SOLO T2 PARA TEST) ---
echo "🏗️ FASE 2: Generando Torre Técnica T2 (Refactored)..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
$PYTHON_BIN -m application.run_tower_pipeline \
    --tower T2 \
    --client "${CLIENT_NAME}" \
    --context-file "${CONTEXT_FILE}" \
    --responses-file "${RESPONSES_FILE}"

# --- 3. FASE 3: CONSOLIDACIÓN GLOBAL ---
echo "🌍 FASE 3: Ejecutando Consolidación Global..."
$PYTHON_BIN -m application.run_global_pipeline "${SLUG}"

# --- 4. FASE 4: REFINADO COMERCIAL Y ACCOUNT PLAN ---
echo "💼 FASE 4: Ejecutando Refinado Comercial..."
$PYTHON_BIN -m application.run_commercial_pipeline "${SLUG}"

# --- 5. FASE 5: DASHBOARD WEB INTERACTIVO ---
echo "🖥️ FASE 5: Generando Dashboard Web..."
$PYTHON_BIN -m application.render_web_presentation "${SLUG}"

echo "==========================================================="
echo "✅ PROCESO DE TEST FINALIZADO CON ÉXITO"
echo "📂 Resultados disponibles en: ${WORKING_DIR}"
echo "==========================================================="
