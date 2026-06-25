#!/bin/bash
set -e

CLIENT_NAME="REDEIA"
SLUG="redeia"
WORKING_DIR="working/${SLUG}"
PYTHON_BIN="./.venv/bin/python"
CONTEXT_FILE="${WORKING_DIR}/260601 Documento de contexto Redeia 2.docx"
RESPONSES_FILE="${WORKING_DIR}/260601 Respuestas Test Redeia 2.txt"

echo "🎯 Finalizando Torre T7..."
$PYTHON_BIN -m assessment_engine.scripts.run_tower_pipeline \
    --tower T7 \
    --client "${CLIENT_NAME}" \
    --context-file "${CONTEXT_FILE}" \
    --responses-file "${RESPONSES_FILE}" \
    --start-from "Render short DOCX"

echo "🏗️ Procesando Torres restantes..."
for t in T8 T10; do
  echo ">>> Procesando Torre $t..."
  $PYTHON_BIN -m assessment_engine.scripts.run_tower_pipeline \
    --tower $t \
    --client "${CLIENT_NAME}" \
    --context-file "${CONTEXT_FILE}" \
    --responses-file "${RESPONSES_FILE}"
done

echo "🌍 FASE 3: Ejecutando Consolidación Global..."
$PYTHON_BIN -m assessment_engine.scripts.run_global_pipeline "${SLUG}"

echo "💼 FASE 4: Ejecutando Refinado Comercial..."
$PYTHON_BIN -m assessment_engine.scripts.run_commercial_pipeline "${SLUG}"

echo "🖥️ FASE 5: Generando Dashboard Web..."
$PYTHON_BIN -m assessment_engine.scripts.render_web_presentation "${SLUG}"

echo "==========================================================="
echo "✅ PROCESO FINALIZADO CON ÉXITO"
echo "==========================================================="
