# core/evolution/layout_contract_sealer.py
import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

# Canonical universal modal / system route targets valid in any industry and language
UNIVERSAL_VALID_TARGETS = {
    "/",
    "#view=home",
    "#view=landing",
    "#view=contact",
    "#view=contacto",
    "#view=login",
    "#view=auth",
    "#view=register",
    "#view=checkout",
    "#view=portal",
}

@dataclass
class LayoutAuditResult:
    is_sealed: bool
    total_nav_links: int
    total_footer_links: int
    orphan_links: List[str]
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_sealed": self.is_sealed,
            "total_nav_links": self.total_nav_links,
            "total_footer_links": self.total_footer_links,
            "orphan_links": self.orphan_links,
            "details": self.details
        }


class LayoutContractSealer:
    def _get_valid_links(self, routes: List[Dict[str, Any]]) -> List[str]:
        """Compute set of valid link destinations from manifest routes and universal targets."""
        valid_links = set(UNIVERSAL_VALID_TARGETS)
        for route in routes:
            path = route.get("path", "")
            if path:
                if path == "/":
                    valid_links.add("/")
                    valid_links.add("#view=home")
                else:
                    slug = path.strip("/")
                    valid_links.add(f"#view={slug}")
                    valid_links.add(path)
                    valid_links.add(f"#{slug}")
        return sorted(list(valid_links))

    def _get_replacement_links(self, routes: List[Dict[str, Any]]) -> List[str]:
        """Extract public route targets suitable for navigational replacements."""
        replacements: List[str] = []
        for route in routes:
            path = route.get("path", "")
            is_public = route.get("is_public", True)
            if path and path != "/" and is_public:
                replacements.append(f"#view={path.strip('/')}")
        if not replacements:
            replacements = ["#view=home", "#view=contact"]
        return replacements

    def _seal_block(self, tsx_code: str, block_tag: str, valid_links: List[str], replacements: List[str]) -> Tuple[str, int]:
        """Seal href links inside a given block (nav or footer) replacing invalid or dead links."""
        if not replacements:
            return tsx_code, 0
            
        pattern = re.compile(rf'(<{block_tag}[^>]*>)(.*?)(</{block_tag}>)', re.IGNORECASE | re.DOTALL)
        href_pattern = re.compile(r'href=["\']([^"\']*)["\']')
        valid_set = set(valid_links)
        
        rewrites = 0
        def block_repl(match: re.Match) -> str:
            nonlocal rewrites
            open_tag = match.group(1)
            content = match.group(2)
            close_tag = match.group(3)
            
            def href_repl(h_match: re.Match) -> str:
                nonlocal rewrites
                href_val = h_match.group(1).strip()
                if not href_val or href_val in ("#", "javascript:void(0)") or (href_val.startswith("#view=") and href_val not in valid_set):
                    rewrites += 1
                    new_val = replacements[(rewrites - 1) % len(replacements)]
                    return f'href="{new_val}"'
                return h_match.group(0)
                
            new_content = href_pattern.sub(href_repl, content)
            return open_tag + new_content + close_tag
            
        sealed_tsx = pattern.sub(block_repl, tsx_code)
        return sealed_tsx, rewrites

    def seal_navbar_links(self, tsx_code: str, routes: List[Dict[str, Any]]) -> Tuple[str, int]:
        valid_links = self._get_valid_links(routes)
        replacements = self._get_replacement_links(routes)
        return self._seal_block(tsx_code, "nav", valid_links, replacements)

    def seal_footer_columns(self, tsx_code: str, routes: List[Dict[str, Any]]) -> Tuple[str, int]:
        valid_links = self._get_valid_links(routes)
        replacements = self._get_replacement_links(routes)
        return self._seal_block(tsx_code, "footer", valid_links, replacements)

    def seal_transactional_modals(self, tsx_code: str) -> Tuple[str, int]:
        """Ensures the 3 universal transactional modals are imported and mounted in any LandingView."""
        rewrites = 0
        sealed = tsx_code

        required_imports = [
            ("UniversalEntityDetailModal", "import { UniversalEntityDetailModal } from '../primitives/UniversalEntityDetailModal';\n"),
            ("JurisdictionLegalModal", "import { JurisdictionLegalModal } from '../primitives/JurisdictionLegalModal';\n"),
            ("ListingPublisherWizard", "import { ListingPublisherWizard } from '../primitives/ListingPublisherWizard';\n"),
        ]
        for symbol, import_stmt in required_imports:
            if symbol not in sealed:
                sealed = import_stmt + sealed
                rewrites += 1

        if "<UniversalEntityDetailModal" not in sealed and "</main>" in sealed:
            modals_jsx = (
                "      <UniversalEntityDetailModal isOpen={!!selectedEntity} entity={selectedEntity} onClose={() => setSelectedEntity(null)} />\n"
                "      <JurisdictionLegalModal isOpen={!!legalModalTab} contract={contract} onClose={() => setLegalModalTab(null)} />\n"
                "      <ListingPublisherWizard isOpen={isPublisherOpen} onClose={() => setIsPublisherOpen(false)} />\n"
                "    </main>"
            )
            sealed = sealed.replace("</main>", modals_jsx, 1)
            rewrites += 1

        return sealed, rewrites

    def audit_layout_integrity(self, tsx_code: str, routes: List[Dict[str, Any]]) -> LayoutAuditResult:
        """Audit all anchor links detecting dead, fragment-only, or unmapped route targets."""
        valid_links = set(self._get_valid_links(routes))
        
        href_pattern = re.compile(r'href=["\']([^"\']*)["\']')
        found_links = href_pattern.findall(tsx_code)
        
        orphan_links: List[str] = []
        for lk in found_links:
            s = lk.strip()
            if not s or s in ("#", "javascript:void(0)"):
                orphan_links.append(f"DEAD_HREF:{lk}")
            elif s.startswith("#view=") and s not in valid_links:
                orphan_links.append(s)
                
        nav_pattern = re.compile(r'<nav[^>]*>.*?</nav>', re.IGNORECASE | re.DOTALL)
        footer_pattern = re.compile(r'<footer[^>]*>.*?</footer>', re.IGNORECASE | re.DOTALL)
        
        total_nav = sum(len(re.findall(r'href=', nav)) for nav in nav_pattern.findall(tsx_code))
        total_footer = sum(len(re.findall(r'href=', footer)) for footer in footer_pattern.findall(tsx_code))
            
        return LayoutAuditResult(
            is_sealed=len(orphan_links) == 0,
            total_nav_links=total_nav,
            total_footer_links=total_footer,
            orphan_links=orphan_links,
            details=f"Audited {len(found_links)} links, {len(orphan_links)} orphans found"
        )

    def apply_sealer_to_workspace(self, workspace_dir: Path, target_tsx: Path, routes_manifest: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ws_path = workspace_dir.resolve()
            tgt_path = target_tsx.resolve()
            if os.path.commonpath([str(ws_path), str(tgt_path)]) != str(ws_path):
                return {"status": "ERROR", "rewrites_applied": 0, "details": "Path traversal"}
        except ValueError:
            return {"status": "ERROR", "rewrites_applied": 0, "details": "Path traversal"}
            
        if not target_tsx.exists():
            return {"status": "ERROR", "rewrites_applied": 0, "details": "File not found"}
            
        content = target_tsx.read_text(encoding="utf-8")
        routes = routes_manifest.get("routes", [])
        
        content, nav_rewrites = self.seal_navbar_links(content, routes)
        content, footer_rewrites = self.seal_footer_columns(content, routes)
        
        target_tsx.write_text(content, encoding="utf-8")
        
        return {
            "status": "SUCCESS",
            "rewrites_applied": nav_rewrites + footer_rewrites,
            "details": f"Sealed {nav_rewrites} navbar links and {footer_rewrites} footer links"
        }
