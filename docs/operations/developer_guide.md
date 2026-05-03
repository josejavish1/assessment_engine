# Guía del Desarrollador: Operaciones Comunes

Este documento centraliza las guías para las operaciones de desarrollo más comunes, asegurando que todos los miembros del equipo sigan prácticas estandarizadas y seguras.

## Saneamiento del Entorno de Desarrollo

Mantener un worktree limpio es crucial para asegurar la reproducibilidad de los tests y evitar el "commit" de artefactos no deseados. Con el tiempo, archivos generados como cachés de Python (`__pycache__`), resultados de builds o logs pueden acumularse.

### El Script `clean.sh` (Método Recomendado)

Para estandarizar y asegurar el proceso de limpieza, el proyecto proporciona un script dedicado en `scripts/ops/clean.sh`. Este script es la **única forma recomendada** para limpiar el worktree.

#### Propósito

El script `clean.sh` automatiza la eliminación de artefactos de build y archivos temporales de una manera controlada. Ofrece dos modos de operación para adaptarse a diferentes necesidades de limpieza.

#### Uso Básico (Limpieza Estándar)

Esta es la operación de limpieza más común. Elimina los artefactos generados que no están rastreados por Git, pero **respeta los archivos listados en `.gitignore`**. Esto significa que no borrará tus ficheros de entorno (como `.env`) o configuraciones de IDE.

Para ejecutar la limpieza estándar:
```bash
./scripts/ops/clean.sh
```

#### Uso Avanzado (Limpieza Completa)

En ocasiones, puede ser necesario realizar una limpieza completa que elimine **absolutamente todo** lo que no está bajo control de versiones, incluyendo los archivos ignorados por `.gitignore`. Esto es útil para simular un "fresh clone" del repositorio sin tener que volver a clonarlo.

**Advertencia:** Este comando es destructivo. Usar con precaución.

Para ejecutar la limpieza completa:
```bash
./scripts/ops/clean.sh --full
```

### Riesgos del Uso Manual de `git clean` (Desaconsejado)

Aunque el script `clean.sh` utiliza `git clean` internamente, su uso directo desde la línea de comandos está **fuertemente desaconsejado**, especialmente con el flag `-x`.

El comando `git clean -fdx` es extremadamente potente y peligroso si no se comprende completamente. Borrará de forma recursiva y forzada cada archivo y directorio que no esté bajo control de versiones o ignorado. Un error al usarlo podría llevar a la pérdida de:
-   Variables de entorno no guardadas (`.env`).
-   Configuraciones locales del IDE.
-   Scripts o notas personales que aún no se han añadido a `.gitignore`.

Utiliza siempre `./scripts/ops/clean.sh` para evitar accidentes y garantizar un comportamiento consistente en todo el equipo.
