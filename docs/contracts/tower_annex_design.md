# Tower Annex v2 - Diseño objetivo

## Objetivo
Rediseñar el anexo de torre para que sea:
- más visual
- más ejecutivo
- más corto
- más explicable
- menos repetitivo

## Principios de diseño
1. El lector debe entender en pocos minutos:
   - dónde está la torre
   - por qué está ahí
   - qué hay que hacer
2. El scoring debe ser visible y explicable por pilar.
3. Cada página debe aportar valor distinto.
4. El documento no debe repetir la misma idea en AS-IS, GAP y Conclusión.
5. El renderer debe generar gráficos y scorecards de forma determinista.

## Estructura objetivo del anexo
### 1. Resumen ejecutivo de la torre
Contenido:
- nombre de torre
- score global
- banda de madurez
- madurez objetivo
- headline ejecutivo
- 3 mensajes clave
- por qué importa

### 2. Perfil de madurez por pilar
Contenido:
- gráfico radial por pilares
- tabla compacta por pilar
- score por pilar
- banda por pilar
- interpretación breve por pilar
- mensajes:
  - pilar más fuerte
  - pilar más débil
  - cuello de botella estructural

### 3. AS-IS
Contenido:
- narrativa breve
- fortalezas clave
- brechas clave
- implicaciones operativas clave
- tabla reducida de riesgos sintetizados

### 4. Riesgos principales
Contenido:
- introducción breve
- tabla de riesgos priorizados
- cierre breve

### 5. Estado objetivo y brechas
Contenido:
- estado objetivo breve
- capacidades objetivo por pilar
- principios arquitectónicos clave
- tabla de gap por pilar:
  - AS-IS
  - estado objetivo
  - brecha clave
  - implicación operativa

### 6. Iniciativas prioritarias
Contenido:
- introducción breve
- iniciativas priorizadas
- objetivo
- prioridad
- resultado esperado
- dependencias

### 7. Conclusión
Contenido:
- valoración final
- mensaje ejecutivo
- áreas prioritarias
- cierre

### 8. Observaciones pendientes de validación
Contenido:
- preguntas abiertas consolidadas en un único punto

## Criterios editoriales
- Texto corto y de alta densidad informativa.
- Nada de párrafos largos si una tabla o scorecard lo explica mejor.
- Máximo enfoque en valor para lector ejecutivo-técnico.
- Reducir redundancia entre secciones.
- No repetir preguntas abiertas en varias secciones.

## Responsabilidades
### Determinista
- score global
- score por pilar
- banda por pilar
- orden de pilares
- radar chart
- scorecards
- consolidación de preguntas abiertas

### Agentes
- headline ejecutivo
- mensajes clave
- interpretación breve por pilar
- narrativa AS-IS
- riesgos
- TO-BE
- GAP
- TO-DO
- conclusión

## Decisión de diseño
Se mantiene el contrato base del artifact_type `tower_annex`, pero se evoluciona a `artifact_version = 2.0`.
