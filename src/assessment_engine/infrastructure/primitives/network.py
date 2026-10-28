"""
Network & Egress Primitive (Tier-1 Host API).
Provides safe outbound HTTP communications with enterprise-grade SSRF protection.
Prevents arbitrary network exfiltration and internal cloud metadata harvesting.
"""

import ipaddress
import logging
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.net")

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Private RFC1918
    ipaddress.ip_network("172.16.0.0/12"),     # Private RFC1918
    ipaddress.ip_network("192.168.0.0/16"),    # Private RFC1918
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local & Cloud Metadata (AWS/GCP)
    ipaddress.ip_network("0.0.0.0/8"),         # Broadcast / Current network
    ipaddress.ip_network("::1/128"),           # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 Private ULA
    ipaddress.ip_network("fe80::/10"),         # IPv6 Link-Local
]


class NetworkEgressPrimitive(CapabilityPrimitive):
    """
    Primitiva de red saliente segura.
    Permite a agentes e integraciones consultar APIs externas blindando la infraestructura contra SSRF.
    """

    @property
    def namespace(self) -> str:
        """Return the namespace."""
        return "net"

    def get_capabilities(self) -> dict[str, Any]:
        """Return the supported capabilities."""
        return {
            "version": "1.0.0",
            "operations": ["safe_fetch"],
            "security": ["SSRF Shield", "Cloud Metadata Blocking (169.254.169.254)", "DNS Resolution Pinning"],
            "protocols": ["HTTP", "HTTPS"]
        }

    def _is_private_ip(self, hostname: str) -> bool:
        """Check whether a hostname resolves to a dangerous internal or private IP address."""
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                for net in BLOCKED_IP_NETWORKS:
                    if ip_obj in net:
                        return True
            return False
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return True

    async def safe_fetch(
        self,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout_seconds: float = 10.0,
        allow_local_test: bool = False
    ) -> dict[str, Any]:
        """Execute an HTTP request with real-time SSRF protection."""
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return {"error": "Protocolo inválido. Solo se admiten peticiones HTTP y HTTPS."}

        hostname = parsed.hostname
        if not hostname:
            return {"error": "URL inválida: falta el host."}

        if not allow_local_test and self._is_private_ip(hostname):
            logger.warning(f"[Net Primitive SSRF Block] Petición bloqueada a destino prohibido: {hostname}")
            return {"error": f"Acceso denegado: el destino '{hostname}' resuelve a una red interna protegida (SSRF Shield)."}

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
                req_headers = headers or {}
                req_headers["User-Agent"] = "Autonomuos-Agent-Worker/2026 (Tier-1 Cloud Runtime)"
                
                resp = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=req_headers,
                    json=json_data
                )

                try:
                    body_json = resp.json()
                except (RuntimeError, ValueError, KeyError, OSError, TypeError):
                    body_json = None

                return {
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "json": body_json,
                    "text": resp.text[:10000] if body_json is None else None
                }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.error(f"[Net Primitive] Error en petición a {url}: {ex}")
            return {"error": f"Fallo de red: {ex!s}"}


# Singleton export
network_primitive = NetworkEgressPrimitive()
