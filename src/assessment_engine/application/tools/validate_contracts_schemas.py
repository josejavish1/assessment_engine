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
    type_str = re.sub(r"[a-zA-Z0-9_]+\.(?=[a-zA-Z0-9_])", "", type_str)
    type_str = type_str.replace("List[", "list[").replace("Dict[", "dict[")
    type_str = type_str.replace("NoneType", "None")
    return type_str


def check_type_compatibility(pydantic_type: str, documented_type: str) -> bool:
    p_type = pydantic_type.lower().replace(" ", "")
    d_type = documented_type.lower().replace(" ", "")

    if p_type == d_type:
        return True

    if "optional[" in p_type:
        inner = p_type.split("optional[", 1)[1].rsplit("]", 1)[0]
        if d_type == inner:
            return True

    if "union[" in p_type:
        inner_content = p_type.split("union[", 1)[1].rsplit("]", 1)[0]
        union_types = [t.strip() for t in inner_content.split(",")]
        if d_type in union_types:
            return True

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
    description = ""
    if len(cols) == 3:
        description = cols[2]
    elif len(cols) >= 4:
        alias_raw = cols[2]
        alias_match = re.match(r"^`([a-zA-Z0-9_]+)`$", alias_raw)
        alias = alias_match.group(1) if alias_match else alias_raw
        if alias.lower() in {"alias json", "n/a", ""}:
            alias = None
        description = cols[3]

    return {
        "field_name": field_name,
        "field_type": field_type,
        "alias": alias,
        "description": description,
    }


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


def generate_markdown_table_lines(model_class, old_fields: list[dict]) -> list[str]:
    # Map old field names (or aliases) to their human descriptions to prevent data loss
    old_descriptions: dict[str, str] = {}
    for f in old_fields:
        old_descriptions[f["field_name"]] = f["description"]
        if f["alias"]:
            old_descriptions[f["alias"]] = f["description"]

    has_aliases = any(
        f_def.alias is not None for f_def in model_class.model_fields.values()
    )

    table_lines = []
    if has_aliases:
        table_lines.append("| Campo | Tipo | Alias JSON | Descripción |")
        table_lines.append("|---|---|---|---|")
        for f_name, f_def in model_class.model_fields.items():
            if f_name.startswith("_"):
                continue
            alias_str = f"`{f_def.alias}`" if f_def.alias else "N/A"
            type_str = normalize_type_annotation(f_def.annotation)
            # Retrieve description with robust fallback
            desc = old_descriptions.get(f_name) or old_descriptions.get(
                f_def.alias or ""
            )
            if not desc:
                desc = f_def.description or "Descripción del campo."
            desc = desc.replace("\n", " ").strip()
            table_lines.append(f"| `{f_name}` | `{type_str}` | {alias_str} | {desc} |")
    else:
        table_lines.append("| Campo | Tipo | Descripción |")
        table_lines.append("|---|---|---|")
        for f_name, f_def in model_class.model_fields.items():
            if f_name.startswith("_"):
                continue
            type_str = normalize_type_annotation(f_def.annotation)
            desc = old_descriptions.get(f_name)
            if not desc:
                desc = f_def.description or "Descripción del campo."
            desc = desc.replace("\n", " ").strip()
            table_lines.append(f"| `{f_name}` | `{type_str}` | {desc} |")

    return table_lines


def replace_table_in_markdown(
    file_content: str, class_name: str, new_table_lines: list[str]
) -> str:
    lines = file_content.splitlines()
    heading_re = re.compile(r"^(#{2,4})\s+.*?\`" + re.escape(class_name) + r"\`")

    heading_idx = -1
    for idx, line in enumerate(lines):
        if heading_re.match(line):
            heading_idx = idx
            break

    if heading_idx == -1:
        return file_content

    table_start_idx = -1
    for idx in range(heading_idx + 1, len(lines)):
        line = lines[idx].strip()
        if line.startswith("#"):
            break
        if line.startswith("|"):
            table_start_idx = idx
            break

    if table_start_idx == -1:
        return file_content

    table_end_idx = table_start_idx
    for idx in range(table_start_idx, len(lines)):
        line = lines[idx].strip()
        if not line.startswith("|"):
            break
        table_end_idx = idx

    before = lines[:table_start_idx]
    after = lines[table_end_idx + 1 :]
    return "\n".join(before + new_table_lines + after)


def validate_contracts_schemas(
    repo_root: Path, documentation_map_path: Path, autofix: bool = False
) -> list[str]:
    documentation_map = governance.load_yaml(documentation_map_path)
    errors: list[str] = []

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
            resolved = (absolute_path.parent / source).resolve()
            if resolved.exists() and resolved.suffix == ".py":
                python_source = resolved
                break

        if not python_source:
            continue

        try:
            relative_py = python_source.relative_to(repo_root / "src")
            module_name = ".".join(relative_py.with_suffix("").parts)
            # Reload module dynamically
            if module_name in sys.modules:
                del sys.modules[module_name]
            module = importlib.import_module(module_name)
        except Exception as err:
            errors.append(
                f"{path}: failed to import source of truth module for {python_source.name}: {err}"
            )
            continue

        extracted_models = extract_markdown_models_and_tables(absolute_path)
        file_content = absolute_path.read_text(encoding="utf-8")
        file_modified = False

        for class_name, fields in extracted_models.items():
            model_class = getattr(module, class_name, None)
            if model_class is None or not hasattr(model_class, "model_fields"):
                continue

            pydantic_fields = model_class.model_fields
            model_has_drift = False

            # Check missing fields
            for p_field_name, p_field_def in pydantic_fields.items():
                if p_field_name.startswith("_"):
                    continue

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
                    model_has_drift = True
                    if not autofix:
                        errors.append(
                            f"{path}: model '{class_name}' is missing documentation for field '{p_field_name}'"
                        )

            # Check obsolete and type mismatches
            for f in fields:
                f_name = f["field_name"]
                f_type = f["field_type"]

                p_field_def = pydantic_fields.get(f_name)
                if not p_field_def:
                    for pf_name, pf_def in pydantic_fields.items():
                        if (
                            pf_def.alias == f_name
                            or pf_def.alias == f["alias"]
                            or pf_name == f["alias"]
                        ):
                            p_field_def = pf_def
                            break

                if not p_field_def:
                    model_has_drift = True
                    if not autofix:
                        errors.append(
                            f"{path}: documentation lists obsolete or non-existent field '{f_name}' in model '{class_name}'"
                        )
                    continue

                p_type_str = normalize_type_annotation(p_field_def.annotation)
                if not check_type_compatibility(p_type_str, f_type):
                    model_has_drift = True
                    if not autofix:
                        errors.append(
                            f"{path}: field '{f_name}' type mismatch in model '{class_name}' (documented as '{f_type}', code is '{p_type_str}')"
                        )

            if model_has_drift and autofix:
                print(f"Auto-fixing schema table for '{class_name}' in '{path}'...")
                new_table = generate_markdown_table_lines(model_class, fields)
                file_content = replace_table_in_markdown(
                    file_content, class_name, new_table
                )
                file_modified = True

        if file_modified and autofix:
            absolute_path.write_text(file_content, encoding="utf-8")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    parser.add_argument("--autofix", action="store_true", default=False)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_contracts_schemas(
        repo_root=Path(args.repo_root).resolve(),
        documentation_map_path=Path(args.documentation_map).resolve(),
        autofix=args.autofix,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if args.autofix:
        print("Contract schemas auto-fixed and reconciled successfully.")
    else:
        print("Contract schemas and models validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
