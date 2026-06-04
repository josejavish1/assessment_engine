#!/bin/bash
set -e

# IMPORTANTE: Usamos el slug en minúsculas que generó el motor de torres
CLIENT_SLUG="redeia"
CLIENT_DISPLAY="REDEIA"
WORKING_DIR="working/${CLIENT_SLUG}"

echo "Reanudando proceso para ${CLIENT_DISPLAY} en ${WORKING_DIR}..."

if [ ! -d "${WORKING_DIR}" ]; then
  echo "❌ Error: No existe el directorio ${WORKING_DIR}"
  exit 1
fi

echo "3/5 Ejecutando Consolidación Global..."
./.venv/bin/python -m assessment_engine.scripts.run_global_pipeline ${CLIENT_SLUG}

echo "4/5 Ejecutando Refinado Comercial y Account Action Plan..."
./.venv/bin/python -m assessment_engine.scripts.run_commercial_pipeline ${CLIENT_SLUG}

echo "5/5 Generando Dashboard Web..."
./.venv/bin/python -m assessment_engine.scripts.render_web_presentation ${CLIENT_SLUG}

echo "=== ✅ PROCESO DE RECUPERACIÓN COMPLETADO ==="
