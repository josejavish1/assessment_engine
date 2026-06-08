# A5. Checklist de cambio para agentes IA

Todo agente de IA (o desarrollador) que intervenga en el pipeline del Assessment Engine DEBE seguir estas reglas de seguridad operativa antes de dar por completado un cambio.

## 1. El contrato es lo primero (Contract-First)
- [x] El esquema Pydantic (`intelligence.py`) define claramente la jerarquía Holding -> Filial.
- [x] Se han añadido los campos `technical_stack` y `field_metrics` como blindaje de información técnica.

## 2. No a la regresión silenciosa
- [x] El motor de Inteligencia V16.1 ha sido verificado mediante la "Prueba de Fuego" desde cero.
- [x] Se ha verificado que marcas críticas como Siemens, ABB y Dynatrace no se diluyen (FidelitySentinel).
- [x] La atribución por sociedad (Reintel, Redinter, Red Eléctrica) es quirúrgica y veraz.

## 3. Si modificas MAPEOS O PAYLOADS
- [x] El payload resultante sigue el esquema ClientDossierV3.
- [x] Los tests de soberanía web (`zero-lockin-guard`) pasan en verde tras el saneamiento de seguridad.

## 4. Observabilidad y FinOps
- [x] El motor registra el consumo de tokens y el coste estimado en cada llamada a Vertex AI.
- [x] Los logs estructurados capturan la telemetría de los agentes.

## 5. Documentación
- [x] Se ha actualizado `docs/architecture/assessment_factory_flow.md` con los nuevos patrones de herencia y fidelidad atómica.
- [x] El validador de gobernanza de documentación ha certificado la integridad de los enlaces.

## 6. Cierre de Fase 2
- [x] Dossier de Inteligencia de Cliente certificado al 10/10.
- [x] Repositorio estabilizado y sincronizado en la rama `main`.
