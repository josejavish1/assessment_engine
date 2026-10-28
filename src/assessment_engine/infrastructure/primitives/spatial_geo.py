"""
Spatial & Geolocation Primitive — GEMA 01 / Radar Primitive 1 (GeoPy & W3C RFC 7946 / SOTA 2026).
Engine for trigonometric Haversine spherical distance calculations, compass bearings,
and SQLite-optimized Bounding Boxes for sub-millisecond proximity queries.
Emits W3C compliant GeoJSON (RFC 7946) FeatureCollections for direct map rendering.
Domain-agnostic: powers distance calculations for veterinary clinics, delivery radius, or padel clubs.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.spatial_geo")

EARTH_RADIUS_KM = 6371.0088  # Radio medio terrestre WGS 84


@dataclass(frozen=True)
class GeoCoordinate:
    latitude: float
    longitude: float


@dataclass
class BoundingBox:
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float


@dataclass
class ProximityDistanceResult:
    distance_km: float
    distance_meters: float
    bearing_degrees: float
    compass_direction: str  # Compass cardinal heading (N, NE, E, SE, S, SW, W, NW)


class SpatialGeoPrimitive:
    """
    Provide canonical geospatial and spherical distance calculations.
    """

    COMPASS_POINTS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]

    def calculate_haversine_distance(
        self,
        point_a: GeoCoordinate,
        point_b: GeoCoordinate
    ) -> ProximityDistanceResult:
        """Calculate the spherical distance and bearing between two geographic coordinates."""
        lat1, lon1 = math.radians(point_a.latitude), math.radians(point_a.longitude)
        lat2, lon2 = math.radians(point_b.latitude), math.radians(point_b.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Apply the canonical Haversine formula.
        a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        dist_km = EARTH_RADIUS_KM * c

        # Rumbo inicial (Initial Bearing)
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing_rad = math.atan2(y, x)
        bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0

        compass_idx = int(round(bearing_deg / 45.0)) % 8
        compass_dir = self.COMPASS_POINTS[compass_idx]

        return ProximityDistanceResult(
            distance_km=round(dist_km, 3),
            distance_meters=round(dist_km * 1000.0, 1),
            bearing_degrees=round(bearing_deg, 1),
            compass_direction=compass_dir
        )

    def calculate_bounding_box(self, center: GeoCoordinate, radius_km: float) -> BoundingBox:
        """Calculate a bounding box for optimized SQLite queries using B-tree indexes. SELECT * FROM locations WHERE lat BETWEEN min_lat AND max_lat AND lon BETWEEN min_lon AND max_lon;"""
        rad_dist = radius_km / EARTH_RADIUS_KM

        lat_rad = math.radians(center.latitude)
        lon_rad = math.radians(center.longitude)

        min_lat_rad = lat_rad - rad_dist
        max_lat_rad = lat_rad + rad_dist

        # Adjust longitude based on latitude (meridians converge at the poles).
        delta_lon = math.asin(math.sin(rad_dist) / math.cos(lat_rad))
        min_lon_rad = lon_rad - delta_lon
        max_lon_rad = lon_rad + delta_lon

        return BoundingBox(
            min_latitude=round(math.degrees(min_lat_rad), 6),
            max_latitude=round(math.degrees(max_lat_rad), 6),
            min_longitude=round(math.degrees(min_lon_rad), 6),
            max_longitude=round(math.degrees(max_lon_rad), 6)
        )

    def to_geojson_feature(
        self,
        coordinate: GeoCoordinate,
        properties: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Export a coordinate conforming to GeoJSON (RFC 7946)."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(coordinate.longitude, 6), round(coordinate.latitude, 6)]
            },
            "properties": properties or {}
        }


spatial_geo = SpatialGeoPrimitive()
