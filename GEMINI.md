---
status: Verified
owner: docs-governance
source_of_truth:
- docs/ai/documentation-governance.md
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
- src/
last_verified_against: 2026-06-26
applies_to:
- gemini
doc_type: operational
diataxis: how_to
verification_mode: editorial
---
# Gemini adapter

Este archivo debe leerse como **adaptador operativo breve para Gemini**, no como documentación canónica del proyecto.

## Herencia de Gobernanza (Estricto)

Como agente de Google, **DEBES leer y someterte obligatoriamente a las Leyes de Ingeniería No Negociables y el Checklist de Disciplina de Cambio definidos en [AGENTS.md](AGENTS.md)**. Esas leyes de calidad son absolutas e inmutables para esta base de código.

### Desacoplamiento Lingüístico Obligatorio (Language Decoupling Law)
- **Regla Inmutable:** Aunque el usuario interactúe en español en el chat, **NUNCA** debes escribir código, comentarios, docstrings, excepciones, logs, prompts o tests en español.
- **Todo artefacto de ingeniería debe ser 100% Technical English.**
- El español u otros idiomas solo existen como datos en `engine_config/locales.json` para renderizar informes al cliente final cuando este lo solicite con un parámetro explícito.
- Prohibido hardcodear `locale="es"` o usar `"es"` como valor por defecto en firmas de funciones; el valor por defecto del sistema es siempre `"en"`.

## Orden de lectura

1. [README.md](README.md)
2. [docs/README.md](docs/README.md)
3. [docs/ai/documentation-governance.md](docs/ai/documentation-governance.md)
4. [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)
5. el documento canónico más cercano al cambio

## Reglas

- no uses este archivo como fuente única de verdad;
- apóyate en código, tests, schemas y workflows reales;
- cuando una afirmación no pueda verificarse, trátala como `Needs Review`;
- no acumules aquí arquitectura detallada, roadmap ni memoria histórica del proyecto;
- si el cambio toca arquitectura, contratos, operación o gobernanza, actualiza la documentación canónica correspondiente.

## Nota de transición

`GEMINI.md` contenía memoria operativa histórica útil, pero parte de ese contenido mezclaba estado actual con visión futura. Esa lectura debe considerarse superada por la base común en `docs/`.
