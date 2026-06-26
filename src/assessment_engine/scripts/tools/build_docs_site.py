# golden-path: ignore
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from assessment_engine.scripts.tools import (
    validate_documentation_governance as governance,
)


def render_markdown(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    output: list[str] = []
    in_code = False
    code_lines: list[str] = []
    in_list = False

    def flush_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    def flush_code() -> None:
        nonlocal in_code, code_lines
        if in_code:
            output.append("<pre><code>")
            output.append(html.escape("\n".join(code_lines)))
            output.append("</code></pre>")
            in_code = False
            code_lines = []

    for line in lines:
        if line.startswith("```"):
            if in_code:
                flush_code()
            else:
                flush_list()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            flush_list()
            continue

        heading_match = governance.MARKDOWN_HEADING_RE.match(line)
        if heading_match:
            flush_list()
            level = len(heading_match.group(1))
            content = html.escape(heading_match.group(2))
            output.append(
                f'<h{level} id="{governance.github_anchor_slug(heading_match.group(2))}">{content}</h{level}>'
            )
            continue

        if stripped.startswith(("- ", "* ")):
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{html.escape(stripped[2:])}</li>")
            continue

        flush_list()
        output.append(f"<p>{html.escape(stripped)}</p>")

    flush_list()
    flush_code()
    return "\n".join(output)


def build_site(
    repo_root: Path, documentation_map_path: Path, output_dir: Path
) -> None:
    documentation_map = governance.load_yaml(documentation_map_path)
    entries = {
        entry["path"]: entry
        for entry in documentation_map.get("entries", [])
        if isinstance(entry, dict) and entry.get("kind") == "document"
    }

    coverage = documentation_map.get("coverage", {})
    include_patterns = coverage.get(
        "include", governance.DEFAULT_COVERAGE_INCLUDE
    )
    exclude_patterns = coverage.get(
        "exclude", governance.DEFAULT_COVERAGE_EXCLUDE
    )

    governed_paths: list[str] = []
    for pattern in include_patterns:
        for discovered_path in repo_root.glob(pattern):
            if not discovered_path.is_file():
                continue
            normalized = governance.normalize_repo_path(discovered_path, repo_root)
            if governance.matches_any_pattern(normalized, exclude_patterns):
                continue
            governed_paths.append(normalized)

    governed_paths = sorted(set(governed_paths))
    pages: list[dict[str, object]] = []
    docs_dir = output_dir / "pages"
    docs_dir.mkdir(parents=True, exist_ok=True)

    for relative_path in governed_paths:
        source_path = repo_root / relative_path
        if source_path.suffix != ".md":
            continue

        text = source_path.read_text(encoding="utf-8")
        front_matter = governance.read_front_matter(source_path) or {}
        title = front_matter.get("title") or source_path.stem
        body = text.split("---\n", 2)[2] if text.startswith("---\n") else text
        rendered = render_markdown(body)
        page_name = relative_path.replace("/", "__") + ".html"
        page_path = docs_dir / page_name
        page_path.write_text(
            "\n".join(
                [
                    "<!DOCTYPE html>",
                    "<html><head><meta charset='utf-8'>",
                    f"<title>{html.escape(str(title))}</title>",
                    "<link rel='stylesheet' href='../site.css'>",
                    "</head><body>",
                    f"<nav><a href='../index.html'>Documentation index</a> / {html.escape(relative_path)}</nav>",
                    rendered,
                    "</body></html>",
                ]
            ),
            encoding="utf-8",
        )
        pages.append(
            {
                "path": relative_path,
                "title": title,
                "status": front_matter.get("status"),
                "doc_type": front_matter.get("doc_type"),
                "diataxis": front_matter.get("diataxis"),
                "verification_mode": front_matter.get("verification_mode"),
                "page": f"pages/{page_name}",
                "mapped": relative_path in entries,
            }
        )

    (output_dir / "site.css").write_text(
        "\n".join(
            [
                "body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 960px; line-height: 1.5; padding: 0 1rem; }",
                "nav { margin-bottom: 1.5rem; font-size: 0.95rem; }",
                "table { border-collapse: collapse; width: 100%; margin-top: 1rem; }",
                "th, td { border: 1px solid #d0d7de; padding: 0.5rem; text-align: left; vertical-align: top; }",
                "th { background: #f6f8fa; }",
                "code, pre { font-family: ui-monospace, monospace; }",
                "pre { overflow-x: auto; background: #f6f8fa; padding: 1rem; }",
            ]
        ),
        encoding="utf-8",
    )

    rows = "\n".join(
        f"<tr><td><a href='{html.escape(page['page'])}'>{html.escape(str(page['path']))}</a></td>"
        f"<td>{html.escape(str(page['status']))}</td>"
        f"<td>{html.escape(str(page['doc_type']))}</td>"
        f"<td>{html.escape(str(page['diataxis']))}</td>"
        f"<td>{html.escape(str(page['verification_mode']))}</td></tr>"
        for page in pages
    )
    (output_dir / "index.html").write_text(
        "\n".join(
            [
                "<!DOCTYPE html>",
                "<html><head><meta charset='utf-8'><title>Documentation preview</title><link rel='stylesheet' href='site.css'></head><body>",
                "<h1>Documentation preview</h1>",
                "<table><thead><tr><th>Path</th><th>Status</th><th>Type</th><th>Diataxis</th><th>Verification mode</th></tr></thead>",
                f"<tbody>{rows}</tbody></table>",
                "</body></html>",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "search-index.json").write_text(
        json.dumps(pages, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--documentation-map", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_site(
        repo_root=Path(args.repo_root).resolve(),
        documentation_map_path=Path(args.documentation_map).resolve(),
        output_dir=Path(args.output_dir).resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
