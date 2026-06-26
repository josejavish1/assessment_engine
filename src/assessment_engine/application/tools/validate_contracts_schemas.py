# golden-path: ignore
from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path

from assessment_engine.application.tools import (
    validate_documentation_governance as governance,
)


def normalize_type_annotation(annotation) -> str:
    if annotation is None:
        return "None"
    type_str = str(annotation)
    type_str = type_str.replace("typing.", "")
    # Remove module prefixes, e.g. domain.schemas.blueprint.BlueprintPayload -> BlueprintPayload
    type_str = re.sub(r"[a-zA-Z0-9_]+\.(?=[a-zA-Z0-9_])", "", type_str)
    type_str = type_str.replace("List[", "list[").replace("Dict[", "dict[")
    type_str = type_str.replace("NoneType", "None")
    return type_str


def check_type_compatibility(pydantic_type: str, documented_type: str) -> bool:
    p_type = pydantic_type.lower().replace(" ", "")
    d_type = documented_type.lower().replace(" ", "")

    if p_type == d_type:
        return True

    # Handle Optional wrappers
    if "optional[" in p_type:
        inner = p_type.split("optional[", 1)[1].rsplit("]", 1)[0]
        if d_type == inner:
            return True

    # Handle Union wrappers
    if "union[" in p_type:
        inner_content = p_type.split("union[", 1)[1].rsplit("]", 1)[0]
        union_types = [t.strip() for t in inner_content.split(",")]
        if d_type in union_types:
            return True

    # Allow dict <=> dict mapping or model list mappings
    if p_type == "dict" and d_type == "dict":
        return True
    if p_type.startswith("list[") and d_type == "list[dict]":
        return True
    if p_type == "str" and d_type == "str":
        return True

    return False


def parse_markdown_table_row(line: str) -> dict | None:
    stripped_line = line.strip()
    if not stripped_line.startswith("|") or not stripped_line.endswith("|"):
        return None

    cols = [col.strip() for col in stripped_line.split("|")]
    cols = cols[1:-1]
    if len(cols) < 2:
        return None

    # Skip separators
    if all(re.match(r"^:?-+:?$", col) for col in cols):
        return None

    field_name_raw = cols[0]
    field_name_match = re.match(r"^`([a-zA-Z0-9_]+)`$", field_name_raw)
    field_name = field_name_match.group(1) if field_name_match else field_name_raw
    if field_name.lower() in {"campo", "field"}:
        return None

    type_raw = cols[1]
    type_match = re.match(r"^`([^`]+)`$", type_raw)
    field_type = type_match.group(1) if type_match else type_raw

    alias = None
    if len(cols) >= 4:
        alias_raw = cols[2]
        alias_match = re.match(r"^`([a-zA-Z0-9_]+)`$", alias_raw)
        alias = alias_match.group(1) if alias_match else alias_raw
        if alias.lower() in {"alias json", "n/a", ""}:
            alias = None

    return {"field_name": field_name, "field_type": field_type, "alias": alias}


def extract_markdown_models_and_tables(absolute_path: Path) -> dict[str, list[dict]]:
    text = absolute_path.read_text(encoding="utf-8")
    models: dict[str, list[dict]] = {}
    current_model: str | None = None
    lines = text.splitlines()

    heading_re = re.compile(r"^(#{2,4})\s+.*?\`([A-Z][a-zA-Z0-9_]+)\`")

    for i, line in enumerate(lines):
        heading_match = heading_re.match(line)
        if heading_match:
            current_model = heading_match.group(2)
            models[current_model] = []
            continue

        if current_model is not None and line.strip().startswith("|"):
            row = parse_markdown_table_row(line)
            if row:
                models[current_model].append(row)

    return models


def validate_contracts_schemas(
    repo_root: Path, documentation_map_path: Path
) -> list[str]:
    documentation_map = governance.load_yaml(documentation_map_path)
    errors: list[str] = []

    # Inject repo_root/src into path for imports
    src_dir = str(repo_root / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    for entry in documentation_map.get("entries", []):
        if not isinstance(entry, dict) or entry.get("kind") != "document":
            continue
        if entry.get("verification_mode") != "schema":
            continue

        path = entry.get("path")
        if not isinstance(path, str) or not path.endswith(".md"):
            continue

        absolute_path = repo_root / path
        if not absolute_path.exists():
            continue

        source_of_truth = entry.get("source_of_truth", [])
        python_source = None
        for source in source_of_truth:
            # Resolve relative to markdown directory
            resolved = (absolute_path.parent / source).resolve()
            if resolved.exists() and resolved.suffix == ".py":
                python_source = resolved
                break

        if not python_source:
            continue

        # Convert python_source to modular import string
        # e.g., /.../src/domain/schemas/blueprint.py -> domain.schemas.blueprint
        try:
            relative_py = python_source.relative_to(repo_root / "src")
            module_name = ".".join(relative_py.with_suffix("").parts)
            module = importlib.import_module(module_name)
        except Exception as err:
            errors.append(
                f"{path}: failed to import source of truth module for {python_source.name}: {err}"
            )
            continue

        extracted_models = extract_markdown_models_and_tables(absolute_path)
        for class_name, fields in extracted_models.items():
            model_class = getattr(module, class_name, None)
            if model_class is None:
                # Class might be imported in another namespace, look wider or log warning/skip
                continue

            # Ensure it is a Pydantic model
            if not hasattr(model_class, "model_fields"):
                continue

            pydantic_fields = model_class.model_fields
            {f["field_name"] for f in fields}

            # Check for missing fields (present in Pydantic but not in MD)
            # Skip private/internal pydantic fields or VersionedPayload inheritances depending on strictness
            for p_field_name, p_field_def in pydantic_fields.items():
                if p_field_name.startswith("_"):
                    continue

                # Check by field name or its designated alias
                has_documented = False
                for f in fields:
                    if f["field_name"] == p_field_name:
                        has_documented = True
                        break
                    if f["alias"] and f["alias"] == p_field_name:
                        has_documented = True
                        break
                    if p_field_def.alias and (
                        p_field_def.alias == f["field_name"]
                        or p_field_def.alias == f["alias"]
                    ):
                        has_documented = True
                        break

                if not has_documented:
                    errors.append(
                        f"{path}: model '{class_name}' is missing documentation for field '{p_field_name}'"
                    )

            # Check for obsolete fields and type matches
            for f in fields:
                f_name = f["field_name"]
                f_type = f["field_type"]

                # Find the Pydantic definition
                p_field_def = pydantic_fields.get(f_name)
                if not p_field_def:
                    # Check if matching by alias
                    for pf_name, pf_def in pydantic_fields.items():
                        if (
                            pf_def.alias == f_name
                            or pf_def.alias == f["alias"]
                            or pf_name == f["alias"]
                        ):
                            p_field_def = pf_def
                            break

                if not p_field_def:
                    errors.append(
                        f"{path}: documentation lists obsolete or non-existent field '{f_name}' in model '{class_name}'"
                    )
                    continue

                # Type check
                p_type_str = normalize_type_annotation(p_field_def.annotation)
                if not check_type_compatibility(p_type_str, f_type):
                    errors.append(
                        f"{path}: field '{f_name}' type mismatch in model '{class_name}' (documented as '{f_type}', code is '{p_type_str}')"
                    )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_contracts_schemas(
        repo_root=Path(args.repo_root).resolve(),
        documentation_map_path=Path(args.documentation_map).resolve(),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Contract schemas and models validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
