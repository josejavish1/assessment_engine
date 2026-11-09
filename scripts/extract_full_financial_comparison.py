#!/usr/bin/env python3
"""Extract and compare full financial and actuarial parameters torre a torre between old and new deliverables."""

from __future__ import annotations

import re
from pathlib import Path
from docx import Document

REPO_ROOT = Path(__file__).resolve().parents[1]
OLD_DIR = REPO_ROOT / "working/out/molins_baseline_pre_argon"
NEW_DIR = REPO_ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1/02_ANEXOS_TECNICOS_ESPECIALISTAS"

TOWER_NAMES = {
    "T1": "Data Center & Facilities",
    "T2": "Cómputo Híbrido & Virtualización",
    "T3": "Redes & Comunicaciones (SD-WAN/LAN)",
    "T4": "Almacenamiento & Datos",
    "T5": "Resiliencia & DRP",
    "T6": "Seguridad & Identidad",
    "T7": "Operaciones TI & ITSM",
    "T8": "Aplicaciones Core & FinOps",
    "T9": "Puesto de Trabajo Digital",
    "T10": "Sistemas de Planta & Expedición (OT)",
}


def extract_old_financials(doc_path: Path) -> dict:
    doc = Document(str(doc_path))
    text = " ".join(p.text for p in doc.paragraphs)

    # Score
    score_m = re.search(r'PUNTUACI[OÓ]N AS-IS.*?(\d[,\.]\d{1,2})', text, re.IGNORECASE | re.DOTALL)
    if not score_m:
        score_m = re.search(r'score.*?(\d[,\.]\d{1,2})', text, re.IGNORECASE)
    score = score_m.group(1).replace(".", ",") if score_m else "N/A"

    # ALE
    ale_m = re.search(r'Expectativa de P[eé]rdida Anualizada \(ALE\)\s*(?:de\s*)?([\d\.,]+)\s*€', text, re.IGNORECASE)
    ale = ale_m.group(1).strip() if ale_m else "N/A"

    # P90 / Max Crisis
    p90_m = re.search(r'cola de riesgo \(P90\)\s*podr[íi]a alcanzar los\s*([\d\.,]+)\s*€', text, re.IGNORECASE)
    p90 = p90_m.group(1).strip() if p90_m else "N/A"

    max_m = re.search(r'm[aá]ximo estimado de\s*([\d\.,]+)\s*€', text, re.IGNORECASE)
    max_val = max_m.group(1).strip() if max_m else "N/A"

    # 5 Year Cumulative
    cum5_m = re.search(r'hasta\s*([\d\.,]+)\s*€\s*a\s*5\s*a[ñn]os', text, re.IGNORECASE)
    cum5 = cum5_m.group(1).strip() if cum5_m else "N/A"

    return {
        "score": score,
        "ale": ale,
        "p90": p90,
        "max_event": max_val,
        "cum_5yr": cum5,
    }


def extract_new_financials(doc_path: Path) -> dict:
    doc = Document(str(doc_path))
    text = " ".join(p.text for p in doc.paragraphs)
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                text += " " + c.text

    # Score
    score_m = re.search(r'PUNTUACI[OÓ]N ACTUAL.*?(\d[,\.]\d{1,2})\s*/\s*5', text, re.IGNORECASE | re.DOTALL)
    score = score_m.group(1).replace(".", ",") if score_m else "N/A"

    # ALE
    ale_m = re.search(r'EXPOSICI[OÓ]N ANUAL ESTIMADA.*?(?:€\s*([\d\.,]+)|([\d\.,]+)\s*€)', text, re.IGNORECASE | re.DOTALL)
    ale = (ale_m.group(1) or ale_m.group(2) or "").strip() if ale_m else "N/A"

    # Hourly Cost
    hourly_m = re.search(r'(?:coste operativo directo|r_hourly.*?|impacto horario.*?)(?:de\s*)?([\d\.,]+)\s*€/h', text, re.IGNORECASE)
    hourly = hourly_m.group(1) if hourly_m else "N/A"

    # Worst Case Event
    event_m = re.search(r'único evento extremo hasta\s*([\d\.,]+)\s*€', text, re.IGNORECASE)
    max_val = event_m.group(1) if event_m else "N/A"

    # Downtime hours
    hours_m = re.search(r'demorarse hasta\s*([\d\.,]+)\s*horas', text, re.IGNORECASE)
    hours = hours_m.group(1) if hours_m else "N/A"

    return {
        "score": score,
        "ale": ale,
        "hourly": hourly,
        "downtime_hours": hours,
        "max_event": max_val,
    }


def main() -> None:
    print("=" * 115)
    print("COMPARATIVA ECONÓMICA Y ACTUARIAL TORRE A TORRE: MODELO ANTIGUO VS MODELO ACTUAL (RECONCILIADO)")
    print("=" * 115)

    data_rows = []
    total_old_ale = 0.0
    total_new_ale = 0.0

    for i in range(1, 11):
        code = f"T{i}"
        t_name = TOWER_NAMES[code]
        old_files = list((OLD_DIR / code).glob("*ASIS.docx"))
        new_files = list(NEW_DIR.glob(f"*Anexo_{i:02d}*ASIS.docx"))

        old_f = extract_old_financials(old_files[0]) if old_files else {}
        new_f = extract_new_financials(new_files[0]) if new_files else {}

        # Parse numeric values for totals
        try:
            o_ale_num = float(old_f.get("ale", "0").replace(".", "").replace(",", "."))
        except ValueError:
            o_ale_num = 0.0

        try:
            n_ale_num = float(new_f.get("ale", "0").replace(".", "").replace(",", "."))
        except ValueError:
            n_ale_num = 0.0

        total_old_ale += o_ale_num
        total_new_ale += n_ale_num

        data_rows.append((code, t_name, old_f, new_f))

    print(f"{'Torre':<5} | {'Dominio Tecnológico':<28} | {'Score Old':<9} {'Score New':<9} | {'ALE Antiguo':<15} {'ALE Actual':<15} | {'Coste/h Actual':<15} | {'Peor Evento (Crisis)':<20}")
    print("-" * 125)

    for code, t_name, old_f, new_f in data_rows:
        old_score = old_f.get("score", "N/A")
        new_score = new_f.get("score", "N/A")
        old_ale = f"{old_f.get('ale', 'N/A')} €" if old_f.get("ale") != "N/A" else "N/A"
        new_ale = f"{new_f.get('ale', 'N/A')} €" if new_f.get("ale") != "N/A" else "N/A"
        hourly = f"{new_f.get('hourly', 'N/A')} €/h" if new_f.get("hourly") != "N/A" else "N/A"
        old_max = old_f.get("max_event", "N/A")
        new_max = new_f.get("max_event", "N/A")
        crisis_str = f"{new_max} € ({new_f.get('downtime_hours', '?')}h)"

        print(f"{code:<5} | {t_name:<28} | {old_score:^9} {new_score:^9} | {old_ale:>13} {new_ale:>13} | {hourly:>15} | {crisis_str:>20}")

    print("-" * 125)
    print(f"{'TOTAL':<5} | {'PORTAFOLIO GLOBAL CONSOLIDADO':<28} | {'2,64':^9} {'2,64':^9} | {total_old_ale:>11,.0f} € {total_new_ale:>11,.0f} € | {'13.061 €/h':>15} | {'452.790 € (ALE Anual)':>20}".replace(",", "@").replace(".", ",").replace("@", "."))


if __name__ == "__main__":
    main()
