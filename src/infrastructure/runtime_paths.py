"""Establishes a canonical source for dynamic runtime paths and foundational file system utilities used throughout the Assessment Engine pipeline."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_REPORT_TEMPLATE_NAME = "11. Template Documento General Alpha v.05.docx"
TOWER_ANNEX_TEMPLATE_NAME = "Template_Documento_Anexos_Alpha_v06_Tower_Annex_v2_6.docx"
WEB_DASHBOARD_TEMPLATE_NAME = "web_dashboard.html"


def resolve_working_dir() -> Path:
    """Return the absolute path to the project's 'working' subdirectory."""
    return ROOT / "working"


def resolve_tower_id(default: str = "T5") -> str:
    """Resolve the tower ID from the `ASSESSMENT_TOWER_ID` environment variable, defaulting if the variable is unset or blank."""
    return os.environ.get("ASSESSMENT_TOWER_ID", default).strip() or default


def resolve_client_id(default: str = "generic_client") -> str:
    """Resolve the client ID from the `ASSESSMENT_CLIENT_ID` environment variable, returning a default if the variable is unset or contains only whitespace."""
    return os.environ.get("ASSESSMENT_CLIENT_ID", default).strip() or default


def resolve_client_dir(default_client: str = "generic_client") -> Path:
    """Resolve the client-specific working directory path.

    Derives a path from a client identifier, which is resolved from the
    execution environment and then slugified for filesystem compatibility.
    The function prioritizes a primary, standardized path over a legacy one.

    The resolution logic is as follows:
    1.  If the primary path exists, it is returned.
    2.  If the primary path does not exist but a legacy path does, the legacy
        path is returned for backward compatibility.
    3.  If neither path exists, the primary path is returned as the designated
        default, though it is not guaranteed to exist.

    Args:
        default_client (str): The client identifier to use as a fallback if one
            cannot be determined from the current execution environment.

    Returns:
        pathlib.Path: The resolved absolute path to the client's working
            directory. This path is not guaranteed to exist on the filesystem.
    """
    from infrastructure.text_utils import slugify

    client_id = slugify(resolve_client_id(default_client))
    primary = resolve_working_dir() / client_id
    legacy = ROOT / "src" / "assessment_engine" / "working" / client_id
    if primary.exists() or not legacy.exists():
        return primary
    return legacy


def resolve_case_dir(
    default_client: str = "generic_client", default_tower: str = "T1"
) -> Path:
    r"""{'docstring': 'Resolve the absolute path for an assessment case directory.\n\nThe path is determined by first checking for a non-empty `ASSESSMENT_CASE_DIR`\nenvironment variable. If this variable is set, its value is resolved to an\nabsolute path and returned immediately.\n\nIf the environment variable is unset or empty, a fallback path is constructed\nby joining the results of `resolve_client_dir()` and `resolve_tower_id()`\nusing the provided default identifiers.\n\nArgs:\n    default_client: The client identifier used to construct the path if the\n        `ASSESSMENT_CASE_DIR` environment variable is not set.\n    default_tower: The tower identifier used to construct the path if the\n        `ASSESSMENT_CASE_DIR` environment variable is not set.\n\nReturns:\n    A `pathlib.Path` object representing the fully resolved, absolute path to\n    the case directory.'}."""
    override = os.environ.get("ASSESSMENT_CASE_DIR", "").strip()
    if override:
        return Path(override).resolve()
    return resolve_client_dir(default_client) / resolve_tower_id(default_tower)


def resolve_case_input_path(
    default_client: str = "generic_client",
    default_tower: str = "T1",
) -> Path:
    """Construct the absolute path to the `case_input.json` file in a case directory."""
    return resolve_case_dir(default_client, default_tower) / "case_input.json"


def resolve_client_intelligence_path(default_client: str = "generic_client") -> Path:
    """Resolves the absolute path to the client's `client_intelligence.json` file."""
    return resolve_client_dir(default_client) / "client_intelligence.json"


def resolve_global_report_payload_path(default_client: str = "generic_client") -> Path:
    """Resolve the absolute path to the global report payload file for a client."""
    return resolve_client_dir(default_client) / "global_report_payload.json"


def resolve_commercial_report_payload_path(
    default_client: str = "generic_client",
) -> Path:
    """Resolve the absolute path to a client's commercial report payload file."""
    return resolve_client_dir(default_client) / "commercial_report_payload.json"


def resolve_blueprint_payload_filename(tower_id: str) -> str:
    """Generate the standard filename for a tower's blueprint payload."""
    return f"blueprint_{tower_id.lower()}_payload.json"


def resolve_blueprint_payload_path(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> Path:
    """Resolve the absolute path to the blueprint payload file.

    This function constructs the full path by first resolving a tower identifier
    from the `default_tower` string. The resulting tower ID and the `default_client`
    are then used to determine the base case directory. Finally, the specific
    payload filename, also derived from the tower ID, is appended to form the
    complete, absolute path.

    Args:
        default_client: The client identifier used to locate the case directory.
        default_tower: The tower identifier string (e.g., 'T5') which is resolved
            to a canonical tower ID.

    Returns:
        A pathlib.Path object representing the absolute path to the blueprint
        payload file.

    Raises:
        ValueError: If `default_tower` cannot be resolved to a valid tower ID by
            the underlying `resolve_tower_id` function, or if the combination of
            `default_client` and the resolved tower ID is invalid for
            `resolve_case_dir`.
    """
    tower_id = resolve_tower_id(default_tower)
    return resolve_case_dir(
        default_client, tower_id
    ) / resolve_blueprint_payload_filename(tower_id)


def resolve_blueprint_payload_candidates(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> tuple[Path, ...]:
    """Generate candidate file paths for a blueprint payload configuration.

    Constructs two potential `pathlib.Path` objects for locating a blueprint
    payload file. The function first resolves a case directory from `default_client`
    and a tower identifier from `default_tower`. It then generates two paths
    within this directory: one using `resolve_blueprint_payload_filename()` and a
    second using the pattern "blueprint_{TOWER_ID}_payload.json".

    Args:
        default_client: Client identifier used to resolve the case directory.
            Defaults to "generic_client".
        default_tower: Tower identifier used for path construction.
            Defaults to "T5".

    Returns:
        A 2-tuple of `pathlib.Path` objects representing the two candidate
        file paths. The first is generated by `resolve_blueprint_payload_filename`,
        and the second follows the format `blueprint_{TOWER_ID}_payload.json`.

    Raises:
        ValueError: If `default_tower` or `default_client` cannot be resolved
            to a valid tower ID or case directory, respectively.
    """
    tower_id = resolve_tower_id(default_tower)
    case_dir = resolve_case_dir(default_client, tower_id)
    return (
        case_dir / resolve_blueprint_payload_filename(tower_id),
        case_dir / f"blueprint_{tower_id.upper()}_payload.json",
    )


def resolve_annex_template_payload_filename(tower_id: str) -> str:
    """Generate the standardized filename for an approved annex template payload."""
    return f"approved_annex_{tower_id.lower()}.template_payload.json"


def resolve_annex_template_payload_path(
    default_client: str = "generic_client",
    default_tower: str = "T5",
) -> Path:
    r"""{'docstring': 'Construct the full path to an annex template payload file.\n\n    Composes a `pathlib.Path` by combining a case-specific directory with a\n    payload filename. Both path components are derived from the provided\n    client and tower model identifiers.\n\n    Args:\n        default_client: The client identifier used to determine the case-specific\n            base directory.\n        default_tower: The tower model identifier (e.g., "T5") used to resolve\n            both the case directory and the final payload filename.\n\n    Returns:\n        A `pathlib.Path` object representing the fully resolved path to the\n        annex template payload file.\n\n    Raises:\n        ValueError: If `default_tower` is not a recognized tower model\n            identifier.'}."""
    tower_id = resolve_tower_id(default_tower)
    return resolve_case_dir(
        default_client,
        tower_id,
    ) / resolve_annex_template_payload_filename(tower_id)


def resolve_tower_definition_file(default_tower: str = "T5") -> Path:
    r"""{'docstring': 'Resolves a tower ID from a name or alias to construct the canonical path to its definition file.\n\nThis function first translates a human-readable tower name or alias (e.g., "T5")\ninto a canonical tower ID. It then uses this ID to construct the absolute\nfilesystem path to the corresponding `tower_definition_{tower_id}.json` file.\nNote that this function does not verify that the file exists at the\nconstructed path.\n\nArgs:\n    default_tower (str): The name or alias of the tower. Defaults to "T5".\n\nReturns:\n    pathlib.Path: The constructed absolute path to the tower\'s definition file.\n\nRaises:\n    ValueError: If the provided `default_tower` name or alias does not\n        correspond to a known tower ID.'}."""
    tower_id = resolve_tower_id(default_tower)
    return (
        ROOT
        / "engine_config"
        / "towers"
        / tower_id
        / f"tower_definition_{tower_id}.json"
    )


def resolve_global_report_template_path() -> Path:
    """Resolve the absolute path to the global report template."""
    return ROOT / "source_docs" / "templates" / GLOBAL_REPORT_TEMPLATE_NAME


def resolve_tower_annex_template_path() -> Path:
    """Resolve the absolute path to the Tower Annex template file."""
    return ROOT / "templates" / TOWER_ANNEX_TEMPLATE_NAME


def resolve_web_dashboard_template_path() -> Path:
    """Resolve the absolute path to the web dashboard HTML template."""
    return ROOT / "templates" / WEB_DASHBOARD_TEMPLATE_NAME
