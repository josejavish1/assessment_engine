#!/bin/bash
set -e

echo "============================================================"
echo "1. LIMPIEZA DEL ESPACIO DE TRABAJO"
echo "============================================================"
rm -rf working/out/Molins_Entrega_Cliente_Final

echo "============================================================"
echo "2. REGENERACIÓN DESDE CERO (AST A DOCX) SIN CHEATS"
echo "============================================================"
# Restore original blue_prints for Molins to clear harmonized cheats
git restore working/molins/*/blueprint_*_payload.json || true
env PYTHONPATH=src .venv/bin/python scripts/regenerate_molins_pure_from_raw_inputs.py

echo "============================================================"
echo "3. AUDITORÍA DEL TRIBUNAL DE EXPERTOS SOBRE LOS DOCX PUROS"
echo "============================================================"
env PYTHONPATH=src .venv/bin/python scripts/audit_ten_towers_top_tier_tribunal.py

echo "============================================================"
echo "4. ENSAMBLAJE DEL NUEVO DOSSIER PARA EVALUACIÓN EXTERNA"
echo "============================================================"
DOSSIER="evaluations/molins_raw_engine_dossier"
rm -rf $DOSSIER
mkdir -p $DOSSIER/01_INPUTS
mkdir -p $DOSSIER/02_RAW_GENERATED_DELIVERABLES
mkdir -p $DOSSIER/03_TRIBUNAL_AUDITS_AND_SCORES

# 4.1 Entradas
cp "source_docs/molins/260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx" $DOSSIER/01_INPUTS/260721_Transcripcion.docx
cp "source_docs/molins/261014 Respuestas Test Molins.txt" $DOSSIER/01_INPUTS/261014_Respuestas.txt

# 4.2 Entregables Puros
cp working/out/Molins_Entrega_Cliente_Final/01_DIAGNOSTICO_GLOBAL/*.docx $DOSSIER/02_RAW_GENERATED_DELIVERABLES/
cp working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS/*.docx $DOSSIER/02_RAW_GENERATED_DELIVERABLES/

# 4.3 Auditorías
cp docs/audits/tribunal_10_towers/AUDIT_EXPERT_*.md $DOSSIER/03_TRIBUNAL_AUDITS_AND_SCORES/
cp docs/audits/ARGON_10_TOWERS_TOP_TIER_TRIBUNAL_CONSOLIDATED.md $DOSSIER/03_TRIBUNAL_AUDITS_AND_SCORES/

# 4.4 README
cat <<EOF > $DOSSIER/README.md
# Raw Assessment Engine Outputs (Pre-Remediation)

This dossier contains the **raw, unedited deliverables** generated directly by the core assessment engine prior to manual surgical fixes, alongside the exact evaluation by the Expert Tribunal.

## Goal for External AI
Evaluate the structural flaws of the generated output (e.g., duplicated P90 values, cookie-cutter "12 hour" Risk Cards, lack of divergence tables) against the Tribunal's strict architectural audit, in order to validate the engine's current state of maturity.
EOF

echo "============================================================"
echo "PROCESO COMPLETADO. LISTO PARA GIT PUSH."
echo "============================================================"
