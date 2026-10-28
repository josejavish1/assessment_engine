"""
SISP Action Bridge Primitive — SOTA Full-Stack Event Wiring (RFC-016 Engine / RFC-020 Stage D).
Binds interactive UI elements in generated React views (buttons, forms, selectors)
to real backend primitives (FastAPI endpoints, SQLite WAL, WebAuthn, Stripe Connect)
and universal modal/deep-route dispatchers in the golden polyglot workspace.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.sisp_action_bridge")


class SispActionType(str, Enum):
    """Define canonical contract action types in the SISP ecosystem."""
    BOOKING = "BOOKING"          # Enlaza a BookingSlots (RFC 5545) y calendario
    CHECKOUT = "CHECKOUT"        # Enlaza a Stripe Connect con pasarela de pago
    AUTH = "AUTH"                # Enlaza a UniversalAuthModal (WebAuthn Passkeys / ReBAC)
    NAVIGATE = "NAVIGATE"        # Enrutamiento profundo multi-página (#view=... / AppRouterDispatcher)
    DYNAMIC_API = "DYNAMIC_API"  # Despacha peticiones REST a /api/v1/data/ con SQLite WAL


@dataclass(frozen=True)
class ActionBindingRule:
    """Define heuristic rules for binding button text patterns to concrete actions."""
    action_type: SispActionType
    keywords: tuple[str, ...]
    target_handler: str
    fallback_hash: str


# Reglas de enlace contractual predeterminadas (Agnósticas y multilingües)
DEFAULT_BINDING_RULES: tuple[ActionBindingRule, ...] = (
    ActionBindingRule(
        action_type=SispActionType.BOOKING,
        keywords=("reservar", "reserva", "solicitar diagnóst", "pedir cita", "agendar", "book", "schedule", "peritaje", "inspeccionar", "visita privada", "sala de puja", "cita", "termin", "buchen", "reservieren", "réserver", "reserver", "rendez-vous", "rdv", "prenotare"),
        target_handler="onOpenBooking",
        fallback_hash="#view=booking",
    ),
    ActionBindingRule(
        action_type=SispActionType.CHECKOUT,
        keywords=("contratar", "adquirir", "comprar", "financiar", "checkout", "subscrib", "pujar", "lote", "consignar", "custodia", "oferta", "adjudicar", "pagar", "buy", "subscribe", "kaufen", "abonnieren", "payer", "commander", "souscrire", "acheter", "acquista"),
        target_handler="onOpenCheckout",
        fallback_hash="#view=checkout",
    ),
    ActionBindingRule(
        action_type=SispActionType.AUTH,
        keywords=("iniciar sesión", "acceder", "login", "mi cuenta", "portal privado", "entrar", "sign in", "anmelden", "espace client", "connexion", "se connecter", "einloggen", "accedi"),
        target_handler="onOpenAuth",
        fallback_hash="#view=login",
    ),
    ActionBindingRule(
        action_type=SispActionType.NAVIGATE,
        keywords=("directorio", "catalogo", "catálogo", "explorar", "descubrir", "ver más", "ver mas", "ver todos", "ver todas", "explore", "directory", "catalog", "browse", "view all", "katalog", "entdecken", "annuaire", "parcourir", "esplora"),
        target_handler="onNavigate",
        fallback_hash="#view=directorio",
    ),
)


def _inject_generative_props_declaration(code: str) -> str:
    """Inject GenerativeLandingProps interface after imports if missing."""
    if "interface GenerativeLandingProps" in code or "GenerativeViewProps" in code:
        return code

    props_decl = (
        "\nexport interface GenerativeLandingProps {\n"
        "  contract?: any;\n"
        "  onAction?: (action: string, payload?: any) => void;\n"
        "  onNavigate?: (route: string) => void;\n"
        "  onOpenBooking?: (payload?: any) => void;\n"
        "  onOpenCheckout?: (payload?: any) => void;\n"
        "  onOpenAuth?: (role?: string) => void;\n"
        "  onLogin?: () => void;\n"
        "  onRegister?: () => void;\n"
        "  onEnterApp?: (targetViewId?: string) => void;\n"
        "  [key: string]: any;\n"
        "}\n\n"
    )
    import_matches = list(re.finditer(r"^import\s+.*?;\s*$", code, re.MULTILINE))
    if import_matches:
        pos = import_matches[-1].end()
        return code[:pos] + "\n" + props_decl + code[pos:]
    return props_decl + code


def _normalize_component_signature(code: str) -> str:
    """Normalize function or arrow component signatures to accept GenerativeLandingProps."""
    sig_patterns = (
        (
            re.compile(r"export\s+(?:default\s+)?function\s+GenerativeLandingView\s*\([^)]*\)", re.MULTILINE),
            "export function GenerativeLandingView({ onOpenBooking, onOpenCheckout, onOpenAuth, onAction, onNavigate, onEnterApp, onLogin, onRegister, contract, ...props }: GenerativeLandingProps = {})",
        ),
        (
            re.compile(r"export\s+(?:default\s+)?function\s+LandingView\s*\([^)]*\)", re.MULTILINE),
            "export function LandingView({ onOpenBooking, onOpenCheckout, onOpenAuth, onAction, onNavigate, onEnterApp, onLogin, onRegister, contract, ...props }: GenerativeLandingProps = {})",
        ),
        (
            re.compile(r"export\s+(?:default\s+)?const\s+GenerativeLandingView(?:\s*:\s*React\.FC(?:<[^>]*>)?)?\s*=\s*\([^)]*\)\s*=>", re.MULTILINE),
            "export const GenerativeLandingView: React.FC<any> = ({ onOpenBooking, onOpenCheckout, onOpenAuth, onAction, onNavigate, onEnterApp, onLogin, onRegister, contract, ...props }: any) =>",
        ),
    )
    res = code
    for pat, repl in sig_patterns:
        if pat.search(res):
            res = pat.sub(repl, res)
    return res


def _ensure_landing_view_exports(code: str) -> str:
    """Ensure consistent named and default exports for App.tsx router compatibility."""
    has_landing_view_decl = bool(re.search(r"(?:function|const)\s+LandingView\b", code))
    has_generative_decl = bool(re.search(r"(?:function|const)\s+GenerativeLandingView\b", code))
    res = code

    if has_generative_decl and not has_landing_view_decl:
        if "export const LandingView" not in res and "export { GenerativeLandingView as LandingView }" not in res:
            res += "\n\nexport const LandingView = GenerativeLandingView;\n"
        if "export default" not in res:
            res += "export default GenerativeLandingView;\n"
    elif has_landing_view_decl:
        if "export default" not in res:
            res += "\nexport default LandingView;\n"
        if "export { LandingView }" not in res and not re.search(r"export\s+(?:const|function)\s+LandingView\b", res):
            res += "\nexport { LandingView };\n"
    return res


class SispActionBridge:
    """Bind generated DOM events to backend infrastructure to ensure all call-to-action elements are interactive."""

    DEFAULT_BINDING_RULES = DEFAULT_BINDING_RULES

    def generate_dispatcher_typescript(self) -> str:
        """Generate the universal TypeScript event hook and dispatcher supporting deep linking and custom events."""
        return """// SISP Universal Action Dispatcher (Generated by SispActionBridge)
export interface SispActionPayload {
  action: 'BOOKING' | 'CHECKOUT' | 'AUTH' | 'NAVIGATE' | 'DYNAMIC_API';
  serviceId?: string;
  planId?: string;
  targetView?: string;
  metadata?: Record<string, unknown>;
}

export interface GenerativeViewProps {
  onAction?: (payload: SispActionPayload) => void;
  onNavigate?: (route: string) => void;
  onOpenBooking?: (payload?: { serviceId?: string; planId?: string }) => void;
  onOpenCheckout?: (payload?: { planId?: string; amountCHF?: number }) => void;
  onOpenAuth?: (role?: string) => void;
}

export function dispatchSispAction(payload: SispActionPayload): void {
  if (typeof window === 'undefined') return;

  switch (payload.action) {
    case 'BOOKING':
      window.location.hash = payload.serviceId ? `#view=booking&service=${payload.serviceId}` : '#view=booking';
      break;
    case 'CHECKOUT':
      window.location.hash = payload.planId ? `#view=checkout&plan=${payload.planId}` : '#view=checkout';
      break;
    case 'AUTH':
      window.location.hash = '#view=login';
      break;
    case 'NAVIGATE': {
      const target = payload.targetView ? payload.targetView.replace(/^\\//, '') : 'directorio';
      window.location.hash = `#view=${target}`;
      window.dispatchEvent(new CustomEvent('sisp:navigate', { detail: { target, original: payload.targetView } }));
      break;
    }
    case 'DYNAMIC_API':
      window.dispatchEvent(new CustomEvent('sisp:dynamic_api', { detail: payload }));
      break;
  }
}
"""

    def build_dynamic_binding_rules(
        self, routes: list[dict[str, Any]] | None = None
    ) -> tuple[ActionBindingRule, ...]:
        """Build dynamic binding rules augmenting DEFAULT_BINDING_RULES with routes from routes_manifest."""
        if not routes:
            return DEFAULT_BINDING_RULES

        dynamic_rules: list[ActionBindingRule] = []
        for r in routes:
            path = str(r.get("path", "")).strip()
            if not path or path == "/":
                continue
            clean_slug = path.strip("/").replace("-", " ")
            title = str(r.get("title", "")).strip().lower()
            keywords = tuple(dict.fromkeys(
                [w for w in (clean_slug.split() + title.split()) if len(w) >= 3]
            ))
            if keywords:
                target_hash = f"#view={path.strip('/')}"
                dynamic_rules.append(
                    ActionBindingRule(
                        action_type=SispActionType.NAVIGATE,
                        keywords=keywords,
                        target_handler="onNavigate",
                        fallback_hash=target_hash,
                    )
                )

        return tuple(dynamic_rules) + DEFAULT_BINDING_RULES

    def audit_component_contracts(self, tsx_code: str) -> dict[str, Any]:
        """Audit a generated TSX file to verify that it declares the contract props interface and check for non-interactive buttons."""
        has_props_interface = "GenerativeViewProps" in tsx_code or "GenerativeLandingProps" in tsx_code
        has_active_onclicks = "onClick" in tsx_code

        # Find inert buttons lacking onClick or type=submit.
        button_tags = re.findall(r"<button\b[^>]*>", tsx_code, re.IGNORECASE)
        unwired_buttons = [b for b in button_tags if "onClick" not in b and 'type="submit"' not in b]

        return {
            "has_props_interface": has_props_interface,
            "has_active_onclicks": has_active_onclicks,
            "total_buttons": len(button_tags),
            "unwired_buttons": len(unwired_buttons),
            "is_fully_wired": has_props_interface and len(unwired_buttons) == 0,
        }

    def inject_action_props_interface(self, tsx_code: str) -> str:
        """Inject the contract props interface and ensure the component signature and export match App.tsx requirements (export { LandingView })."""
        updated = _inject_generative_props_declaration(tsx_code)
        updated = _normalize_component_signature(updated)
        return _ensure_landing_view_exports(updated)

    def wire_button_actions(
        self,
        tsx_code: str,
        rules: tuple[ActionBindingRule, ...] = DEFAULT_BINDING_RULES
    ) -> tuple[str, int]:
        """Inspect buttons in the TSX component and wire non-interactive buttons to contract handlers."""
        wired_code = tsx_code
        rewrites_count = 0

        button_block_pattern = re.compile(
            r"(<button\b(?![^>]*\bonClick\b)[^>]*>)([\s\S]*?)(</button>)",
            re.IGNORECASE
        )

        def replacer(match: re.Match[str]) -> str:
            """Return the replacement string for the given regular expression match."""
            nonlocal rewrites_count
            opening_tag = match.group(1)
            inner_content = match.group(2)
            closing_tag = match.group(3)
            lower_inner = inner_content.lower()

            matched_rule = None
            for rule in rules:
                if any(kw in lower_inner for kw in rule.keywords):
                    matched_rule = rule
                    break

            if matched_rule:
                rewrites_count += 1
                action_name = matched_rule.action_type.value
                fallback = matched_rule.fallback_hash
                target_arg = f', targetView: "{fallback.replace("#view=", "").strip("/")}"' if action_name == "NAVIGATE" else ""
                onclick_attr = (
                    f' onClick={{() => {{'
                    f' try {{ if ((window as any).dispatchSispAction) {{ (window as any).dispatchSispAction({{ action: "{action_name}"{target_arg} }}); return; }} }} catch (_) {{}}'
                    f' window.location.hash = "{fallback}";'
                    f' }}}}'
                )

                new_opening = opening_tag[:-1] + onclick_attr + ">"
                return f"{new_opening}{inner_content}{closing_tag}"

            return match.group(0)

        wired_code = button_block_pattern.sub(replacer, wired_code)
        return wired_code, rewrites_count

    def apply_bridge_to_workspace(
        self, workspace_dir: Path, target_tsx_path: Path, routes: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Apply the complete SISP bridge to a workspace with dynamic route augmentation."""
        web_dir = workspace_dir / "web" if (workspace_dir / "web").exists() else workspace_dir
        lib_dir = web_dir / "src" / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)

        dispatcher_path = lib_dir / "sispActionDispatcher.ts"
        dispatcher_path.write_text(self.generate_dispatcher_typescript(), encoding="utf-8")

        if not target_tsx_path.exists():
            return {
                "status": "PARTIAL",
                "dispatcher_generated": True,
                "error": f"Archivo TSX no encontrado en: {target_tsx_path}"
            }

        original_code = target_tsx_path.read_text(encoding="utf-8")
        code_with_props = self.inject_action_props_interface(original_code)
        effective_rules = self.build_dynamic_binding_rules(routes)
        final_code, rewrites = self.wire_button_actions(code_with_props, rules=effective_rules)
        target_tsx_path.write_text(final_code, encoding="utf-8")

        audit = self.audit_component_contracts(final_code)
        logger.info(f"✔ Puente SISP aplicado a {target_tsx_path.name} ({rewrites} botones cableados)")

        return {
            "status": "SUCCESS",
            "dispatcher_path": str(dispatcher_path),
            "rewrites_applied": rewrites,
            "contract_audit": audit,
        }


sisp_action_bridge = SispActionBridge()
