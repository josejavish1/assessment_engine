"""
Módulo runtime_paths.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

if "APEX_WORKSPACE_DIR" in os.environ:
    ROOT = Path(os.environ["APEX_WORKSPACE_DIR"]).resolve()
else:
    ROOT = Path(__file__).resolve().parents[4]
GLOBAL_REPORT_TEMPLATE_NAME = "11. Template Documento General Alpha v.05.docx"
TOWER_ANNEX_TEMPLATE_NAME = "Template_Documento_Anexos_Alpha_v06_Tower_Annex_v2_6.docx"
WEB_DASHBOARD_TEMPLATE_NAME = "dashboard.html"


def resolve_working_dir() -> Path:
    return ROOT / "working"


def resolve_tower_id(default: str = "T5") -> str:
    return os.environ.get("ASSESSMENT_TOWER_ID", default).strip() or default


def resolve_client_id(default: str = "generic_client") -> str:
    return os.environ.get("ASSESSMENT_CLIENT_ID", default).strip() or default


def resolve_client_dir(default_client: str = "generic_client") -> Path:
    client_id = resolve_client_id(default_client)
    primary = resolve_working_dir() / client_id
    legacy = ROOT / "src" / "assessment_engine" / "working" / client_id
    if primary.exists() or not legacy.exists():
        return primary
    return legacy


def resolve_case_dir(
    default_client: str = "generic_client", default_tower: str = "T1"
) -> Path:
    override = os.environ.get("ASSESSMENT_CASE_DIR", "").strip()
    if override:
        return Path(override).resolve()
    return resolve_client_dir(default_client) / resolve_tower_id(default_tower)


def resolve_case_input_path(
    default_client: str = "generic_client",
    default_tower: str = "T1",
) -> Path:
    return resolve_case_dir(default_client, default_tower) / "case_input.json"


def resolve_client_intelligence_path(default_client: str = "generic_client") -> Path:
    return resolve_client_dir(default_client) / "client_intelligence.json"


def resolve_global_report_payload_path(default_client: str = "generic_client") -> Path:
    return resolve_client_dir(default_client) / "global_report_payload.json"


def resolve_commercial_report_payload_path(
    default_client: str = "generic_client",
) -> Path:
    return resolve_client_dir(default_client) / "commercial_report_payload.json"


def resolve_blueprint_payload_filename(tower_id: str) -> str:
    return f"blueprint_{tower_id.lower()}_payload.json"


def resolve_blueprint_payload_path(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> Path:
    tower_id = resolve_tower_id(default_tower)
    return resolve_case_dir(
        default_client, tower_id
    ) / resolve_blueprint_payload_filename(tower_id)


def resolve_blueprint_payload_candidates(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> tuple[Path, ...]:
    tower_id = resolve_tower_id(default_tower)
    case_dir = resolve_case_dir(default_client, tower_id)
    return (
        case_dir / resolve_blueprint_payload_filename(tower_id),
        case_dir / f"blueprint_{tower_id.upper()}_payload.json",
    )


def resolve_annex_template_payload_filename(tower_id: str) -> str:
    return f"approved_annex_{tower_id.lower()}.template_payload.json"


def resolve_annex_template_payload_path(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> Path:
    tower_id = resolve_tower_id(default_tower)
    return resolve_case_dir(
        default_client,
        tower_id,
    ) / resolve_annex_template_payload_filename(tower_id)


def resolve_tower_definition_file(default_tower: str = "T5") -> Path:
    tower_id = resolve_tower_id(default_tower)
    return (
        ROOT
        / "engine_config"
        / "towers"
        / tower_id
        / f"tower_definition_{tower_id}.json"
    )


def resolve_global_report_template_path() -> Path:
    return ROOT / "source_docs" / "templates" / GLOBAL_REPORT_TEMPLATE_NAME


def resolve_tower_annex_template_path() -> Path:
    return ROOT / "templates" / TOWER_ANNEX_TEMPLATE_NAME


def resolve_web_dashboard_template_path() -> Path:
    return (
        ROOT / "src" / "assessment_engine" / "templates" / "web_dashboard"
    )
