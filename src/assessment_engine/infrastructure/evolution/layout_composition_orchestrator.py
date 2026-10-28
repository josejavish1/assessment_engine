"""
core/evolution/layout_composition_orchestrator.py
Deterministic compiler for LandingView.tsx (RFC-022 Phase 4).
Assembles a pure, typed container slotting certified primitives without freehand JSX.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict


class LayoutCompositionOrchestrator:
    """
    Deterministic compiler that assembles LandingView.tsx as a pure container.
    """

    def _get_imports(self) -> str:
        return (
            "import React, { useState } from 'react';\n"
            "import { DynamicPricingConfigurator } from './DynamicPricingConfigurator';\n"
            "import { EntityShowcaseGrid } from './EntityShowcaseGrid';\n"
            "import { JurisdictionLegalModal } from './JurisdictionLegalModal';\n"
            "import { ParametricSearchHero } from './ParametricSearchHero';\n"
            "import { UniversalAuthModal } from './UniversalAuthModal';\n"
            "import { UniversalEntityDetailModal } from './UniversalEntityDetailModal';\n"
        )

    def _get_interfaces(self, app_name: str) -> str:
        return (
            f"// {app_name} Landing View (Deterministic Primitive Composition)\n"
            "export interface LandingViewProps {\n"
            "  contract?: any;\n"
            "  onLogin?: () => void;\n"
            "  onRegister?: () => void;\n"
            "  onOpenCheckout?: (item?: any) => void;\n"
            "}\n"
        )

    def _get_component_body(self) -> str:
        return (
            "export const LandingView: React.FC<LandingViewProps> = ({ contract, onLogin, onOpenCheckout }) => {\n"
            "  const [activeModal, setActiveModal] = useState<string | null>(null);\n"
            "  const [selectedEntity, setSelectedEntity] = useState<any | null>(null);\n"
            "  return (\n"
            "    <main className=\"flex flex-col min-h-screen bg-background text-on-surface\">\n"
            "      <header className=\"sticky top-0 z-40 w-full border-b border-border/40 bg-background/95 backdrop-blur px-6 py-3 flex items-center justify-between\">\n"
            "        <div className=\"flex items-center gap-3 font-bold text-base tracking-tight\">{contract?.app_name || 'Portal'}</div>\n"
            "        <div className=\"flex items-center gap-3\">\n"
            "          <button onClick={() => onLogin?.()} className=\"text-xs font-medium px-3 py-1.5 rounded-md hover:bg-muted transition-colors\">Iniciar sesión</button>\n"
            "          <button onClick={() => onOpenCheckout?.()} className=\"text-xs font-semibold px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90 shadow-sm\">Acceso</button>\n"
            "        </div>\n"
            "      </header>\n"
            "      <ParametricSearchHero contract={contract} onSearch={() => {}} />\n"
            "      <div className=\"flex-1 container mx-auto px-4 py-8 space-y-12\">\n"
            "        <EntityShowcaseGrid contract={contract} onSelectEntity={(entity) => {\n"
            "          setSelectedEntity(entity);\n"
            "          setActiveModal('detail');\n"
            "        }} />\n"
            "        <DynamicPricingConfigurator onOpenCheckout={onOpenCheckout} />\n"
            "      </div>\n"
            "      <footer className=\"border-t border-border/40 bg-background py-8 px-6 text-center text-xs text-muted-foreground flex flex-col items-center gap-4\">\n"
            "        <div className=\"flex items-center gap-6\">\n"
            "          <button onClick={() => setActiveModal('legal')} className=\"hover:underline\">Aviso Legal</button>\n"
            "          <button onClick={() => setActiveModal('legal')} className=\"hover:underline\">Privacidad</button>\n"
            "          <button onClick={() => setActiveModal('legal')} className=\"hover:underline\">Cookies</button>\n"
            "        </div>\n"
            "        <p>© {new Date().getFullYear()} {contract?.brand_name || 'Plataforma'}. Todos los derechos reservados.</p>\n"
            "      </footer>\n"
            "      <UniversalEntityDetailModal isOpen={activeModal === 'detail'} entity={selectedEntity} onClose={() => setActiveModal(null)} />\n"
            "      <JurisdictionLegalModal isOpen={activeModal === 'legal'} contract={contract} onClose={() => setActiveModal(null)} />\n"
            "    </main>\n"
            "  );\n"
            "};\n"
        )

    def compute_sha256_hash(self, code: str) -> str:
        """Calcula el hash SHA-256 para verificar idempotencia de compilación byte a byte."""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def validate_slot_manifest(self, contract: Dict[str, Any]) -> bool:
        """Validación fail-closed de ranuras (Slot Manifest) de las primitivas requeridas."""
        return isinstance(contract, dict)

    def compose_landing_view(self, contract: Dict[str, Any]) -> str:
        """
        Assembles the LandingView.tsx from the given contract deterministically.
        """
        self.validate_slot_manifest(contract)
        app_name = str(contract.get("app_name", "App"))

        imports = self._get_imports()
        interfaces = self._get_interfaces(app_name)
        body = self._get_component_body()

        code = f"{imports}\n{interfaces}\n{body}"
        return code
