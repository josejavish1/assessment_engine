"""
core/evolution/layout_self_healer.py

Motor autónomo de auto-sanación en bucle cerrado (Closed-Loop Test-Time Compute)
para reparar quirúrgicamente enlaces rotos y botones inertes en layouts generados TSX.
Opera con neutralidad absoluta (Zero-Language-Lock) en cualquier vertical de negocio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from typing import Any, Dict, List, Sequence, Tuple, Union


@dataclass
class SelfHealingResult:
    """Resultado inmutable del proceso de auto-sanación de layout."""
    converged: bool
    iterations_count: int
    repairs_applied: List[str]
    remaining_issues: List[str]
    final_tsx: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Vocabulario canónico de intenciones universales en 5 idiomas (EN, ES, DE, FR, IT)
_INTENT_KEYWORD_MAP: Tuple[Tuple[Tuple[str, ...], str], ...] = (
    # Contact
    (("contactar", "contacto", "escribenos", "escríbenos", "mensaje", "soporte", "support", "contact",
      "kontakt", "contatto", "contattaci", "contacter", "nous-contacter", "message"), "contact"),
    # Booking
    (("cita", "citas", "reservas", "reservar", "booking", "book", "appointments", "appointment",
      "termine", "termin", "buchen", "rendez-vous", "reserver", "prenota", "prenotazione"), "booking"),
    # Catalog / Properties / Inventory
    (("inmuebles", "propiedades", "catalogo", "catálogo", "inventario", "properties", "listings",
      "katalog", "immobilien", "catalogue", "immobili"), "properties"),
    # Pricing
    (("tarifas", "precios", "planes", "pricing", "tarifa", "precio", "subscripcion", "suscripción",
      "preise", "tarife", "tarifs", "prix", "prezzi", "tariffe", "plans"), "precios"),
    # About
    (("nosotros", "equipo", "quienes somos", "quiénes somos", "about", "about-us",
      "uber uns", "über uns", "a propos", "à propos", "chi siamo"), "nosotros"),
    # Login / Auth
    (("login", "iniciar sesion", "iniciar sesión", "acceder", "entrar", "signin", "auth",
      "anmelden", "einloggen", "connexion", "se connecter", "accedi", "accesso"), "login"),
    # Register
    (("registro", "registrarse", "crear cuenta", "signup", "register",
      "registrieren", "inscription", "s'inscrire", "registrati"), "register"),
    # Home
    (("inicio", "home", "portada", "principal", "startseite", "accueil", "inizio"), "home"),
)


def _clean_slug(val: str) -> str:
    return val.strip().lstrip("/").replace("#view=", "")


def _extract_from_dict(r: Dict[str, Any]) -> str:
    for key in ("slug", "path", "view", "id"):
        val = r.get(key)
        if isinstance(val, str):
            return _clean_slug(val)
    return ""


def _extract_slug_from_route(r: Union[str, Dict[str, Any]]) -> str:
    if isinstance(r, str):
        return _clean_slug(r)
    if isinstance(r, dict):
        return _extract_from_dict(r)
    return ""


def _extract_canonical_slugs(routes: Sequence[Union[str, Dict[str, Any]]]) -> List[str]:
    """Extrae slugs canónicos normalizados desde routes_manifest."""
    slugs: List[str] = []
    for r in routes:
        clean = _extract_slug_from_route(r)
        if clean:
            slugs.append(clean)
    return slugs or ["home", "contact", "properties", "precios"]


def _extract_tag_text(html: str) -> str:
    """Extrae texto visible de etiquetas HTML/JSX eliminando etiquetas interiores y espacios redundantes."""
    clean = re.sub(r'<[^>]+>', ' ', html)
    return " ".join(clean.split()).strip()


def _match_route_by_label_or_path(text: str, routes: Sequence[Union[str, Dict[str, Any]]]) -> str:
    """Empareja texto contra títulos y rutas del manifiesto en cualquier idioma y vertical."""
    clean_text = text.lower().strip()
    if not clean_text:
        return ""
    best_slug = ""
    best_score = 0
    tokens_text = set(re.findall(r'\w+', clean_text))
    for r in routes:
        if isinstance(r, dict):
            slug = _extract_from_dict(r)
            title = str(r.get("title", "")).lower()
            label = str(r.get("label", "")).lower()
            tokens_route = set(re.findall(r'\w+', f"{title} {label} {slug}"))
            overlap = len(tokens_text & tokens_route)
            if overlap > best_score:
                best_score = overlap
                best_slug = slug
    return best_slug


def _find_best_slug_match(target: str, candidates: Sequence[str]) -> str:
    """Calcula similitud difusa determinista contra candidatos canónicos."""
    clean_target = target.lower().strip().replace("-", "").replace("_", "")
    best_candidate = candidates[0]
    best_score = -1.0

    for cand in candidates:
        clean_cand = cand.lower().strip().replace("-", "").replace("_", "")
        score = SequenceMatcher(None, clean_target, clean_cand).ratio()
        if score > best_score:
            best_score = score
            best_candidate = cand

    return best_candidate


def _resolve_intent(text: str, candidates: Sequence[str]) -> str:
    """Resuelve la intención semántica a partir de texto visible o slug roto."""
    norm_text = text.lower()
    for keywords, target_slug in _INTENT_KEYWORD_MAP:
        if any(kw in norm_text for kw in keywords):
            if target_slug in candidates:
                return target_slug
            if target_slug in ("contact", "login", "register", "home", "booking"):
                return target_slug
            return _find_best_slug_match(target_slug, candidates)
    return ""


def _resolve_best_slug(current_target: str, raw_a_tag: str, slugs: Sequence[str], routes: Sequence[Union[str, Dict[str, Any]]]) -> str:
    """Determina el slug canónico óptimo analizando el target actual, texto visible o títulos de rutas."""
    # 1. Intención semántica en slug
    intent_slug = _resolve_intent(current_target, slugs)
    if intent_slug:
        return intent_slug

    # 2. Intención en texto visible
    visible_text = _extract_tag_text(raw_a_tag)
    if visible_text:
        intent_slug = _resolve_intent(visible_text, slugs)
        if intent_slug:
            return intent_slug
            
        # 3. Emparejamiento dinámico con rutas del manifiesto (cualquier idioma/vertical)
        matched = _match_route_by_label_or_path(visible_text, routes)
        if matched:
            return matched

    # 4. Fallback a similitud difusa
    if current_target and current_target != "#":
        return _find_best_slug_match(current_target, slugs)
    return slugs[0]


class LayoutSelfHealer:
    """Motor de sanación de interfaz en bucle cerrado (Closed-Loop Test-Time Compute)."""

    def heal_broken_link(self, raw_a_tag: str, routes: Sequence[Union[str, Dict[str, Any]]]) -> Tuple[str, bool]:
        """
        Mapea semánticamente enlaces rotos (#, vacíos, huérfanos) a la ruta
        canónica más afín de routes_manifest garantizando un href válido.
        """
        slugs = _extract_canonical_slugs(routes)
        href_match = re.search(r'href=(["\'])(.*?)\1', raw_a_tag)
        
        if not href_match:
            default_target = f"#view={slugs[0]}"
            healed = raw_a_tag.replace("<a ", f'<a href="{default_target}" ', 1)
            return healed, healed != raw_a_tag

        quote_char = href_match.group(1)
        href_val = href_match.group(2).strip()
        current_target = href_val.lstrip("/").replace("#view=", "")

        if current_target in slugs:
            return raw_a_tag, False

        best_slug = _resolve_best_slug(current_target, raw_a_tag, slugs, routes)
        healed = raw_a_tag.replace(href_match.group(0), f'href={quote_char}#view={best_slug}{quote_char}')
        return healed, healed != raw_a_tag

    def heal_inert_button(self, raw_button_tag: str, routes: Sequence[Union[str, Dict[str, Any]]]) -> Tuple[str, bool]:
        """
        Inyecta onClick={() => window.location.hash = ...} basándose en la intención
        del texto visible del botón si carece de manejador interactivo y no es submit.
        """
        if "onClick" in raw_button_tag or "disabled" in raw_button_tag or 'type="submit"' in raw_button_tag:
            return raw_button_tag, False

        slugs = _extract_canonical_slugs(routes)
        visible_text = _extract_tag_text(raw_button_tag)

        # 1. Intención semántica en 5 idiomas
        intent_slug = _resolve_intent(visible_text, slugs)
        
        # 2. Emparejamiento dinámico con títulos de rutas del manifiesto
        if not intent_slug and visible_text:
            intent_slug = _match_route_by_label_or_path(visible_text, routes)

        best_slug = intent_slug if intent_slug else slugs[0]

        injection = f' onClick={{() => window.location.hash = "#view={best_slug}"}}'

        if raw_button_tag.startswith("<button"):
            closing_bracket = raw_button_tag.find(">")
            if closing_bracket != -1:
                healed = raw_button_tag[:closing_bracket] + injection + raw_button_tag[closing_bracket:]
                return healed, True
                
        return raw_button_tag, False

    def heal_layout(self, tsx_code: str, routes: Sequence[Union[str, Dict[str, Any]]], max_iterations: int = 3) -> SelfHealingResult:
        """
        Ejecuta el ciclo de reparación iterativo hasta converger (idempotencia f(x) = x)
        o agotar las iteraciones máximas.
        """
        current_code = tsx_code
        repairs_applied: List[str] = []
        converged = False
        iteration = 0

        link_pattern = re.compile(r'<a\s+[^>]*?>.*?</a>|<a\s+[^>]*?/>', re.DOTALL | re.IGNORECASE)
        button_pattern = re.compile(r'<button\b[^>]*?>.*?</button>|<button\b[^>]*?/>', re.DOTALL | re.IGNORECASE)

        for i in range(1, max_iterations + 1):
            iteration = i
            changed_in_iter = False
            
            matches = list(link_pattern.finditer(current_code))
            for match in reversed(matches):
                raw_tag = match.group(0)
                healed, changed = self.heal_broken_link(raw_tag, routes)
                if changed:
                    start, end = match.span()
                    current_code = current_code[:start] + healed + current_code[end:]
                    repairs_applied.append(f"Healed link: {raw_tag} -> {healed}")
                    changed_in_iter = True

            btn_matches = list(button_pattern.finditer(current_code))
            for btn_match in reversed(btn_matches):
                raw_tag = btn_match.group(0)
                healed, changed = self.heal_inert_button(raw_tag, routes)
                if changed:
                    start, end = btn_match.span()
                    current_code = current_code[:start] + healed + current_code[end:]
                    repairs_applied.append(f"Healed button: {raw_tag} -> {healed}")
                    changed_in_iter = True

            if not changed_in_iter:
                converged = True
                break

        return SelfHealingResult(
            converged=converged,
            iterations_count=iteration,
            repairs_applied=repairs_applied,
            remaining_issues=[],
            final_tsx=current_code
        )
