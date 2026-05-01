---
status: Verified
owner: docs-governance
source_of_truth:
  - ../../AGENTS.md
  - ../../.github/copilot-instructions.md
  - ../../.github/pull_request_template.md
  - ../../docs/operations/engineering-quality-gates.md
  - ../../src/assessment_engine/
  - ../../tests/
  - ../../.github/workflows/ci.yml
  - ../../.github/workflows/quality.yml
  - ../../.github/workflows/typing.yml
last_verified_against: 2026-05-01
applies_to:
  - humans
  - ai-agents
doc_type: canonical
---

# Agentic development workflow

Esta guía define cómo debe desarrollarse software en `assessment-engine` cuando intervienen agentes de IA. El objetivo no es solo generar código más rápido, sino evitar deriva arquitectónica, duplicación semántica y cambios grandes mal especificados.

## Regla principal

El agente no debe trabajar sobre instrucciones vagas. Debe trabajar sobre una **spec mínima verificable**, dentro de un **alcance acotado**, con **reglas ejecutables** y con **review humano centrado en semántica y arquitectura**.

## Flujo recomendado

### 1. Especificar antes de implementar

Antes de tocar código, deja clara al menos esta información:

- problema concreto;
- alcance incluido;
- alcance explícitamente fuera;
- contratos o documentos canónicos afectados;
- invariantes que no deben romperse;
- validación esperada.

Una spec mínima válida para una PR o sesión debe responder a estas preguntas:

1. ¿Qué cambio real se busca?
2. ¿Qué no se debe tocar?
3. ¿Qué fuente de verdad manda?
4. ¿Qué reglas de dominio deben seguir intactas?
5. ¿Cómo se detectará que el cambio degradó el sistema?

## Plantilla mínima de spec

```text
Problema:
- qué está mal o qué capacidad falta

In scope:
- cambios permitidos

Out of scope:
- cambios que no deben entrar en esta iteración

Source of truth:
- código, schemas, workflows o documentos canónicos que mandan

Invariantes:
- reglas que deben seguir siendo ciertas tras el cambio

Validación:
- tests, checks o artefactos que deben pasar
```

## Reglas de alcance

- prioriza cambios pequeños, reversibles y con frontera clara;
- no mezcles refactor, feature nueva y rediseño semántico en una sola iteración si no es necesario;
- si un cambio cruza varias capas, identifica primero qué helper o policy compartida debe absorber la lógica;
- si una sesión necesita varias fases, mantén la spec y la trazabilidad vivas durante toda la ejecución.

## Qué se considera best practice en este repo

- una única fuente de verdad por semántica crítica;
- lógica importante fuera de prompts y dentro de código, tests, schemas o workflows;
- helpers o policies compartidas para reglas reutilizadas;
- errores explícitos en zonas críticas en lugar de degradaciones silenciosas;
- tests de coherencia cuando la semántica atraviesa varias capas;
- cambios guiados por contratos y no por “texto que parece razonable”.

## Qué se considera mala práctica

- dejar lógica de negocio solo en prompts;
- duplicar score, target, band, color, severidad o prioridades en varios sitios;
- meter defaults silenciosos en zonas críticas;
- capturar errores amplios sin señal auditable;
- cambiar más superficie de la necesaria;
- introducir una segunda fuente de verdad “temporal” que luego se queda.

## Review humano esperado

En PR review, el foco principal no debe ser estilo superficial, sino estas preguntas:

1. ¿La PR parte de una spec clara?
2. ¿El alcance es razonable o intenta hacer demasiadas cosas?
3. ¿Se ha duplicado lógica existente en vez de reutilizar helpers o policies?
4. ¿Se ha introducido una nueva fuente de verdad?
5. ¿Se han protegido las invariantes con tests o checks?
6. ¿La documentación canónica y la trazabilidad siguen alineadas?
7. ¿El agente pudo haber generado código correcto en apariencia pero semánticamente equivocado?

## Relación con los gates automáticos

Los gates automáticos actuales (`pytest`, `quality`, `typing`, gobernanza documental) son necesarios, pero no suficientes por sí solos.

El workflow correcto es:

1. spec mínima;
2. cambio acotado;
3. implementación con helpers/policies/contratos;
4. tests y checks;
5. review humano orientado a arquitectura y semántica;
6. si la PR recibe feedback automático o de review, nueva iteración de corrección sin saltarse los mismos gates;
7. merge solo cuando GitHub deja la PR verde y sin conversaciones bloqueantes.

Si un agente automatiza el post-PR reconciliation, su mandato no es “forzar el merge”, sino exactamente esto:

- leer checks y review threads;
- corregir en la rama;
- rerun de validaciones locales del repo;
- push del follow-up;
- esperar de nuevo los checks oficiales;
- detenerse si la PR sigue bloqueada por reglas humanas o de protección que no puede satisfacer legítimamente.

## Regla operativa para agentes

Si una sesión con agente no puede responder con claridad qué cambia, qué no cambia, qué fuente de verdad manda y qué invariantes protege, la sesión todavía no está lista para implementar.

## Traducción desde lenguaje product owner

Cuando la petición venga desde negocio y no desde un programador, el flujo recomendado no es pedir directamente “haz el cambio”, sino usar el orquestador descrito en `product-owner-orchestrator.md`.

Ese orquestador convierte la intención de negocio en:

- spec mínima;
- tareas pequeñas;
- validación estándar;
- PR con trazabilidad.
