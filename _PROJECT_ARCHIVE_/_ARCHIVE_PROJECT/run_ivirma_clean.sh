#!/bin/bash
set -e

CLIENT="ivirma"
WORKING_DIR="working/${CLIENT}"
LOG_FILE="execution_${CLIENT}_$(date +%Y%m%d_%H%M%S).log"

echo "--- INICIANDO PROCESO END-TO-END PARA ${CLIENT} ---" | tee -a "$LOG_FILE"
echo "Fecha: $(date)" | tee -a "$LOG_FILE"

# 1. Limpieza segura
echo "1. Realizando limpieza de la carpeta de trabajo..." | tee -a "$LOG_FILE"
if [ -d "$WORKING_DIR" ]; then
    # Crear carpeta temporal para backup de base
    mkdir -p .tmp_backup
    [ -f "$WORKING_DIR/context.txt" ] && cp "$WORKING_DIR/context.txt" .tmp_backup/
    [ -f "$WORKING_DIR/responses.txt" ] && cp "$WORKING_DIR/responses.txt" .tmp_backup/
    
    # Borrar contenido
    rm -rf "${WORKING_DIR:?}"/*
    
    # Restaurar
    [ -f ".tmp_backup/context.txt" ] && mv .tmp_backup/context.txt "$WORKING_DIR/"
    [ -f ".tmp_backup/responses.txt" ] && mv .tmp_backup/responses.txt "$WORKING_DIR/"
    rm -rf .tmp_backup
    echo "   Carpeta limpiada. context.txt y responses.txt preservados." | tee -a "$LOG_FILE"
else
    mkdir -p "$WORKING_DIR"
    echo "   Carpeta no existía. Creada de nuevo." | tee -a "$LOG_FILE"
fi

# 2. Ejecución del Pipeline
echo "2. Lanzando Pipeline..." | tee -a "$LOG_FILE"

# Nota: No llamamos a run_ivirma.sh porque ese genera datos mock. 
# Llamamos directamente a los pasos que procesan tus ficheros reales.

for t in T2 T3 T4 T5 T6 T7 T8 T9; do
  echo ">>> Procesando Torre $t..." | tee -a "$LOG_FILE"
  .venv/bin/python -m assessment_engine.scripts.run_tower_pipeline --tower $t --client ${CLIENT} --context-file ${WORKING_DIR}/context.txt --responses-file ${WORKING_DIR}/responses.txt 2>&1 | tee -a "$LOG_FILE"
done

echo ">>> Consolidando Informe Global..." | tee -a "$LOG_FILE"
.venv/bin/python -m assessment_engine.scripts.run_global_pipeline ${CLIENT} 2>&1 | tee -a "$LOG_FILE"

echo ">>> Generando Refinado Comercial..." | tee -a "$LOG_FILE"
.venv/bin/python -m assessment_engine.scripts.run_commercial_pipeline ${CLIENT} 2>&1 | tee -a "$LOG_FILE"

echo "--- ✅ PROCESO FINALIZADO ---" | tee -a "$LOG_FILE"
echo "Log guardado en: $LOG_FILE"
