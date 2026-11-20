#!/usr/bin/env bash
# Assessment Engine runtime environment bootstrap
# Portable default values with environment variable overrides

export GOOGLE_GENAI_USE_VERTEXAI="${GOOGLE_GENAI_USE_VERTEXAI:-0}"
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-sub403o4u0q5}"
export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
export GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-${HOME}/.secrets/sa-key.json}"
export AI_FAST_MODEL="${AI_FAST_MODEL:-gemini-3.8-flash}"
export AI_REASONING_MODEL="${AI_REASONING_MODEL:-gemini-4-argon}"
