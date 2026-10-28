"""
Canonical Spatial & Geolocation Engine — System 09 (W3C RFC 7946 / SOTA 2026).
Consolidated spatial analysis and proximity search suite:
1. Trigonometric spherical distance (Haversine km & meters).
2. Compass bearing calculations (N, NE, E, SE, S, SW, W, NW).
3. SQLite-optimized Bounding Boxes for sub-millisecond proximity queries.
4. W3C GeoJSON RFC 7946 Feature and FeatureCollection generator.
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.spatial_geo import (
    SpatialGeoPrimitive,
    GeoCoordinate,
    BoundingBox,
    ProximityDistanceResult,
    spatial_geo
)

spatial_engine = spatial_geo
