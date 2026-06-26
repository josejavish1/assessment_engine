#!/bin/bash
# Script para ejecutar el Assessment Pipeline completo para Redeia (Redeia v3 - Optimizado)

CLIENT="REDEIA"
SLUG="redeia"
CONTEXT="working/redeia_v3/redeia/contexto_redeia_elite.docx"
RESPONSES="working/redeia_v3/redeia/preguntas_redeia_con_notas.txt"
TOWERS=("T2" "T4" "T5" "T6" "T7" "T8" "T10")

echo "=========================================================="
echo "   INICIANDO ASSESSMENT ENGINE - REDEIA v3 (CALIDAD MÁXIMA)"
echo "=========================================================="

# --- CONFIGURACIÓN DE AISLAMIENTO FÍSICO ---
export ASSESSMENT_CLIENT_ID="redeia_v3"
export PYTHONPATH=src

# --- LIMPIEZA DE TORRES (Preservando el RAG de la Fase 0) ---
echo "🧹 Limpiando resultados de ejecuciones anteriores de torres (Preservando RAG)..."
for TOWER in "${TOWERS[@]}"; do
    rm -rf "working/redeia_v3/redeia/${TOWER}"
done
rm -f "working/redeia_v3/redeia/client_intelligence.json"
rm -f "working/redeia_v3/redeia/global_report_payload.json"
rm -f "working/redeia_v3/redeia/commercial_report_payload.json"
rm -f "working/redeia_v3/redeia/Account_Action_Plan_REDEIA.docx"
rm -f "working/redeia_v3/redeia/Informe_Ejecutivo_Consolidado_REDEIA.docx"
rm -f "working/redeia_v3/redeia/Interactive_Dashboard.html"

# --- ASEGURAR DIRECTORIO DE ENTRADA ---
mkdir -p "working/redeia_v3/redeia"

# --- COPIA Y CONFIGURACIÓN DE ARCHIVOS DE ENTRADA ---
echo "📥 Asegurando archivos de contexto y preguntas para '$CLIENT'..."
if [ ! -f "working/REDEIA/260601 Documento de contexto Redeia 2.docx" ]; then
    echo "❌ No se encontró el documento de contexto base en working/REDEIA/. Deteniendo."
    exit 1
fi
if [ ! -f "working/REDEIA/260601 Respuestas Test Redeia 2.txt" ]; then
    echo "❌ No se encontraron las respuestas base en working/REDEIA/. Deteniendo."
    exit 1
fi

cp "working/REDEIA/260601 Documento de contexto Redeia 2.docx" "$CONTEXT"
cp "working/REDEIA/260601 Respuestas Test Redeia 2.txt" "$RESPONSES"

source .env
export GOOGLE_APPLICATION_CREDENTIALS=/home/jsanchhi/.secrets/sa-key.json

# --- FASE 0: INGESTA DE DOCUMENTOS (OMITIDA - REUTILIZAMOS RAG PREVIO) ---
echo "⏭️ FASE 0: Reutilizando árbol de conocimiento RAG previo (Aceleración de Coste Cero)..."
if [ ! -f "working/redeia_v3/redeia/raptor_tree.json" ]; then
    echo "⚠️ RAG previo no encontrado. Ejecutando ingesta rápida..."
    ./.venv/bin/python ingest_redeia.py
    if [ $? -ne 0 ]; then
        echo "❌ Fallo en la ingesta. Deteniendo el pipeline."
        exit 1
    fi
fi

# --- FASE 1: COSECHA DE INTELIGENCIA DE MERCADO Y CLIENTE (MESA DE TRABAJO DINÁMICA) ---
echo "🔍 FASE 1: Cosechando Inteligencia Estratégica (Market & Client Intelligence)..."
./.venv/bin/python src/application/run_intelligence_harvesting.py "${CLIENT}" "${CONTEXT}"
if [ $? -ne 0 ]; then
    echo "❌ Fallo en el cosechador de inteligencia. Deteniendo el pipeline."
    exit 1
fi

# --- FASE 2: PIPELINE DE TORRES TÉCNICAS (CON CONTEXTO E INTELIGENCIA) ---
for TOWER in "${TOWERS[@]}"; do
    echo ""
    echo "▶️ PROCESANDO TORRE $TOWER"
    echo "--------------------------------------------------------"
    ./.venv/bin/python src/application/run_tower_pipeline.py \
        --tower "$TOWER" \
        --client "$CLIENT" \
        --context-file "$CONTEXT" \
        --responses-file "$RESPONSES"
        
    if [ $? -ne 0 ]; then
        echo "❌ Fallo en la ejecución de la torre $TOWER. Deteniendo el pipeline."
        exit 1
    fi
done

echo "🌍 FASE 3: Ejecutando Consolidación Global..."
./.venv/bin/python -m src.application.run_global_pipeline "${SLUG}"

echo "💼 FASE 4: Ejecutando Refinado Comercial..."
./.venv/bin/python -m src.application.run_commercial_pipeline "${SLUG}"

echo "🖥️ FASE 5: Generando Dashboard Web..."
./.venv/bin/python -m src.adapters.render_web_presentation "${SLUG}"

echo ""
echo "=========================================================="
echo "✅ EJECUCIÓN DEL PIPELINE COMPLETADA PARA TODAS LAS TORRES"
echo "📂 Resultados generados en: working/redeia_v3/redeia"
echo "=========================================================="
