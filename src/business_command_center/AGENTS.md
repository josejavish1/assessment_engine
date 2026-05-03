---
status: "Verified"
owner: "frontend-governance"
last_verified_against: "2026-05-03"
doc_type: "operational-directive"
---

# Directiva de Agente: Principios para la Modificación del Frontend

Este documento establece las reglas canónicas que deben seguir los agentes de IA al modificar la base de código del `business_command_center`. El objetivo es garantizar la predictibilidad, mantenibilidad y robustez de la aplicación, con un foco especial en la gestión del estado.

## Principios Fundamentales (Do's and Don'ts)

### State Management

El estado de la aplicación se gestiona de forma centralizada. Cualquier modificación debe respetar este principio para evitar la desincronización y los efectos secundarios no deseados.

*   **DO:** Utilizar exclusivamente el `StateContext` para leer o modificar el estado global de la aplicación.
    *   **Ejemplo de lectura:** `const { state } = useStateContext();`
    *   **Ejemplo de escritura:** `dispatch({ type: 'UPDATE_USER', payload: newUser });`

*   **DON'T:** No introducir estado local (`useState`) para datos que tengan un alcance global o que necesiten ser consistentes a través de diferentes componentes.

*   **DON'T:** Nunca modificar directamente el objeto de estado. Todas las actualizaciones deben realizarse a través de la función `dispatch` para asegurar que las mutaciones sean predecibles y rastreables.
    *   **Incorrecto:** `state.user = newUser;`
    *   **Correcto:** `dispatch({ type: 'UPDATE_USER', payload: newUser });`

### Component Architecture

*   **DO:** Crear componentes puros y sin estado siempre que sea posible. Estos componentes deben recibir datos y callbacks exclusivamente a través de `props`.

*   **DON'T:** No introducir lógica de negocio ni llamadas a APIs directamente en los componentes de la interfaz de usuario. Esta lógica debe estar centralizada en los servicios o hooks designados.

### Testing

*   **DO:** Añadir o actualizar los tests de interfaz de usuario (`test_ui.js`) para verificar cualquier cambio visual o de comportamiento.
*   **DON'T:** No considerar una tarea como completada hasta que los tests existentes y los nuevos pasen satisfactoriamente.
