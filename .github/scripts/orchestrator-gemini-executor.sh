#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <repo_root> <task_prompt_file> [attempt]" >&2
  exit 2
fi

repo_root=$1
task_prompt_file=$2
attempt=${3:-1}

cd "$repo_root"

if ! command -v gemini >/dev/null 2>&1; then
  echo "gemini command not found for the GitHub Actions executor." >&2
  exit 127
fi

export GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI:-1}
export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-sub403o4u0q5}
export GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION:-europe-west1}

gemini_model=${ASSESSMENT_ORCHESTRATOR_EXECUTOR_MODEL:-gemini-2.5-pro}

if [ "${ORCHESTRATOR_EXECUTOR_PREFLIGHT:-0}" = "1" ]; then
  exec gemini \
    --model "$gemini_model" \
    --skip-trust \
    --approval-mode yolo \
    --output-format text \
    -p "Return exactly OK."
fi

exec gemini \
  --model "$gemini_model" \
  --skip-trust \
  --approval-mode yolo \
  --output-format text \
  -p "$(cat "$task_prompt_file")"
