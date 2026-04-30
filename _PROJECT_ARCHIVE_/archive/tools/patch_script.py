from pathlib import Path

path = Path("scripts/render_commercial_report.py")
content = path.read_text(encoding="utf-8")
logic = Path("update_renderer_logic.py").read_text(encoding="utf-8")

if "process_footnotes(doc, payload.get" not in content:
    content = content.replace("def main():", f"{logic}\n\ndef main():")
    content = content.replace("doc.save(str(output_path))", "process_footnotes(doc, payload.get(\"intelligence_dossier\", {}))\n    doc.save(str(output_path))")
    path.write_text(content, encoding="utf-8")
    print("Patched.")
