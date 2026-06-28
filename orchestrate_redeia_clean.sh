#!/usr/bin/env bash
# ==============================================================================
# Script: orchestrate_redeia_clean.sh
# Purpose: Simple and safe orchestrator for a 100% clean Redeia run.
#          It leaves the old v3 aside (moves it to working/redeia_v3_backup)
#          and runs the pipeline natively on working/redeia_v3 from scratch.
# ==============================================================================

# Exit immediately if a command exits with a non-zero status
set -eo pipefail

# Define text colors for clear console output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}        REDEIA CLEAN PIPELINE RUN (v3 left aside)                     ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Ensure we are in the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${REPO_ROOT}"

# Step 0.1: Source environmental settings if they exist
if [ -f ".assessment_env.sh" ]; then
    echo -e "${GREEN}[+] Sourcing cloud project environment variables...${NC}"
    source .assessment_env.sh
else
    echo -e "${YELLOW}[!] Warning: .assessment_env.sh not found. Proceeding with existing environment.${NC}"
fi

# Step 0.1.1: Resolve permanent Google Application Credentials if not set
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
    FALLBACK_CREDENTIALS="${HOME}/.secrets/sa-key.json"
    if [ -f "${FALLBACK_CREDENTIALS}" ]; then
        echo -e "${GREEN}[+] Found permanent GCP Service Account key at: ${FALLBACK_CREDENTIALS}${NC}"
        export GOOGLE_APPLICATION_CREDENTIALS="${FALLBACK_CREDENTIALS}"
    else
        echo -e "${YELLOW}[!] Warning: No GCP service account key found at standard path ${FALLBACK_CREDENTIALS}.${NC}"
    fi
fi

# Configure larger timeout for deep AI analysis steps on complex documents
export ASSESSMENT_AI_STEP_TIMEOUT_SECONDS=600
echo -e "${GREEN}[+] Configured ASSESSMENT_AI_STEP_TIMEOUT_SECONDS=600 for deep qualitative analysis.${NC}"

# Step 0.2: Resolve Python Interpreter (prefer local .venv)
if [ -d ".venv" ]; then
    PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
    echo -e "${GREEN}[+] Using virtual environment interpreter: ${PYTHON_BIN}${NC}"
else
    PYTHON_BIN="python3"
    echo -e "${YELLOW}[!] Warning: .venv not found. Falling back to system python3.${NC}"
fi

# Step 0.3: Vertex AI Preflight Check
echo -e "${GREEN}[+] Running Vertex AI preflight diagnostics...${NC}"
if ! "${PYTHON_BIN}" -m assessment_engine.application.tools.check_vertex_ai_access; then
    echo -e "${RED}[-] Vertex AI preflight failed. Please verify your GCP/Vertex credentials before running.${NC}"
    exit 1
fi

# Paths definitions
CLIENT_DIR="${REPO_ROOT}/working/redeia_v3"
BACKUP_DIR="${REPO_ROOT}/working/redeia_v3_backup"
SOURCE_DIR="${CLIENT_DIR}/redeia"

# Step 0.4: Check and move existing v3 aside
if [ -d "${CLIENT_DIR}" ]; then
    if [ -f "${CLIENT_DIR}/redeia/context_redeia.docx" ] && [ -f "${CLIENT_DIR}/redeia/preguntas_redeia_con_notas.txt" ]; then
        if [ ! -d "${BACKUP_DIR}" ]; then
            echo -e "${GREEN}[+] Leaving old v3 folder aside at: ${BACKUP_DIR}${NC}"
            mv "${CLIENT_DIR}" "${BACKUP_DIR}"
        else
            echo -e "${YELLOW}[!] Backup directory already exists. We will reuse it and purge current sparse working directory.${NC}"
            rm -rf "${CLIENT_DIR}"
        fi
    else
        echo -e "${RED}[-] Critical Error: Source files not found in ${CLIENT_DIR}/redeia.${NC}"
        exit 1
    fi
else
    # If no v3 exists, check if backup already exists to recover sources
    if [ ! -d "${BACKUP_DIR}" ]; then
        echo -e "${RED}[-] Critical Error: No working/redeia_v3 nor working/redeia_v3_backup found to extract sources.${NC}"
        exit 1
    fi
    echo -e "${GREEN}[+] Previous backup folder found. We will use its sources.${NC}"
fi

# Step 0.5: Create clean new v3 workspace and restore source documents
echo -e "${GREEN}[+] Initializing fresh working/redeia_v3 directory...${NC}"
mkdir -p "${SOURCE_DIR}"
cp "${BACKUP_DIR}/redeia/context_redeia.docx" "${SOURCE_DIR}/"
cp "${BACKUP_DIR}/redeia/preguntas_redeia_con_notas.txt" "${SOURCE_DIR}/"
echo -e "${GREEN}[✓] Raw source files restored to pristine workspace: ${SOURCE_DIR}${NC}"


# ==============================================================================
# PHASE 1: Document Ingestion (Evidence & Raptor Engine)
# ==============================================================================
echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}  PHASE 1: Ingesting Documents (Evidence & Raptor RAG Tree)           ${NC}"
echo -e "${BLUE}======================================================================${NC}"

"${PYTHON_BIN}" -m assessment_engine.application.tools.ingest_redeia

# Quick verification of Phase 1 outputs
if [ -f "${SOURCE_DIR}/evidence_vault.json" ] && [ -f "${SOURCE_DIR}/raptor_tree.json" ]; then
    echo -e "${GREEN}[✓] Phase 1 Ingestion Completed. RAG Tree and Evidence Vault generated.${NC}"
else
    echo -e "${RED}[-] Error: Phase 1 output verification failed.${NC}"
    exit 1
fi


# ==============================================================================
# PHASE 2: Client Intelligence Harvesting
# ==============================================================================
echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}  PHASE 2: Client Intelligence Harvesting                             ${NC}"
echo -e "${BLUE}======================================================================${NC}"

"${PYTHON_BIN}" -m assessment_engine.application.run_intelligence_harvesting redeia_v3

# Quick verification of Phase 2 outputs
if [ -f "${CLIENT_DIR}/client_intelligence.json" ]; then
    echo -e "${GREEN}[✓] Phase 2 Completed. client_intelligence.json generated successfully.${NC}"
else
    echo -e "${RED}[-] Error: Phase 2 output verification failed.${NC}"
    exit 1
fi


# ==============================================================================
# PHASE 3: Technical Tower Pipelines
# ==============================================================================
echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}  PHASE 3: Running Technical Towers Diagnostic Pipelines              ${NC}"
echo -e "${BLUE}======================================================================${NC}"

TOWERS=("T1" "T2" "T4" "T5" "T6" "T7" "T8" "T10")

for tower in "${TOWERS[@]}"; do
    echo -e "\n${YELLOW}▶ Processing Tower ${tower}...${NC}"
    echo "--------------------------------------------------------"
    
    "${PYTHON_BIN}" -m assessment_engine.application.run_tower_pipeline \
        --tower "${tower}" \
        --client "redeia_v3" \
        --context-file "${SOURCE_DIR}/context_redeia.docx" \
        --responses-file "${SOURCE_DIR}/preguntas_redeia_con_notas.txt"
        
    # Quick verification of Tower output
    BLUEPRINT_FILE="${CLIENT_DIR}/${tower}/blueprint_$(echo "${tower}" | tr '[:upper:]' '[:lower:]')_payload.json"
    if [ -f "${BLUEPRINT_FILE}" ]; then
        echo -e "${GREEN}[✓] Tower ${tower} completed successfully. Blueprint generated.${NC}"
    else
        echo -e "${RED}[-] Error: Tower ${tower} pipeline did not generate expected blueprint payload.${NC}"
        exit 1
    fi
done


# ==============================================================================
# PHASE 4: Global Consolidated Pipeline
# ==============================================================================
echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}  PHASE 4: Executing Global Executive Consolidation                   ${NC}"
echo -e "${BLUE}======================================================================${NC}"

"${PYTHON_BIN}" -m assessment_engine.application.run_global_pipeline redeia_v3

# Quick verification of Phase 4 outputs
if [ -f "${CLIENT_DIR}/global_report_payload.json" ] && [ -f "${CLIENT_DIR}/Global_AS-IS_Consolidado.docx" ] && [ -f "${CLIENT_DIR}/Global_TO-BE_Consolidado.docx" ]; then
    echo -e "${GREEN}[✓] Phase 4 Consolidated Global Pipeline Completed successfully.${NC}"
else
    echo -e "${RED}[-] Error: Phase 4 output verification failed.${NC}"
    exit 1
fi


# ==============================================================================
# PHASE 5: Commercial Account Action Plan Pipeline
# ==============================================================================
echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}  PHASE 5: Running Commercial Refiner & Account Action Plan          ${NC}"
echo -e "${BLUE}======================================================================${NC}"

"${PYTHON_BIN}" -m assessment_engine.application.run_commercial_pipeline redeia_v3

# Quick verification of Phase 5 outputs
if [ -f "${CLIENT_DIR}/commercial_report_payload.json" ] && [ -f "${CLIENT_DIR}/Account_Action_Plan_redeia.docx" ]; then
    echo -e "${GREEN}[✓] Phase 5 Commercial Pipeline Completed successfully.${NC}"
else
    echo -e "${RED}[-] Error: Phase 5 output verification failed.${NC}"
    exit 1
fi


# ==============================================================================
# PHASE 6: Interactive Web Dashboard presentation
# ==============================================================================
echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${BLUE}  PHASE 6: Composing Interactive Web Presentation Dashboard         ${NC}"
echo -e "${BLUE}======================================================================${NC}"

"${PYTHON_BIN}" -m assessment_engine.adapters.render_web_presentation redeia_v3

# Quick verification of Phase 6 outputs
if [ -f "${CLIENT_DIR}/presentation/index.html" ]; then
    echo -e "${GREEN}[✓] Phase 6 Web Presentation Dashboard generated successfully.${NC}"
else
    echo -e "${RED}[-] Error: Phase 6 output verification failed.${NC}"
    exit 1
fi


# ==============================================================================
# SUMMARY
# ==============================================================================
echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}      ✓ EXTREME CLEAN PIPELINE RUN COMPLETED SUCCESSFULLY FOR REDEIA     ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "Generated Deliverables Summary in ${CLIENT_DIR}:"
echo -e " - ${BLUE}Client Dossier:${NC} client_intelligence.json"
echo -e " - ${BLUE}Technical Blueprints:${NC} in T1, T2, T4, T5, T6, T7, T8, T10 directories"
echo -e " - ${BLUE}Global AS-IS Report Docx:${NC} Global_AS-IS_Consolidado.docx"
echo -e " - ${BLUE}Global TO-BE Report Docx:${NC} Global_TO-BE_Consolidado.docx"
echo -e " - ${BLUE}Global Report Payload:${NC} global_report_payload.json"
echo -e " - ${BLUE}Account Action Plan Docx:${NC} Account_Action_Plan_redeia.docx"
echo -e " - ${BLUE}Commercial Report Payload:${NC} commercial_report_payload.json"
echo -e " - ${BLUE}Web Dashboard Index:${NC} presentation/index.html"
echo -e "======================================================================"
echo -e "${YELLOW}[i] The old v3 directory is untouched and left aside at: ${BACKUP_DIR}${NC}"
echo -e "======================================================================"
exit 0
