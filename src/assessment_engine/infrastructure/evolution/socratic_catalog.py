"""
Provide a catalog of domain invariants and Pareto solutions.
Decoupled from socratic_deliberator.py to maintain modularity and reduce cognitive overhead.
"""
from __future__ import annotations

from typing import Any


def get_domain_fallback_data(slug: str) -> dict[str, Any]:
    """Generate domain-specific invariants, pitfalls, and Pareto solutions for deterministic fallbacks."""
    s = slug.lower()
    if any(k in s for k in ("analytic", "kpi", "telemetr", "metric", "dashboard", "tooltip", "svg", "bézier", "bezier")):
        return {
            "benchmarks": ["Plausible Analytics", "Stripe Dashboard", "Vercel Analytics"],
            "invariants": [
                "Privacidad sin cookies (exención legal de banner de consentimiento RGPD)",
                "Visualización de tendencias temporales (24h, 7d, 30d)",
                "Bento grid de métricas con deltas porcentuales respecto al periodo anterior",
                "Embudo secuencial de conversión por fases de retención",
            ],
            "traps": [
                "Desbordamiento de tooltips fuera del viewport en los bordes de la pantalla",
                "Deformación de fuentes y grosores de línea al escalar un SVG en pantallas móviles",
                "Solapamiento ilegible de etiquetas de fechas en el eje X en resoluciones estrechas",
                "Fractura de curvas Bézier cuando hay días consecutivos con métricas en cero o null",
            ],
            "pareto": [
                "Regla del Cuadrante CSS: invertir clases Tailwind del tooltip (-translate-x-full) si x > 50% del ancho",
                "Ejes temporales desacoplados en Flexbox HTML para evitar distorsión de fuentes en pantallas móviles",
                "Interpolación paramétrica Catmull-Rom de 20 líneas en TypeScript puro sin dependencias externas",
                "Barras de embudo y distribución resueltas con elementos div nativos y transiciones CSS",
            ],
        }

    if any(k in s for k in ("pricing", "charge", "billing", "subscrip", "quote", "tier")):
        return {
            "benchmarks": ["Stripe Billing (Dynamic Quotes)", "Paddle Pricing Matrix", "Vercel Add-on Tiering"],
            "invariants": [
                "Matriz comparativa responsiva de planes con cálculo dinámico de descuentos anuales",
                "Selector reactivo de add-ons con desglose de impuestos e IVA a coste $0.00",
                "Cálculo en intervalos semiabiertos UTC [start, end) para evitar colisiones de periodos de prueba",
            ],
            "traps": [
                "Colapso de altura en CSS Grid cuando las tarjetas de tiers tienen diferente número de características",
                "Desbordamiento de tooltips de desglose de precios al recortarse por 'overflow: hidden' del contenedor",
                "Pérdida de foco accesible en sliders de rango y botones de checkout",
            ],
            "pareto": [
                "CSS Subgrid (grid-rows-subgrid) para alinear invariablemente los botones de checkout al fondo",
                "CSS Popover API nativo (popover='auto') para tooltips inmunes a stacking contexts",
                "Pseudo-elementos táctiles virtuales (before:min-w-[44px]) para touch targets accesibles",
            ],
        }

    if any(k in s for k in ("map", "geo", "locat", "radius")):
        return {
            "benchmarks": ["Mapbox GL Native", "OpenStreetMap Leaflet", "Google Maps Platform"],
            "invariants": [
                "Renderizado vectorial de mapas y pines geolocalizados a coste $0.00 sin cuotas de API",
                "Cálculo determinista de radio de cobertura y proximidad mediante fórmula Haversine en backend",
                "Navegación fluida de pan, zoom y selección de coordenadas geográficas",
            ],
            "traps": [
                "Bloqueo del scroll de la página móvil al arrastrar el mapa con gestos táctiles",
                "Degradación de rendimiento por saturación del DOM al pintar más de 500 pines simultáneos",
                "Fallo de cálculo de distancias por inversión de latitud/longitud (GeoJSON vs EPSG:4326)",
            ],
            "pareto": [
                "Clustering determinista de pines en cuadrícula antes del renderizado DOM",
                "Captura de eventos 'touch-action: pan-x pan-y' para evitar atrapar el scroll vertical de la ventana",
                "Cálculo matemático puro Haversine en 15 líneas de Python/TS sin librerías SIG pesadas",
            ],
        }

    if any(k in s for k in ("seat", "inventor", "matrix", "allocation")):
        return {
            "benchmarks": ["Ticketmaster Visual Seating", "Eventbrite Floorplan", "Fever Experience"],
            "invariants": [
                "Matriz bidimensional interactiva de butacas/asientos con estados libre, ocupado y seleccionado",
                "Bloqueo temporal con lease-hold TTL en memoria para evitar colisiones de compra simultánea",
                "Navegación accesible por teclado mediante matriz de coordenadas ARIA",
            ],
            "traps": [
                "Condición de carrera cuando dos usuarios seleccionan la misma butaca en el mismo milisegundo",
                "Deformación del aspect-ratio de las butacas en pantallas con zoom de usuario o móviles",
                "Fuga de memoria por temporizadores TTL no cancelados al desmontar el componente",
            ],
            "pareto": [
                "Lease-hold optimista con versión de token atómico en SQLite WAL",
                "CSS Aspect-Ratio 1/1 y SVG viewBox escalable a 60 FPS",
                "Hook useEffect con cancelación estricta de temporizador en el return",
            ],
        }

    if any(k in s for k in ("copilot", "chat", "assist", "ai", "drawer")):
        return {
            "benchmarks": ["Linear Ask Assistant", "Cursor AI Drawer", "Intercom Fin"],
            "invariants": [
                "Drawer lateral accesible colapsable con atajo de teclado global (Cmd+K / Ctrl+K)",
                "Streaming reactivo de respuestas asistidas con indicador visual de pensamiento",
                "Historial conversacional local persistido sin fugas de contexto",
            ],
            "traps": [
                "Atrapamiento de foco (Focus Trap) roto que impide cerrar el drawer con la tecla Escape",
                "Salto vertical molesto del scroll al recibir fragmentos de streaming a alta velocidad",
                "Inyección de HTML/Markdown peligroso no saneado en las respuestas del asistente",
            ],
            "pareto": [
                "HTML Dialog nativo o Popover API con manejo automático de Escape y foco",
                "Auto-scroll suave anclado al contenedor solo si el usuario no ha subido el scroll manualmente",
                "Renderizado seguro de texto sanitizado escapando tags HTML nativamente",
            ],
        }

    if any(k in s for k in ("doc", "forge", "pdf", "invoice", "print")):
        return {
            "benchmarks": ["Stripe Invoicing W3C", "DocuSign Print Standard", "PandaDoc Engine"],
            "invariants": [
                "Plantilla conforme a estándares W3C @media print para exportación vectorial nítida a PDF",
                "Desglose legal de impuestos, base imponible y emisor/receptor conforme a RGPD y Facturae",
                "Sellado de código QR legal verificable en impresión",
            ],
            "traps": [
                "Saltos de página indeseados que parten tablas o firmas por la mitad en la exportación a PDF",
                "Desaparición de colores de fondo o bordes en navegadores que desactivan 'background-graphics'",
                "Desalineación milimétrica de columnas en páginas de tamaño A4 frente a US Letter",
            ],
            "pareto": [
                "Reglas CSS 'break-inside: avoid' y 'page-break-inside: avoid' en bloques de totales y firmas",
                "CSS 'print-color-adjust: exact' para forzar renderizado de fondos y contrastes en PDF",
                "Contenedor con medidas milimétricas exactas (210mm x 297mm) en modo vista previa",
            ],
        }

    return {
        "benchmarks": [f"Líder {slug.capitalize()} Tier-1", "Stripe Platform", "Vercel Infrastructure"],
        "invariants": [
            f"Implementación funcional completa del dominio '{slug}' con lógica de negocio real",
            f"Endpoints REST en /api/{slug}/ tipados con Pydantic y persistencia SQLite WAL",
            f"Componente React interactivo a 60 FPS sin dependencias externas pesadas",
        ],
        "traps": [
            f"Acoplamiento indebido de estado mutable entre la vista de {slug} y vistas ajenas",
            f"Falta de estados de carga (loading) o estados vacíos (empty state) cuando no hay datos",
            "Uso accidental de librerías externas no instaladas en package.json",
        ],
        "pareto": [
            "Uso exclusivo de React useState, useMemo y fetch nativo con Tailwind CSS",
            "Diseño defensivo con estado inicial vacío elegante y datos de prueba preconfigurados",
            "Modularidad desacoplada comunicándose exclusivamente vía REST",
        ],
    }
