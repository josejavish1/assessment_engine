from abc import ABC, abstractmethod
from typing import Any


class CapabilityPrimitive(ABC):
    """
    Clase base para las 10 Primitivas Universales del sistema (Estado del Arte 2026).
    Cada primitiva expone métodos atómicos que pueden ser consumidos por el código
    aislado de la IA (Isolate/Sandbox) o directamente a través de la API REST dinámica.
    """
    
    @property
    @abstractmethod
    def namespace(self) -> str:
        """Specify the primitive namespace (e.g., 'db', 'auth', 'payments', 'network')."""

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """Return the schema of permitted operations and their input/output signatures."""
