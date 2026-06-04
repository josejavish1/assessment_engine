#!/bin/bash
set -e

CLIENT="REDEIA"
SLUG="redeia"
WORKING_DIR="working/${SLUG}"

echo "🔨 Restaurando archivos de entrada..."
cp "working/REDEIA/260601 Documento de contexto Redeia 2.docx" "${WORKING_DIR}/"
cp "working/REDEIA/260601 Respuestas Test Redeia 2.txt" "${WORKING_DIR}/"

CONTEXT_FILE="${WORKING_DIR}/260601 Documento de contexto Redeia 2.docx"
RESPONSES_FILE="${WORKING_DIR}/260601 Respuestas Test Redeia 2.txt"

echo "🚀 Iniciando Pipeline de ALTA CALIDAD para ${CLIENT}..."

# 1. Procesar Torres (Fase 2) - Ahora detectará client_intelligence.json en ${WORKING_DIR}
for t in T2 T4 T5 T6 T7 T8 T10; do
  echo ">>> Procesando Torre $t con Inteligencia Estratégica..."
  ./.venv/bin/python -m assessment_engine.scripts.run_tower_pipeline \
    --tower $t \
    --client ${CLIENT} \
    --context-file "${CONTEXT_FILE}" \
    --responses-file "${RESPONSES_FILE}"
done

# 2. Consolidación Global (Fase 3)
echo ">>> Ejecutando Consolidación Global..."
./.venv/bin/python -m assessment_engine.scripts.run_global_pipeline ${SLUG}

# 3. Refinado Comercial (Fase 4)
echo ">>> Ejecutando Refinado Comercial..."
./.venv/bin/python -m assessment_engine.scripts.run_commercial_pipeline ${SLUG}

# 4. Dashboard Web (Fase 5)
echo ">>> Generando Dashboard Web..."
./.venv/bin/python -m assessment_engine.scripts.render_web_presentation ${SLUG}

echo "=== ✅ PROCESO DE ALTA CALIDAD COMPLETADO ==="
