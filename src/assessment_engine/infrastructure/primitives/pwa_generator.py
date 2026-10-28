"""
Universal W3C Progressive Web App (PWA) Generator — GEMA 15 (SOTA 2026).
Enables zero-touch native installation on iOS, iPadOS, Android, and macOS/Windows.
Generates W3C-compliant manifest.webmanifest and resilient offline Service Worker (sw.js)
parameterized directly by the domain contract and design archetype.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.pwa_generator")


class PWAGeneratorPrimitive:
    """
    Generador PWA agnóstico al dominio.
    Convierte cualquier aplicación web generada en una app móvil instalable.
    """

    def generate_manifest(self, contract: dict[str, Any]) -> dict[str, Any]:
        """Generate the formal W3C manifest content."""
        app_name = contract.get("app_name", "Plataforma Profesional")
        short_name = contract.get("short_name", app_name[:12].strip())
        theme = contract.get("theme", {})
        primary_color = theme.get("primary_color", "#0D9488")
        bg_color = theme.get("bg_color", "#FFFFFF")

        return {
            "name": app_name,
            "short_name": short_name,
            "description": contract.get("tagline", "Plataforma profesional instalable"),
            "start_url": "./",
            "scope": "./",
            "display": "standalone",
            "orientation": "any",
            "background_color": bg_color,
            "theme_color": primary_color,
            "categories": [contract.get("sector", "business").lower()],
            "icons": [
                {
                    "src": "pwa-192.svg",
                    "sizes": "192x192",
                    "type": "image/svg+xml",
                    "purpose": "any maskable"
                },
                {
                    "src": "pwa-512.svg",
                    "sizes": "512x512",
                    "type": "image/svg+xml",
                    "purpose": "any maskable"
                }
            ]
        }

    def generate_service_worker(self) -> str:
        """Generate the service worker (sw.js) with a cache-first strategy for static assets and network-first for APIs."""
        return """// Tier-1 Resilient W3C Service Worker
const CACHE_NAME = 'app-cache-v1';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.webmanifest'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Network-First para llamadas de API y eventos SSE
  if (url.pathname.includes('/api/') || url.pathname.includes('/realtime/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({ error: 'offline_mode_active' }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Cache-First con Stale-While-Revalidate para assets
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        fetch(event.request).then((networkResponse) => {
          if (networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
          }
        }).catch(() => {});
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});
"""

    def generate_default_svg_icon(self, primary_color: str = "#0D9488") -> str:
        """Generate a crisp vector SVG icon for the PWA."""
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <rect width="512" height="512" rx="128" fill="{primary_color}"/>
  <path d="M256 120 L380 340 L132 340 Z" fill="#FFFFFF" opacity="0.95"/>
  <circle cx="256" cy="300" r="40" fill="{primary_color}"/>
</svg>
"""

    def apply_to_workspace(self, ws_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
        """Inject all PWA artifacts into the workspace web/ directory."""
        web_dir = ws_dir / "web"
        if not web_dir.exists():
            return {"applied": False, "reason": "web_dir_missing"}

        dist_public = web_dir / "public"
        dist_public.mkdir(exist_ok=True)

        manifest_data = self.generate_manifest(contract)
        (dist_public / "manifest.webmanifest").write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # 2. sw.js
        sw_code = self.generate_service_worker()
        (dist_public / "sw.js").write_text(sw_code, encoding="utf-8")

        primary = manifest_data.get("theme_color", "#0D9488")
        svg_content = self.generate_default_svg_icon(primary)
        (dist_public / "pwa-192.svg").write_text(svg_content, encoding="utf-8")
        (dist_public / "pwa-512.svg").write_text(svg_content, encoding="utf-8")

        index_html = web_dir / "index.html"
        if index_html.exists():
            html_txt = index_html.read_text(encoding="utf-8")
            if "manifest.webmanifest" not in html_txt:
                head_insert = (
                    '    <link rel="manifest" href="/manifest.webmanifest">\n'
                    f'    <meta name="theme-color" content="{primary}">\n'
                    '    <meta name="apple-mobile-web-app-capable" content="yes">\n'
                    '    <meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
                    '  </head>'
                )
                html_txt = html_txt.replace("</head>", head_insert)
                index_html.write_text(html_txt, encoding="utf-8")

        logger.info(f"[{ws_dir.name}] PWA W3C instalable aplicada: {manifest_data['name']}")
        return {"applied": True, "app_name": manifest_data["name"]}


pwa_generator = PWAGeneratorPrimitive()
