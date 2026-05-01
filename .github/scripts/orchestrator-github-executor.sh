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

copilot_auth_token=${COPILOT_REQUESTS_TOKEN:-${GITHUB_TOKEN:-${GH_TOKEN:-}}}
if [ -z "$copilot_auth_token" ]; then
  echo "COPILOT_REQUESTS_TOKEN or GITHUB_TOKEN is required for the GitHub Actions executor." >&2
  exit 2
fi

export GH_TOKEN="$copilot_auth_token"
export GITHUB_TOKEN="$copilot_auth_token"

exec copilot \
  --model gpt-5.4 \
  --allow-all \
  --no-ask-user \
  --silent \
  --log-level error \
  --name "orchestrator-pr-reconcile-${attempt}" \
  -p "$(cat "$task_prompt_file")"
