---
status: Verified
owner: docs-governance
source_of_truth:
  - "package.json"
  - "src/app/components/"
last_verified_against: 2026-05-03
applies_to:
  - gemini
  - developers
doc_type: operational
---

# Business Command Center

Esta es la interfaz gráfica de usuario (GUI) para el Assessment Engine, construida como parte de la Fase 4 de la arquitectura (El *Business Command Center*).

Esta plataforma web está diseñada para ser utilizada por Consultores y Negocio, consumiendo datos en tiempo real del backend de Python a través del Model Context Protocol (MCP).

## Tecnologías

- Next.js (App Router)
- React
- Tailwind CSS
- shadcn/ui

## Arquitectura de Componentes

El siguiente diagrama ilustra la relación de alto nivel entre los componentes clave de la interfaz y su interacción con el backend.

```mermaid
graph TD
    subgraph "Business Command Center"
        A[ExecutiveExecutionDashboard] --> B(ArtifactCanvas);
        A --> C(AgentChat);
        A --> D(FloatingOmnibar);
    end

    subgraph "External Systems"
        E(MCP Server);
    end

    C -- "Sends user input" --> E;
    D -- "Executes commands" --> E;
    E -- "Streams artifact data" --> B;

    style A fill:#0284c7,stroke:#fff,stroke-width:2px,color:#fff
    style B fill:#34d399,stroke:#fff,stroke-width:2px,color:#fff
    style C fill:#f97316,stroke:#fff,stroke-width:2px,color:#fff
    style D fill:#f97316,stroke:#fff,stroke-width:2px,color:#fff
    style E fill:#4f46e5,stroke:#fff,stroke-width:2px,color:#fff
```

- **ExecutiveExecutionDashboard:** El componente principal que orquesta la visualización de los demás elementos.
- **ArtifactCanvas:** El área principal donde se renderizan y se interactúa con los artefactos generados por el motor de evaluación.
- **AgentChat:** La interfaz de chat para interactuar con los agentes de IA.
- **FloatingOmnibar:** Una barra de comandos para acceso rápido a acciones y herramientas.
- **MCP Server:** El backend de Python que proporciona los datos y la lógica de negocio.

## Desarrollo

Para arrancar el servidor de desarrollo local:

1.  **Navega al directorio:**
    ```bash
    cd src/business_command_center
    ```

2.  **Instala las dependencias:**
    ```bash
    npm install
    ```

3.  **Inicia el servidor de desarrollo:**
    ```bash
    npm run dev
    ```

Abre [http://localhost:3000](http://localhost:3000) en tu navegador para ver la interfaz.
