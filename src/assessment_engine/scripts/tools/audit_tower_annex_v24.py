"""
Módulo audit_tower_annex_v24.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}")
SUSPICIOUS_PATTERNS = [
    r"\{'statement':",
    r'"statement":',
    r"\.\.\.",
]


def read_zip_xml_texts(docx_path: Path):
    texts = []
    with zipfile.ZipFile(docx_path, "r") as zf:
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                try:
                    texts.append(zf.read(name).decode("utf-8", errors="ignore"))
                except Exception:
                    pass
    return texts


def extract_placeholders_from_docx(docx_path: Path):
    found = set()
    for text in read_zip_xml_texts(docx_path):
        found.update(PLACEHOLDER_RE.findall(text))
    return sorted(found)


def extract_suspicious_from_docx(docx_path: Path):
    joined = "\n".join(read_zip_xml_texts(docx_path))
    result = {}
    for pat in SUSPICIOUS_PATTERNS:
        result[pat] = len(re.findall(pat, joined))
    return result


def extract_placeholders_from_py(py_path: Path):
    text = py_path.read_text(encoding="utf-8", errors="ignore")
    return sorted(set(PLACEHOLDER_RE.findall(text)))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_get(data, path, default=None):
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 4:
        raise SystemExit(
            "Uso: python -m scripts.tools.audit_tower_annex_v24 <template_docx> <payload_json> <output_docx>"
        )

    template_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    payload_path = Path((argv if argv is not None else sys.argv)[2]).resolve()
    output_path = Path((argv if argv is not None else sys.argv)[3]).resolve()
    renderer_path = (
        Path(__file__).resolve().parents[3] / "render_tower_annex_from_template.py"
    )

    print("=== PATHS ===")
    print("template =", template_path)
    print("payload  =", payload_path)
    print("output   =", output_path)
    print("renderer =", renderer_path)

    print("\n=== EXISTENCE ===")
    for p in [template_path, payload_path, output_path, renderer_path]:
        print(f"{p.name}: {'OK' if p.exists() else 'MISSING'}")

    template_placeholders = (
        extract_placeholders_from_docx(template_path) if template_path.exists() else []
    )
    output_placeholders = (
        extract_placeholders_from_docx(output_path) if output_path.exists() else []
    )
    renderer_placeholders = (
        extract_placeholders_from_py(renderer_path) if renderer_path.exists() else []
    )

    print("\n=== TEMPLATE PLACEHOLDERS ===")
    for x in template_placeholders:
        print(x)

    print("\n=== RENDERER PLACEHOLDERS ===")
    for x in renderer_placeholders:
        print(x)

    print("\n=== PLACEHOLDERS IN TEMPLATE BUT NOT IN RENDERER ===")
    missing_in_renderer = sorted(
        set(template_placeholders) - set(renderer_placeholders)
    )
    for x in missing_in_renderer:
        print(x)
    if not missing_in_renderer:
        print("NONE")

    print("\n=== PLACEHOLDERS STILL UNRESOLVED IN OUTPUT DOCX ===")
    for x in output_placeholders:
        print(x)
    if not output_placeholders:
        print("NONE")

    if output_path.exists():
        print("\n=== SUSPICIOUS OUTPUT PATTERNS ===")
        suspicious = extract_suspicious_from_docx(output_path)
        for k, v in suspicious.items():
            print(f"{k} -> {v}")

    if payload_path.exists():
        payload = load_json(payload_path)
        print("\n=== PAYLOAD CHECKS ===")
        checks = {
            "document_meta.client_name": safe_get(payload, "document_meta.client_name"),
            "document_meta.tower_code": safe_get(payload, "document_meta.tower_code"),
            "document_meta.tower_name": safe_get(payload, "document_meta.tower_name"),
            "executive_summary.summary_body": safe_get(
                payload, "executive_summary.summary_body"
            ),
            "executive_summary.message_strength": safe_get(
                payload, "executive_summary.message_strength"
            ),
            "executive_summary.message_gap": safe_get(
                payload, "executive_summary.message_gap"
            ),
            "executive_summary.message_bottleneck": safe_get(
                payload, "executive_summary.message_bottleneck"
            ),
            "pillar_score_profile.profile_intro": safe_get(
                payload, "pillar_score_profile.profile_intro"
            ),
            "pillar_score_profile.strongest_pillar": safe_get(
                payload, "pillar_score_profile.strongest_pillar"
            ),
            "pillar_score_profile.weakest_pillars": safe_get(
                payload, "pillar_score_profile.weakest_pillars"
            ),
            "pillar_score_profile.structural_reading": safe_get(
                payload, "pillar_score_profile.structural_reading"
            ),
            "sections.tobe_gap.introduction": safe_get(
                payload, "sections.tobe_gap.introduction"
            ),
            "sections.todo.priority_initiatives": safe_get(
                payload, "sections.todo.priority_initiatives"
            ),
            "sections.conclusion.final_assessment": safe_get(
                payload, "sections.conclusion.final_assessment"
            ),
            "sections.conclusion.executive_message": safe_get(
                payload, "sections.conclusion.executive_message"
            ),
            "sections.conclusion.priority_focus_areas": safe_get(
                payload, "sections.conclusion.priority_focus_areas"
            ),
            "sections.conclusion.closing_statement": safe_get(
                payload, "sections.conclusion.closing_statement"
            ),
        }
        for k, v in checks.items():
            if isinstance(v, list):
                print(f"{k} -> LIST(len={len(v)})")
                if v:
                    print("  first =", repr(v[0])[:300])
            else:
                print(f"{k} ->", repr(v)[:300])

        pillars = safe_get(payload, "pillar_score_profile.pillars", [])
        print("\n=== FIRST PILLAR SAMPLE ===")
        if pillars:
            first = pillars[0]
            for k, v in first.items():
                print(f"{k} ->", repr(v)[:300])
        else:
            print("NO PILLARS")

    print("\n=== SUMMARY ===")
    print("template_placeholder_count =", len(template_placeholders))
    print("renderer_placeholder_count =", len(renderer_placeholders))
    print("unresolved_output_count    =", len(output_placeholders))
    print("template_minus_renderer    =", len(missing_in_renderer))


if __name__ == "__main__":
    main()
