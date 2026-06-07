#!/bin/bash
set -e
CLIENT_NAME="REDEIA"
SLUG="redeia3"
WORKING_DIR="working/${SLUG}"
PYTHON_BIN="./.venv/bin/python"
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
export GOOGLE_APPLICATION_CREDENTIALS=/home/jsanchhi/.secrets/sa-key.json
CONTEXT_FILE="${WORKING_DIR}/260601 Documento de contexto Redeia 2.docx"
RESPONSES_FILE="${WORKING_DIR}/260601 Respuestas Test Redeia 2.txt"
echo "🔄 REANUDANDO PROCESO PARA ${SLUG} (Desde T4)..."
for t in T4 T5 T6 T7 T8 T10; do
  echo ">>> Procesando Torre $t..."
  $PYTHON_BIN -m application.run_tower_pipeline --tower $t --client "${SLUG}" --context-file "${CONTEXT_FILE}" --responses-file "${RESPONSES_FILE}"
done
$PYTHON_BIN -m application.run_global_pipeline "${SLUG}"
$PYTHON_BIN -m application.run_commercial_pipeline "${SLUG}"
$PYTHON_BIN -m adapters.render_web_presentation "${SLUG}"
echo "✅ FINALIZADO"
