"""
Canonical Growth, SEO & Progressive Web App Engine — System 12 (W3C PWA / GEO SOTA 2026).
Consolidated organic discovery and mobile acceleration suite:
1. W3C Progressive Web App (PWA) generator with Service Worker and offline caching.
2. Generative Engine Optimization (GEO): llms.txt & robots.txt for ChatGPT and Claude.
3. Schema.org JSON-LD microdata injector for Google Maps and rich cards.
4. Dynamic sitemap.xml with prioritized frequency weighting.
5. Zero-FOUC inline theme bootstrapper (instant dark/light mode with zero flash).
6. W3C Speculation Rules engine for sub-50ms instant page loads.
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.pwa_generator import PWAGeneratorPrimitive, pwa_generator
from assessment_engine.infrastructure.primitives.geo_engine import GeoEnginePrimitive, geo_engine
from assessment_engine.infrastructure.primitives.schema_org_injector import SchemaOrgInjectorPrimitive, schema_org_injector
from assessment_engine.infrastructure.primitives.sitemap_generator import SitemapGeneratorPrimitive, sitemap_generator
from assessment_engine.infrastructure.primitives.zero_fouc_theme import ZeroFOUCThemePrimitive, zero_fouc_theme
from assessment_engine.infrastructure.primitives.speculative_preloader import SpeculativePreloaderPrimitive, speculative_preloader

growth_engine = pwa_generator
geo_engine_suite = geo_engine
