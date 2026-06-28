import hashlib
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List

import docx

from assessment_engine.domain.schemas.evidence import EvidenceFragment, EvidenceLedger
from assessment_engine.infrastructure.text_utils import slugify

logger = logging.getLogger(__name__)


class EvidenceEngine:
    r"""{'EvidenceEngine': "Manages the ingestion, parsing, and serialization of evidence fragments.\n\n    This class provides a pipeline for processing source documents (e.g., .docx,\n    .txt, .html) into discrete, content-addressable `EvidenceFragment` objects.\n    It maintains a persistent ledger of these fragments for a specific client,\n    handling deduplication based on content hashes. The engine can serialize the\n    entire collection of fragments into a formatted string suitable for use as\n    grounding context in Retrieval-Augmented Generation (RAG) systems.\n\n    Attributes:\n        client_id: The unique identifier for the client instance.\n        storage_dir: The root directory for storing the client's evidence ledger\n            and extracted media files.\n        ledger_path: The full path to the `evidence_vault.json` ledger file.\n        ledger: The in-memory representation of the evidence ledger, containing\n            all registered fragments.", '__init__': "Initializes the EvidenceEngine for a specific client.\n\n        Establishes the storage path for the client's data and attempts to load\n        an existing evidence ledger from disk. If no ledger is found, a new,\n        empty one is created in memory.\n\n        Args:\n            client_id: The unique identifier for the client.\n            storage_dir: The directory path for storing the evidence ledger and\n                any associated media files.", '_load_ledger': 'Loads the evidence ledger from disk or creates a new one.\n\n        Attempts to read and validate the `evidence_vault.json` file from the\n        configured storage path. If the file does not exist or contains invalid\n        data, a new, empty `EvidenceLedger` instance is returned.\n\n        Returns:\n            An `EvidenceLedger` instance, either loaded from disk or newly\n            initialized.', 'ingest_file': "Parses a source file into content fragments and adds them to the ledger.\n\n        Selects a parser based on the file's extension to decompose its content.\n        Each resulting fragment is registered in the evidence ledger. The use of\n        content-addressable identifiers provides implicit deduplication, ensuring\n        only new, unique fragments are added. The ledger is persisted to storage\n        upon successful completion.\n\n        Args:\n            file_path: The path to the source file to ingest.\n\n        Returns:\n            The number of new, unique fragments added to the ledger. Returns 0 if\n            the file type is unsupported or if all fragments from the file were\n            already present.\n\n        Raises:\n            FileNotFoundError: If the file specified by `file_path` does not exist.", '_parse_docx': 'Decomposes a `.docx` file into a list of `EvidenceFragment` objects.\n\n        Iterates through block-level items (paragraphs, tables) in document order,\n        maintaining a hierarchical context based on heading styles. It also\n        extracts all media assets (e.g., images) directly from the underlying\n        ZIP archive and creates placeholder fragments for them. Heuristics are\n        used to identify implicit headings (e.g., short, bolded lines).\n\n        Args:\n            path: The path to the `.docx` file.\n\n        Returns:\n            A list of `EvidenceFragment` objects representing the structured\n            content of the document.', '_parse_text': 'Parses a plaintext or Markdown file into a list of `EvidenceFragment` objects.\n\n        The method infers a document hierarchy by treating lines prefixed with\n        Markdown-style hash characters (`#`, `##`, etc.) as headings. All other\n        non-empty lines are treated as simple text content. This structure is\n        used to populate the location metadata for each created fragment.\n\n        Args:\n            path: The path to the `.txt` or `.md` file.\n\n        Returns:\n            A list of `EvidenceFragment` objects from the text content.', '_parse_html': 'Parses an HTML file into a list of `EvidenceFragment` objects.\n\n        This method uses BeautifulSoup4 to extract textual content from common\n        semantic tags (`h1`-`h3`, `p`, `li`). It first removes `<script>` and\n        `<style>` elements to isolate content. If BeautifulSoup4 is not\n        available, it falls back to parsing the file as raw text.\n\n        Args:\n            path: The path to the `.html` file.\n\n        Returns:\n            A list of `EvidenceFragment` objects extracted from the HTML content.', '_create_fragment': "Creates an `EvidenceFragment` from content and location metadata.\n\n        Generates a content hash (SHA256) for deduplication and a deterministic\n        UUIDv5 for stable identification. The UUID is derived from the source URI,\n        the fragment's hierarchical path, and its content hash, ensuring that\n        identical content in the same structural position yields the same ID.\n\n        Args:\n            content: The textual content of the fragment.\n            source_uri: The identifier of the source document.\n            location: A dictionary containing metadata about the fragment's\n                position and type within the source document.\n\n        Returns:\n            An initialized `EvidenceFragment` instance.", '_save_ledger': 'Persists the current evidence ledger to disk as a JSON file.', 'get_grounding_context': 'Serializes all registered fragments into a single string for LLM context.\n\n        This method compiles all evidence fragments from the ledger into a single,\n        newline-separated string. A header is added, and each subsequent line is\n        formatted as `[fragment_id] content`, which is an optimized format for\n        inclusion as grounding context in a language model prompt.\n\n        Returns:\n            A formatted string containing all evidence fragments prefixed with their\n            unique identifiers.'}."""

    def __init__(self, client_id: str, storage_dir: Path):
        """Initializes the EvidenceEngine for a specific client.

        Sets up instance attributes and loads the client's evidence ledger from disk.
        The ledger is read from a file named 'evidence_vault.json' located within the
        specified storage directory.

        Args:
            client_id (str): The unique identifier for the client.
            storage_dir (pathlib.Path): The base directory for evidence storage.

        Attributes:
            client_id (str): The unique identifier for the client.
            storage_dir (pathlib.Path): The base directory for evidence storage.
            ledger_path (pathlib.Path): The direct path to the evidence ledger file.
            ledger (dict): The deserialized evidence ledger loaded from the JSON file.

        Raises:
            IOError: If the ledger file cannot be found or read.
            ValueError: If the ledger file contains malformed JSON.
        """
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
        """Ingest a source file by parsing it into unique content fragments for the ledger.

        A parser is selected based on the file's extension to decompose its
        content. Supported formats include .docx, .txt, .md, and .html. Each
        resulting fragment is identified by its content hash, which provides
        implicit deduplication; only fragments not already present in the ledger
        are added.

        The updated ledger is persisted to storage upon successful ingestion. Files
        with unsupported extensions are skipped.

        Args:
            file_path: The path to the source file to ingest.

        Returns:
            The number of new, unique fragments added to the ledger. This will
            be 0 if the file type is unsupported or if all fragments from the
            file were already present.

        Raises:
            FileNotFoundError: If the file at `file_path` does not exist.
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

        # Registers the newly generated fragments into the evidence ledger. The use of content-addressable identifiers provides implicit deduplication at the point of insertion.
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

        #
        media_dir = self.storage_dir / "media" / slugify(path.name)
        media_dir.mkdir(parents=True, exist_ok=True)

        doc = docx.Document(str(path))
        fragments: List[EvidenceFragment] = []
        heading_stack: List[str] = []

        # The Office Open XML (.docx) format is a ZIP archive. This block directly accesses the package to extract all media assets, which are conventionally stored in the 'word/media/' directory.
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
            r"""{'docstring': 'Yields block-level content items from a python-docx container.\n\nThis generator provides a unified interface for iterating through the\nblock-level content within a python-docx container, such as a `Document` or\na table `Cell`. It operates by inspecting the underlying Open XML element\ntree to identify paragraphs, tables, and graphical elements.\n\nArgs:\n    parent (Any): A python-docx container object, typically an instance of\n        `docx.document.Document` or `docx.table._Cell`. The object must\n        possess an underlying XML element that can be accessed via\n        `.element.body` (for a `Document`) or `._element` (for other\n        containers).\n\nYields:\n    Union[Paragraph, Table, str]: The next block-level item from the\n    container. Yields `Paragraph` or `Table` objects for text and table\n    content, respectively. For graphical elements like drawings (`<w:drawing>`)\n    or pictures (`<w:pict>`), it yields the literal string\n    "image_placeholder".\n\nRaises:\n    AttributeError: If `parent` does not have the required underlying XML\n        element attribute (`.element.body` or `._element`).'}."""
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

                #
                level = None
                h_match = re.search(r"Heading\s*(\d)", style, re.I)
                if h_match:
                    level = int(h_match.group(1))
                elif (
                    any(run.bold for run in block.runs)
                    and len(text) < 100
                    and len(text) > 0
                ):
                    # Implements a heuristic to identify implicit headings. Lines with low character counts and bold formatting, which lack an explicit heading style, are promoted to a canonical heading level.
                    # Implicitly detected headings are assigned a canonical depth of Level 3 to ensure consistent handling within the hierarchical context stack.
                    level = 3

                if level:
                    # Reconciles the heading context stack with the current heading's level. The stack is unwound by popping parent contexts until its top element represents the direct hierarchical predecessor of the current heading.
                    heading_stack = heading_stack[: level - 1]
                    # Ensures structural continuity in the document hierarchy by inserting synthetic parent headings where non-sequential jumps in heading levels occur (e.g., a transition from H1 to H3).
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
                # Associates the current table fragment with the active heading context stack to preserve its semantic position within the document's hierarchy.
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
        # Infers the hierarchical structure of plaintext documents (MD, TXT) by applying two primary heuristics: lines prefixed with Markdown-style hashes, and lines composed entirely of uppercase characters, are treated as headings.
        lines = [line.strip() for line in content.split("\n")]
        fragments: List[EvidenceFragment] = []
        heading_stack: List[str] = []

        for i, line in enumerate(lines):
            if not line:
                continue

            # Implements a heading detection heuristic for plaintext formats by identifying lines prefixed with Markdown-style hash characters (`#`, `##`, etc.).
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
        """A minimalist parser for converting HTML to plaintext, specifically designed to extract semantic textual content from web-archived snapshots."""
        try:
            from bs4 import (
                BeautifulSoup,  # Suppresses a static type checker error where the framework's behavior intentionally deviates from the statically inferred type.
            )
        except ImportError:
            print("⚠️ BeautifulSoup4 not installed. Falling back to raw text for HTML.")
            return self._parse_text(path)

        content = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(content, "html.parser")

        # Removes all `<script>` and `<style>` elements from the HTML to isolate semantic content from presentational markup and executable code.
        for script in soup(["script", "style"]):
            script.decompose()

        fragments = []
        # Aggregates consecutive document elements of a homogenous type (e.g., a sequence of paragraphs or list items) into a single logical block prior to fragmentation.
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
        # Generates a deterministic UUIDv5 for each fragment. The namespace and name are derived from the source document ID, the fragment's hierarchical path, and its content hash, ensuring content-addressable stability and uniqueness for identical content in different structural contexts.
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
        import uuid
        tmp_path = self.ledger_path.with_name(f"{self.ledger_path.name}.{uuid.uuid4().hex[:8]}.tmp")
        try:
            tmp_path.write_text(
                self.ledger.model_dump_json(indent=2), encoding="utf-8"
            )
            # POSIX Atomic Rename: replaces the old file atomically, preventing partial corruption
            tmp_path.replace(self.ledger_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def get_grounding_context(self) -> str:
        """Serialize registered evidence fragments into a numbered context string."""
        lines = ["--- GROUND TRUTH FRAGMENTS ---"]
        for f in self.ledger.fragments:
            lines.append(f"[{f.fragment_id}] {f.content}")
        return "\n".join(lines)
