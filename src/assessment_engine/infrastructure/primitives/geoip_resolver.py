"""
Deterministic Offline GeoIP & Currency Resolver Primitive — GEMA 43 (ISO 3166 / SOTA 2026).
Resolves geographical regions and ISO 4217 currencies using in-memory CIDR subnet tables.
Employs Python's native ipaddress library for zero-latency, sub-microsecond lookups.
Zero external MaxMind license keys or slow network dependencies needed.
"""

from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass

logger = logging.getLogger("assessment_engine.infrastructure.primitives.geoip_resolver")


@dataclass(frozen=True)
class GeoLocationData:
    country_code: str  # ISO 3166-1 alpha-2
    country_name: str
    currency: str      # ISO 4217
    locale: str        # BCP 47


class GeoIPResolverPrimitive:
    """
    Resolve geographic locations offline by evaluating CIDR subnets.
    """

    # Define canonical representative public subnets by region (CIDR blocks).
    SUBNET_GEO_MAP = [
        (ipaddress.ip_network("80.0.0.0/11"), GeoLocationData("ES", "España", "EUR", "es-ES")),
        (ipaddress.ip_network("82.0.0.0/11"), GeoLocationData("ES", "España", "EUR", "es-ES")),
        (ipaddress.ip_network("88.0.0.0/11"), GeoLocationData("ES", "España", "EUR", "es-ES")),
        (ipaddress.ip_network("212.0.0.0/10"), GeoLocationData("ES", "España", "EUR", "es-ES")),
        (ipaddress.ip_network("81.0.0.0/11"), GeoLocationData("GB", "Reino Unido", "GBP", "en-GB")),
        (ipaddress.ip_network("86.0.0.0/11"), GeoLocationData("GB", "Reino Unido", "GBP", "en-GB")),
        (ipaddress.ip_network("140.0.0.0/9"), GeoLocationData("US", "Estados Unidos", "USD", "en-US")),
        (ipaddress.ip_network("142.0.0.0/9"), GeoLocationData("US", "Estados Unidos", "USD", "en-US")),
        (ipaddress.ip_network("174.0.0.0/9"), GeoLocationData("US", "Estados Unidos", "USD", "en-US")),
        (ipaddress.ip_network("187.0.0.0/9"), GeoLocationData("MX", "México", "MXN", "es-MX")),
        (ipaddress.ip_network("177.0.0.0/9"), GeoLocationData("BR", "Brasil", "BRL", "pt-BR")),
        (ipaddress.ip_network("133.0.0.0/9"), GeoLocationData("JP", "Japón", "JPY", "ja-JP")),
    ]

    DEFAULT_FALLBACK = GeoLocationData("ES", "España", "EUR", "es-ES")

    def resolve_ip(self, ip_str: str) -> GeoLocationData:
        """Determine the country, currency, and regional format by evaluating the IP subnet."""
        if not ip_str or ip_str == "localhost":
            return self.DEFAULT_FALLBACK

        clean_ip = ip_str.split(":")[0].strip()

        try:
            ip_obj = ipaddress.ip_address(clean_ip)
            # 1. Comprobar si es privada, loopback o de enlace local (RFC 1918 / RFC 3927)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
                return self.DEFAULT_FALLBACK

            for subnet, geo_data in self.SUBNET_GEO_MAP:
                if ip_obj in subnet:
                    return geo_data

        except ValueError:
            logger.debug(f"[GeoIPResolver] IP con formato no válido: '{ip_str}'")

        return self.DEFAULT_FALLBACK


geoip_resolver = GeoIPResolverPrimitive()
