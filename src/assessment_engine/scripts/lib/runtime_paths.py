"""Runtime paths management for the Assessment Engine pipeline.

This module provides core utilities and logic for handling dynamic file and directory paths required during the pipeline's execution.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[4]
GLOBAL_REPORT_TEMPLATE_NAME = "11. Template Documento General Alpha v.05.docx"
TOWER_ANNEX_TEMPLATE_NAME = "Template_Documento_Anexos_Alpha_v06_Tower_Annex_v2_6.docx"
WEB_DASHBOARD_TEMPLATE_NAME = "web_dashboard.html"


def resolve_working_dir() -> Path:
    """Resolve the absolute path to the project's working directory."""
    return ROOT / "working"


def resolve_tower_id(default: str = "T5") -> str:
    """Resolve the assessment tower ID from the environment, using a default if unset or empty."""
    return os.environ.get("ASSESSMENT_TOWER_ID", default).strip() or default


def resolve_client_id(default: str = "generic_client") -> str:
    """{'docstring': 'Return the `ASSESSMENT_CLIENT_ID` environment variable, falling back to a default if unset or empty.'}."""
    return os.environ.get("ASSESSMENT_CLIENT_ID", default).strip() or default


def resolve_client_dir(default_client: str = "generic_client") -> Path:
    """Resolves the client working directory path with a legacy location fallback.

    The function determines the path by checking two locations in order of
    precedence. It first constructs a primary path by appending a resolved
    client ID to the path from `resolve_working_dir()`. If this primary path does
    not exist, it checks for a legacy path.

    The primary path is returned if it exists, or if neither path exists. The
    legacy path is returned only if it exists and the primary path does not.

    Args:
        default_client: An identifier used to derive the client-specific directory
            name. This serves as a default if a more specific client ID cannot
            be resolved internally.

    Returns:
        A `pathlib.Path` object for the client's working directory. The path is
        not guaranteed to exist on the filesystem.
    """
    client_id = resolve_client_id(default_client)
    primary = resolve_working_dir() / client_id
    legacy = ROOT / "src" / "assessment_engine" / "working" / client_id
    if primary.exists() or not legacy.exists():
        return primary
    return legacy


def resolve_case_dir(
    default_client: str = "generic_client", default_tower: str = "T1"
) -> Path:
    """Resolves the absolute path to the assessment case directory.

    The path is determined with the following priority:
    1. The value of the `ASSESSMENT_CASE_DIR` environment variable, if set and
       not an empty string.
    2. A path constructed from the default client and tower identifiers.

    Args:
        default_client (str): The default client name to use if the environment
            variable `ASSESSMENT_CASE_DIR` is not set.
        default_tower (str): The default tower ID to use if the environment
            variable `ASSESSMENT_CASE_DIR` is not set.

    Returns:
        pathlib.Path: The absolute, resolved path to the case directory.
    """
    override = os.environ.get("ASSESSMENT_CASE_DIR", "").strip()
    if override:
        return Path(override).resolve()
    return resolve_client_dir(default_client) / resolve_tower_id(default_tower)


def resolve_case_input_path(
    default_client: str = "generic_client",
    default_tower: str = "T1",
) -> Path:
    """Resolve the path to the main case input JSON file."""
    return resolve_case_dir(default_client, default_tower) / "case_input.json"


def resolve_client_intelligence_path(default_client: str = "generic_client") -> Path:
    """Resolve the absolute path to the 'client_intelligence.json' file for a client."""
    return resolve_client_dir(default_client) / "client_intelligence.json"


def resolve_global_report_payload_path(default_client: str = "generic_client") -> Path:
    """Resolve the absolute path to a client's `global_report_payload.json` file."""
    return resolve_client_dir(default_client) / "global_report_payload.json"


def resolve_commercial_report_payload_path(
    default_client: str = "generic_client",
) -> Path:
    """Resolve the absolute path to the `commercial_report_payload.json` file."""
    return resolve_client_dir(default_client) / "commercial_report_payload.json"


def resolve_blueprint_payload_filename(tower_id: str) -> str:
    """{'docstring': "Construct the standardized filename for a tower's blueprint payload."}."""
    return f"blueprint_{tower_id.lower()}_payload.json"


def resolve_blueprint_payload_path(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> Path:
    r"""{'docstring': 'Resolve the absolute path to a blueprint payload file.\n\n    Constructs an absolute path by joining a case directory with a payload\n    filename. The case directory is resolved using both the client and tower\n    identifiers, while the payload filename is resolved using only the tower\n    identifier.\n\n    Args:\n        default_client: The client identifier used to determine the case directory.\n        default_tower: The tower identifier used to determine the case directory\n            and the payload filename.\n\n    Returns:\n        An absolute `pathlib.Path` object representing the full path to the\n        payload file.'}."""
    tower_id = resolve_tower_id(default_tower)
    return resolve_case_dir(
        default_client, tower_id
    ) / resolve_blueprint_payload_filename(tower_id)


def resolve_blueprint_payload_candidates(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> tuple[Path, ...]:
    """Constructs candidate file paths for a blueprint payload.

    This function generates two potential `pathlib.Path` objects for locating a
    blueprint payload file based on client and tower identifiers. The first
    path is constructed using a standardized filename from the
    `resolve_blueprint_payload_filename` function. The second path is a
    fallback using a common naming convention.

    Both paths are located within a case-specific directory derived from the
    client and tower identifiers. This function does not perform any I/O and
    does not verify the existence of the files at the returned paths.

    Args:
        default_client: The client identifier used to determine the case directory.
        default_tower: The tower identifier used to determine the case directory
            and the payload filename.

    Returns:
        A tuple of two `pathlib.Path` objects representing the primary and
        fallback candidate paths for the blueprint payload file.
    """
    tower_id = resolve_tower_id(default_tower)
    case_dir = resolve_case_dir(default_client, tower_id)
    return (
        case_dir / resolve_blueprint_payload_filename(tower_id),
        case_dir / f"blueprint_{tower_id.upper()}_payload.json",
    )


def resolve_annex_template_payload_filename(tower_id: str) -> str:
    """Return the standardized filename for an approved annex template payload."""
    return f"approved_annex_{tower_id.lower()}.template_payload.json"


def resolve_annex_template_payload_path(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> Path:
    """Resolve the full path to an annex template payload file.

    Constructs the path by resolving a tower ID from the tower name, finding the
    appropriate case directory for the client and tower, and appending the
    tower-specific payload filename.

    Args:
        default_client: Client identifier used to locate the root case directory.
        default_tower: Tower model identifier (e.g., 'T5') used to resolve
            the tower-specific directory and payload filename.

    Returns:
        The full `pathlib.Path` to the payload file.

    Raises:
        ValueError: If `default_tower` is not a valid tower identifier.
    """
    tower_id = resolve_tower_id(default_tower)
    return resolve_case_dir(
        default_client,
        tower_id,
    ) / resolve_annex_template_payload_filename(tower_id)


def resolve_tower_definition_file(default_tower: str = "T5") -> Path:
    """Constructs the absolute `pathlib.Path` to a tower's JSON definition file.

    This function first resolves the provided tower identifier into a canonical
    tower ID, and then constructs a path based on a predefined directory layout.
    The expected final path format is:
    `ROOT/engine_config/towers/{tower_id}/tower_definition_{tower_id}.json`.

    Args:
        default_tower: The identifier for the tower to resolve.

    Returns:
        A `pathlib.Path` object for the corresponding tower definition file.

    Raises:
        ValueError: Propagated if the `default_tower` identifier cannot be
            resolved to a valid canonical tower ID.
    """
    tower_id = resolve_tower_id(default_tower)
    return (
        ROOT
        / "engine_config"
        / "towers"
        / tower_id
        / f"tower_definition_{tower_id}.json"
    )


def resolve_global_report_template_path() -> Path:
    """Resolve the absolute path to the global report template file."""
    return ROOT / "source_docs" / "templates" / GLOBAL_REPORT_TEMPLATE_NAME


def resolve_tower_annex_template_path() -> Path:
    """Return the absolute path to the Tower Annex template file."""
    return ROOT / "templates" / TOWER_ANNEX_TEMPLATE_NAME


def resolve_web_dashboard_template_path() -> Path:
    """Resolve the absolute path to the web dashboard template file."""
    return (
        ROOT / "src" / "assessment_engine" / "templates" / WEB_DASHBOARD_TEMPLATE_NAME
    )
