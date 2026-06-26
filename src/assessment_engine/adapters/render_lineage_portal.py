"""Renders and persists the static HTML for the Unified Lineage Matrix Explorer portal by hydrating a Jinja2 template with global and Digital Twin Object (DTO) state payloads."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import jinja2

logger = logging.getLogger(__name__)

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from assessment_engine.infrastructure.runtime_paths import (
    ROOT,
    resolve_client_dir,
    resolve_global_report_payload_path,
)

TEMPLATE_PATH = ROOT / "templates" / "lineage_portal_template.html"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _load_towers_detail(client_name: str) -> dict[str, Any]:
    client_dir = resolve_client_dir(client_name)
    towers_detail = {}

    # The system architecture defines a fixed, inclusive range of tower identifiers from T2 to T8 that require processing.
    for i in range(2, 9):
        tower_id = f"T{i}"
        blueprint_file = client_dir / tower_id / f"blueprint_t{i}_payload.json"
        if not blueprint_file.exists():
            # If an initial key lookup is unsuccessful, a fallback mechanism attempts a case-insensitive match using a normalized, lowercase variant of the key.
            blueprint_file = (
                client_dir / tower_id / f"blueprint_{tower_id.lower()}_payload.json"
            )

        if blueprint_file.exists():
            try:
                data = _load_json(blueprint_file)
                towers_detail[tower_id] = {
                    "document_meta": data.get("document_meta", {}),
                    "executive_snapshot": data.get("executive_snapshot", {}),
                    "pillars_analysis": data.get("pillars_analysis", []),
                }
                logger.info(f"Loaded blueprint details for tower {tower_id}")
            except Exception as e:
                logger.warning(f"Could not load blueprint for {tower_id}: {e}")

    return towers_detail


def render_lineage_portal(client_name: str) -> Path:
    """Generates a static HTML data lineage portal for a specified client.

    Aggregates data from a global report payload, a Digital Twin Object (DTO)
    state file (`digital_twin_state.json`), and supplementary tower metadata.
    The function gracefully handles missing payload and DTO state files by
    substituting empty dictionaries. These aggregated data sources are serialized
    to JSON strings and injected into a Jinja2 template. The final rendered HTML
    is written to a dedicated portal directory for the client (`<client_dir>/portal/`),
    creating the directory structure if it does not exist.

    Args:
        client_name (str): The unique identifier for the client, used to derive
            paths for input data files and the output portal directory.

    Returns:
        pathlib.Path: The absolute path to the generated `index.html` file.

    Raises:
        FileNotFoundError: If the main Jinja2 template file cannot be found at
            its configured path.
    """
    client_dir = resolve_client_dir(client_name)
    output_dir = client_dir / "portal"
    output_path = output_dir / "index.html"

    logger.info(
        f"🎨 [Lineage Portal] Generando Lineage Matrix Explorer para {client_name}..."
    )

    # Load the global state payload, containing system-wide configuration and metadata required for template hydration.
    global_payload_path = resolve_global_report_payload_path(client_name)
    if not global_payload_path.exists():
        logger.warning(
            f"⚠️ Payload global no encontrado en {global_payload_path}. Generando con dict vacío."
        )
        global_payload = {}
    else:
        global_payload = _load_json(global_payload_path)

    # Load the Digital Twin Object (DTO) state, which constitutes the primary operational data snapshot for visualization.
    dto_state_path = client_dir / "digital_twin_state.json"
    if not dto_state_path.exists():
        logger.warning(
            f"⚠️ Digital Twin State no encontrado en {dto_state_path}. Generando con dict vacío."
        )
        dto_state = {}
    else:
        dto_state = _load_json(dto_state_path)

    # Augment the primary Digital Twin Object (DTO) with supplementary, tower-specific metadata attributes.
    towers_detail = _load_towers_detail(client_name)

    #
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"No se encuentra la plantilla del portal en: {TEMPLATE_PATH}"
        )

    template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

    #
    template = jinja2.Template(template_content)
    rendered_html = template.render(
        client_name=client_name,
        sovereign_payload_json=json.dumps(global_payload, ensure_ascii=False),
        dto_state_json=json.dumps(dto_state, ensure_ascii=False),
        towers_detail_json=json.dumps(towers_detail, ensure_ascii=False),
    )

    #
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_html, encoding="utf-8")

    logger.info(
        f"✅ Lineage Matrix Explorer renderizado exitosamente en: {output_path}"
    )
    return output_path


def main(argv: list[str] | None = None) -> int:
    """Executes the lineage portal rendering process from the command line.

    Serves as the main entry point for the script. This function parses
    command-line arguments to identify a target client and subsequently
    invokes the rendering process for the Lineage Matrix Explorer.
    It handles argument validation and encapsulates rendering exceptions,
    translating outcomes into standard process exit codes.

    Args:
        argv: A list of command-line arguments. If None, `sys.argv` is used.
            The second element (`argv[1]`) is expected to be the client name.

    Returns:
        An integer exit code. Returns `0` for successful rendering and `1` for
        any failure, including an incorrect argument count or an exception
        raised during the rendering process.
    """
    args = argv if argv is not None else sys.argv
    if len(args) < 2:
        print("Uso: python -m adapters.render_lineage_portal <client_name>")
        return 1

    client_name = args[1]
    try:
        render_lineage_portal(client_name)
        return 0
    except Exception:
        logger.exception("❌ Fallo al renderizar el Lineage Matrix Explorer:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
