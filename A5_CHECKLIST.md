# A5. Checklist de cambio para agentes IA

Todo agente de IA (o desarrollador) que intervenga en el pipeline del Assessment Engine DEBE seguir estas reglas de seguridad operativa antes de dar por completado un cambio. El objetivo principal es **prevenir la regresión silenciosa** (evitar romper otras partes del sistema sin saberlo).

## 1. Alcance y Contexto
- [ ] Has leído el fichero `GEMINI.md` de la raíz del proyecto para comprender el propósito del sistema y la arquitectura aprobada.
- [ ] Tu propuesta de cambio tiene un alcance justificado (por ejemplo, corrige un bug o modulariza un componente existente). No introduces grandes refactorizaciones a la vez sin pruebas de contención.

## 2. Si modificas PROMPTS (`prompts/registry/*.yaml` o python)
- [ ] Has ejecutado `tests/test_prompt_registry.py` para asegurar que el YAML o sintaxis no está roto.
- [ ] Has evaluado si el cambio alterará la estructura del output. En caso afirmativo, ¿has validado que los scripts de renderizado *downstream* aguanten el nuevo payload?

## 3. Si modificas MAPEOS O PAYLOADS (`build_tower_annex_template_payload.py`, etc.)
- [ ] El payload resultante sigue la estructura Pydantic definida en los esquemas correspondientes.
- [ ] Los tests de Golden (por ejemplo, `tests/test_t5_golden.py`) que comprueban que el payload de T5 no ha mutado inesperadamente **siguen pasando en verde**.

## 4. Si modificas el RENDER O GENERACIÓN DOCX
- [ ] Has vuelto a generar los documentos de humo (smoke tests) para T5: `Blueprint` y `Annex`.
- [ ] Has revisado visualmente o mediante `tests/test_document_integrity.py` que no haya *placeholders* sueltos y que las imágenes estén incrustadas correctamente en el DOCX.
- [ ] El documento no rompe XML ni el formato al abrirse con Microsoft Word.

## 5. Validaciones Generales (Pipeline Completo)
Antes de confirmar que una refactorización está acabada, debes ejecutar obligatoriamente (con el venv correcto de Python):
```bash
./.venv/bin/python -m pytest tests/test_t5_golden.py tests/test_prompt_registry.py tests/test_document_integrity.py -q
```
- [ ] Todos los tests regresan en OK.

## 6. Actualización del Registro de Memoria (GEMINI.md)
- [ ] Tras haber verificado que los documentos DOCX renderizan bien y que los tests pasan, has añadido un punto en la sección `13. Diario de Refactorización` de `GEMINI.md` documentando tu cambio.
