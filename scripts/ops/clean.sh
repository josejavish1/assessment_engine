#!/bin/bash
#
# Saneamiento controlado del worktree para eliminar artefactos generados.
#
# Este script proporciona un método estandarizado y seguro para limpiar el
# worktree de cachés, artefactos de build y archivos no rastreados por Git.
#
# Uso:
#   ./scripts/ops/clean.sh         -> Limpieza estándar (respeta .gitignore)
#   ./scripts/ops/clean.sh --full  -> Limpieza completa (elimina también ignorados)
#

set -e # Abortar si cualquier comando falla

# Navegar a la raíz del proyecto para asegurar que los paths son correctos
cd "$(dirname "$0")/../../"

echo "INFO: Iniciando saneamiento del worktree..."

# --- Limpieza de Artefactos de Python y Build ---

echo "INFO: Eliminando cachés de Python (__pycache__)..."
find . -type d -name "__pycache__" -exec rm -r {} +

echo "INFO: Eliminando cachés de Pytest (.pytest_cache)..."
rm -rf .pytest_cache

echo "INFO: Eliminando artefactos de build (build/, dist/, *.egg-info)..."
rm -rf build/
rm -rf dist/
rm -rf ./*.egg-info

# --- Limpieza con Git ---

# Por defecto, git clean no elimina archivos ignorados.
# El flag --full activa la limpieza de archivos ignorados también.
if [[ "$1" == "--full" ]]; then
  echo "INFO: Ejecutando limpieza completa con 'git clean -fdx' (incluye ignorados)..."
  git clean -fdx
else
  echo "INFO: Ejecutando limpieza estándar con 'git clean -fd' (respeta ignorados)..."
  git clean -fd
fi

echo "SUCCESS: Saneamiento del worktree completado."
git status --short
