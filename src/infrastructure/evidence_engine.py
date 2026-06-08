import hashlib
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List

import docx

from domain.schemas.evidence import EvidenceFragment, EvidenceLedger
from infrastructure.text_utils import slugify

logger = logging.getLogger(__name__)


class EvidenceEngine:
    """
    Tier-1 Deterministic Fragmentation Engine.
    Decomposes documents into atomic, addressable evidence pieces.
    """

    def __init__(self, client_id: str, storage_dir: Path):
        self.client_id = client_id
        self.storage_dir = storage_dir
        self.ledger_path = storage_dir / "evidence_vault.json"
        self.ledger = self._load_ledger()

    def _load_ledger(self) -> EvidenceLedger:
        if self.ledger_path.exists():
            try:
                return EvidenceLedger.model_validate_json(
                    self.ledger_path.read_text(encoding="utf-8")
                )
            except Exception:
                pass
        return EvidenceLedger(client_id=self.client_id)

    def ingest_file(self, file_path: Path) -> int:
        """
        Parses a file and adds its fragments to the ledger.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        fragments = []
        if file_path.suffix.lower() == ".docx":
            fragments = self._parse_docx(file_path)
        elif file_path.suffix.lower() in [".txt", ".md"]:
            fragments = self._parse_text(file_path)
        elif file_path.suffix.lower() == ".html":
            fragments = self._parse_html(file_path)
        else:
            print(f"⚠️ Unsupported file type: {file_path.suffix}")
            return 0

        # Update ledger (deduplicate by hash)
        existing_hashes = {f.content_hash for f in self.ledger.fragments}
        new_count = 0
        for frag in fragments:
            if frag.content_hash not in existing_hashes:
                self.ledger.fragments.append(frag)
                existing_hashes.add(frag.content_hash)
                new_count += 1

        self._save_ledger()
        return new_count

    def _parse_docx(self, path: Path) -> List[EvidenceFragment]:
        import re
        import zipfile

        from docx.table import Table
        from docx.text.paragraph import Paragraph

        # Create media directory for images
        media_dir = self.storage_dir / "media" / slugify(path.name)
        media_dir.mkdir(parents=True, exist_ok=True)

        doc = docx.Document(str(path))
        fragments: List[EvidenceFragment] = []
        heading_stack: List[str] = []

        # Extract images from the docx (zip)
        try:
            with zipfile.ZipFile(path) as z:
                for name in z.namelist():
                    if name.startswith("word/media/"):
                        image_data = z.read(name)
                        image_filename = name.split("/")[-1]
                        (media_dir / image_filename).write_bytes(image_data)
        except Exception as e:
            logger.warning(f"Could not extract images from {path.name}: {e}")

        def iter_block_items(parent: Any) -> Any:
            """Iterates through paragraphs and tables in order."""
            from docx.document import Document

            parent_elm = (
                parent.element.body if isinstance(parent, Document) else parent._element
            )
            for child in parent_elm.iterchildren():
                if child.tag.endswith("p"):
                    yield Paragraph(child, parent)
                elif child.tag.endswith("tbl"):
                    yield Table(child, parent)
                elif child.tag.endswith("drawing") or child.tag.endswith("pict"):
                    yield "image_placeholder"

        img_counter = 0
        for block in iter_block_items(doc):
            if block == "image_placeholder":
                img_counter += 1
                fragments.append(
                    self._create_fragment(
                        content=f"[EVIDENCIA MULTIMODAL]: Imagen o diagrama técnico detectado en la posición {img_counter}.",
                        source_uri=str(path),
                        location={
                            "type": "image",
                            "hierarchy": list(heading_stack),
                            "needs_vision_parsing": True,
                            "image_index": img_counter,
                        },
                    )
                )
                continue

            if isinstance(block, Paragraph):
                text = block.text.strip()
                style = block.style.name if block.style else "Normal"

                # Detect Heading Levels
                level = None
                h_match = re.search(r"Heading\s*(\d)", style, re.I)
                if h_match:
                    level = int(h_match.group(1))
                elif (
                    any(run.bold for run in block.runs)
                    and len(text) < 100
                    and len(text) > 0
                ):
                    # Heuristic for bold short lines as headers (common in some DOCX)
                    # We'll treat them as Heading 3 for the stack
                    level = 3

                if level:
                    # Shrink stack to match current level
                    heading_stack = heading_stack[: level - 1]
                    # Fill gaps if level 3 comes after level 1
                    while len(heading_stack) < level - 1:
                        heading_stack.append("...")
                    heading_stack.append(text)

                    fragments.append(
                        self._create_fragment(
                            content=text,
                            source_uri=str(path),
                            location={
                                "type": "heading",
                                "level": level,
                                "hierarchy": list(heading_stack),
                            },
                        )
                    )
                elif len(text) >= 20:
                    fragments.append(
                        self._create_fragment(
                            content=text,
                            source_uri=str(path),
                            location={
                                "type": "paragraph",
                                "style": style,
                                "hierarchy": list(heading_stack),
                                "is_bold": any(run.bold for run in block.runs),
                            },
                        )
                    )

            elif isinstance(block, Table):
                # Process Table with current heading context
                for r_idx, row in enumerate(block.rows):
                    cells = [cell.text.strip() for cell in row.cells]
                    row_text = " | ".join([c for c in cells if c])
                    if len(row_text) >= 20:
                        fragments.append(
                            self._create_fragment(
                                content=row_text,
                                source_uri=str(path),
                                location={
                                    "type": "table_row",
                                    "row_index": r_idx,
                                    "hierarchy": list(heading_stack),
                                    "is_header": r_idx == 0,
                                },
                            )
                        )

        return fragments

    def _parse_text(self, path: Path) -> List[EvidenceFragment]:
        content = path.read_text(encoding="utf-8")
        # Simple hierarchical detection for MD/TXT if it uses # or uppercase lines
        lines = [line.strip() for line in content.split("\n")]
        fragments: List[EvidenceFragment] = []
        heading_stack: List[str] = []

        for i, line in enumerate(lines):
            if not line:
                continue

            # Simple Markdown-like heading detection
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                text = line.lstrip("#").strip()
                heading_stack = heading_stack[: level - 1]
                heading_stack.append(text)
                fragments.append(
                    self._create_fragment(
                        content=text,
                        source_uri=str(path),
                        location={
                            "type": "heading",
                            "level": level,
                            "hierarchy": list(heading_stack),
                        },
                    )
                )
            elif len(line) >= 20:
                fragments.append(
                    self._create_fragment(
                        content=line,
                        source_uri=str(path),
                        location={
                            "type": "line",
                            "index": i,
                            "hierarchy": list(heading_stack),
                        },
                    )
                )

        return fragments

    def _parse_html(self, path: Path) -> List[EvidenceFragment]:
        """Simple HTML to text parser for external snapshots."""
        try:
            from bs4 import BeautifulSoup  # type: ignore
        except ImportError:
            print("⚠️ BeautifulSoup4 not installed. Falling back to raw text for HTML.")
            return self._parse_text(path)

        content = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(content, "html.parser")

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        fragments = []
        # Group by common blocks
        for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
            text = tag.get_text().strip()
            if len(text) > 30:
                fragments.append(
                    self._create_fragment(
                        content=text,
                        source_uri=str(path.name),
                        location={
                            "type": "html_block",
                            "tag": tag.name,
                            "hierarchy": [
                                soup.title.string if soup.title else "Web Snapshot"
                            ],
                        },
                    )
                )
        return fragments

    def _create_fragment(
        self, content: str, source_uri: str, location: Dict[str, Any]
    ) -> EvidenceFragment:
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        # Stable UUID based on content, source AND hierarchy to distinguish identical strings in different sections
        hierarchy_str = " > ".join(location.get("hierarchy", []))
        namespace = uuid.NAMESPACE_URL
        fragment_id = str(
            uuid.uuid5(namespace, f"{source_uri}:{hierarchy_str}:{content_hash}")
        )

        return EvidenceFragment(
            fragment_id=fragment_id,
            source_uri=source_uri,
            content=content,
            content_hash=content_hash,
            location_metadata=location,
        )

    def _save_ledger(self) -> None:
        self.ledger_path.write_text(
            self.ledger.model_dump_json(indent=2), encoding="utf-8"
        )

    def get_grounding_context(self) -> str:
        """Returns a numbered list of all fragments for AI context."""
        lines = ["--- GROUND TRUTH FRAGMENTS ---"]
        for f in self.ledger.fragments:
            lines.append(f"[{f.fragment_id}] {f.content}")
        return "\n".join(lines)
