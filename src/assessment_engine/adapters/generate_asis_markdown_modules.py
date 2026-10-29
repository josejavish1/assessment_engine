import logging
logger = logging.getLogger(__name__)
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.localization import (
    format_number,
    get_localized_list,
    resolve_base_locale,
    t,
)


def clean_client_name(client_name: str) -> str:
    """Cleans a raw client name (which might be a slug or directory name) for reporting.

    Removes version tags (e.g. _v3, _v2, -v4), replaces underscores/hyphens with spaces,
    strips trailing whitespace, and ensures Proper Noun Title Case capitalization.
    """
    if not client_name:
        return "Cliente"
    import re
    # Remove version endings like _v3, _V2, -v4, etc.
    cleaned = re.sub(r'[_-][vV]\d+\b', '', client_name)
    # Replace underscores/hyphens with spaces
    cleaned = cleaned.replace('_', ' ').replace('-', ' ')
    cleaned = cleaned.strip()
    
    # Elite Capitalization: Ensure it is a Proper Noun (Title Case)
    # If the cleaned string is all lowercase, convert it to Title Case (e.g., 'cliente' -> 'Cliente')
    # If it has uppercase, preserve the client's custom branding (e.g., 'CLIENTE' stays 'CLIENTE')
    if cleaned.islower():
        return cleaned.title()
    return cleaned


def _load_asis_annex_catalogs() -> dict[str, Any]:
    from assessment_engine.infrastructure.runtime_paths import ROOT
    path = ROOT / "engine_config/locales_asis_annex.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


_ASIS_ANNEX_DATA = _load_asis_annex_catalogs()
CAPABILITY_KEYWORD_MAPS: dict[str, Any] = _ASIS_ANNEX_DATA.get("capability_keyword_maps", {})
HIGH_MATURITY_CATALOG: dict[str, Any] = _ASIS_ANNEX_DATA.get("high_maturity_catalog", {})
BALANCED_MATURITY_CATALOG: dict[str, Any] = _ASIS_ANNEX_DATA.get("balanced_maturity_catalog", {})
LOW_MATURITY_CATALOG: dict[str, Any] = _ASIS_ANNEX_DATA.get("low_maturity_catalog", {})


def _clean_cap_name(cap_name: str, doc_lang: str) -> str:
    """Clean and translate capability name to canonical label if configured."""
    if not cap_name:
        return ""
    from assessment_engine.infrastructure.localization import resolve_base_locale
    if resolve_base_locale(doc_lang) != "es":
        return cap_name
    keyword_map = CAPABILITY_KEYWORD_MAPS.get("es", [])
    c_lower = cap_name.lower()
    for keywords, label in keyword_map:
        if any(kw in c_lower for kw in keywords):
            return label
    return cap_name


def _get_high_maturity_prose(doc_lang: str, stable_caps: list[str]) -> tuple[str, str, str, str, str, str]:
    """Return labels and paragraphs for high maturity posture."""
    from assessment_engine.infrastructure.localization import resolve_base_locale
    spec = HIGH_MATURITY_CATALOG.get(resolve_base_locale(doc_lang), HIGH_MATURITY_CATALOG["en"])
    labels = spec["labels"]
    caps_str = ", ".join(stable_caps[:3])
    p1 = spec["p1_caps"].format(caps=caps_str) if stable_caps else spec["p1_fallback"]
    return labels[0], p1, labels[1], spec["p2"], labels[2], spec["p3"]


def _get_balanced_maturity_prose(doc_lang: str, v_idx: int, stable_caps: list[str], gaps_caps: list[str], gaps_str_joined: str, risks_str_joined: str, worst_cap: str) -> tuple[str, str, str, str, str, str]:
    """Return labels and paragraphs for balanced maturity posture."""
    from assessment_engine.infrastructure.localization import resolve_base_locale
    spec = BALANCED_MATURITY_CATALOG.get(resolve_base_locale(doc_lang), BALANCED_MATURITY_CATALOG["en"])
    labels = spec["labels"]
    var_list = spec["variants"]
    chosen_var = var_list[v_idx % len(var_list)]
    caps_str = ", ".join(stable_caps[:3])
    gaps_str = ", ".join(gaps_caps[:3])
    p1 = chosen_var["p1_caps"].format(caps=caps_str) if stable_caps else chosen_var["p1_fallback"]
    p2 = chosen_var["p2"].format(gaps_caps=gaps_str, gaps_str_joined=gaps_str_joined, risks_str_joined=risks_str_joined)
    p3 = chosen_var["p3"].format(worst_cap=worst_cap)
    return labels[0], p1, labels[1], p2, labels[2], p3


def _get_low_maturity_prose(doc_lang: str, v_idx: int, gaps_caps: list[str], gaps_str_joined: str, risks_str_joined: str, worst_cap: str) -> tuple[str, str, str, str, str, str]:
    """Return labels and paragraphs for critical or low maturity posture."""
    from assessment_engine.infrastructure.localization import resolve_base_locale
    spec = LOW_MATURITY_CATALOG.get(resolve_base_locale(doc_lang), LOW_MATURITY_CATALOG["en"])
    labels = spec["labels"]
    caps_str = ", ".join(gaps_caps[:3])
    p1 = spec["p1_caps"].format(caps=caps_str) if gaps_caps else spec["p1_fallback"]
    p2 = spec["p2"].format(gaps_str_joined=gaps_str_joined, risks_str_joined=risks_str_joined)
    p3 = spec["p3"].format(worst_cap=worst_cap)
    return labels[0], p1, labels[1], p2, labels[2], p3


def derive_pillar_justification(p: dict, idx: int, doc_lang: str) -> str:
    """Derive pillar justification according to technical specification."""
    from assessment_engine.domain.maturity_band import (
        ANNEX_MATURITY_BANDS,
        resolve_maturity_band,
    )
    from assessment_engine.infrastructure.localization import format_number

    p_score = float(p.get("score", 3.0))
    band = resolve_maturity_band(
        p_score, ANNEX_MATURITY_BANDS, locale=doc_lang
    )["label"]
    formatted_score = format_number(p_score, locale=doc_lang, decimals=2)
    p_name = p.get("pilar_name", "Pilar")

    findings = p.get("health_check_asis", [])
    if not findings:
        hdr_kpis = t("asis_header_kpis_status", locale=doc_lang)
        hdr_gaps = t("asis_header_gaps_consequences", locale=doc_lang)
        hdr_just = t("asis_header_score_justification", locale=doc_lang)
        empty_kpis = t("asis_pillar_empty_kpis", locale=doc_lang, band=band, formatted_score=formatted_score)
        empty_gaps = t("asis_pillar_empty_gaps", locale=doc_lang)
        empty_just = t("asis_pillar_empty_justification", locale=doc_lang)
        return (
            f"• **{hdr_kpis}**\n• {empty_kpis}\n"
            f"• **{hdr_gaps}**\n• {empty_gaps}\n"
            f"• **{hdr_just} ({formatted_score})**\n• {empty_just}"
        )

    # Sort findings by vulnerability_level (descending) or fair_ale_score (descending)
    def get_ale(f):
        try:
            return float(f.get("fair_ale_score", 0.0) or 0.0)
        except Exception:
            return 0.0
    def get_vuln(f):
        try:
            return int(f.get("vulnerability_level", 3) or 3)
        except Exception:
            return 3
            
    sorted_findings = sorted(findings, key=lambda x: (get_vuln(x), get_ale(x)), reverse=True)
    
    gaps_findings = [f for f in sorted_findings if get_vuln(f) >= 4]
    if not gaps_findings:
        gaps_findings = sorted_findings[:1]
        
    stable_findings = [f for f in sorted_findings if f not in gaps_findings]
    
    def clean_cap_name(name):
        return _clean_cap_name(name, doc_lang)

    gaps_caps = [clean_cap_name(f.get("target_state", f.get("capability", ""))) for f in gaps_findings if f.get("target_state", f.get("capability"))]
    stable_caps = [clean_cap_name(f.get("target_state", f.get("capability", ""))) for f in stable_findings if f.get("target_state", f.get("capability"))]
    
    gaps_caps = [c for c in gaps_caps if c]
    stable_caps = [c for c in stable_caps if c]

    # Deterministic variation index based on index
    v_idx = idx % 3
    
    # 2. Brechas y Consecuencias Operativas
    main_gaps = []
    main_risks = []
    for f in gaps_findings[:2]:
        fd = (f.get("risk_observed", f.get("finding", "")) or "").strip()
        br = (f.get("impact", f.get("business_risk", "")) or "").strip()
        from assessment_engine.infrastructure.localization import resolve_base_locale
        target_is_spanish = resolve_base_locale(doc_lang).startswith("es")
        if fd:
            if target_is_spanish and ("the" in fd.lower() or "is" in fd.lower() or "reflects" in fd.lower()):
                desc_map = _ASIS_ANNEX_DATA.get("default_finding_descriptions", {}).get("es", {})
                if "lifecycle" in fd.lower() or "patch" in fd.lower():
                    fd = desc_map.get("lifecycle", "")
                elif "configur" in fd.lower() or "standar" in fd.lower():
                    fd = desc_map.get("virtualization", "")
                elif "availability" in fd.lower() or "high availability" in fd.lower():
                    fd = desc_map.get("availability", "")
                else:
                    fd = desc_map.get("fallback", "")
            else:
                # Lowercase the first letter of fd if it was parsed as a separate sentence and not an acronym
                if fd and fd[0].isupper() and not (len(fd) >= 2 and fd[:2].isupper()):
                    fd = fd[0].lower() + fd[1:]
            fd_sent = fd.rstrip(".")
            main_gaps.append(fd_sent)
            
        if br:
            if target_is_spanish and ("increase" in br.lower() or "higher" in br.lower() or "risk" in br.lower() or "result" in br.lower()):
                risk_fallbacks = _ASIS_ANNEX_DATA.get("risk_fallback_strings", {}).get("es", {})
                if "security" in br.lower() or "vulnerab" in br.lower():
                    br = risk_fallbacks.get("surface", "an expanded attack surface and prolonged exposure to critical vulnerabilities")
                elif "cost" in br.lower() or "tco" in br.lower():
                    br = risk_fallbacks.get("tco", "an increase in total cost of ownership (TCO) from managing heterogeneous technologies")
                else:
                    br = risk_fallbacks.get("mttr", "increased mean time to resolution (MTTR) and operational toil on engineering teams")
            else:
                if br and br[0].isupper() and not (len(br) >= 2 and br[:2].isupper()):
                    br = br[0].lower() + br[1:]
            br_sent = br.rstrip(".")
            main_risks.append(br_sent)

    loc_key = resolve_base_locale(doc_lang)
    default_gaps_catalog = _ASIS_ANNEX_DATA.get("default_gaps_catalog", {})
    default_risks_catalog = _ASIS_ANNEX_DATA.get("default_risks_catalog", {})
    default_worst_cap_catalog = _ASIS_ANNEX_DATA.get("default_worst_cap_catalog", {})

    if not main_gaps:
        main_gaps = default_gaps_catalog.get(loc_key, default_gaps_catalog.get("en", []))
    if not main_risks:
        main_risks = default_risks_catalog.get(loc_key, default_risks_catalog.get("en", []))

    conjunction = " y " if target_is_spanish else " and "
    gaps_str_joined = conjunction.join(main_gaps)
    risks_str_joined = conjunction.join(main_risks)

    worst_cap = gaps_caps[0] if gaps_caps else default_worst_cap_catalog.get(loc_key, default_worst_cap_catalog.get("en", "critical capabilities"))

    p_score = float(p.get("score", 3.0))

    if p_score >= 4.20:
        label_1, p1_text, label_2, p2_text, label_3, p3_text = _get_high_maturity_prose(doc_lang, stable_caps)
    elif p_score >= 2.60:
        label_1, p1_text, label_2, p2_text, label_3, p3_text = _get_balanced_maturity_prose(
            doc_lang, v_idx, stable_caps, gaps_caps, gaps_str_joined, risks_str_joined, worst_cap
        )
    else:
        label_1, p1_text, label_2, p2_text, label_3, p3_text = _get_low_maturity_prose(
            doc_lang, v_idx, gaps_caps, gaps_str_joined, risks_str_joined, worst_cap
        )

    return f"**{label_1}:** {p1_text}\n**{label_2}:** {p2_text}\n**{label_3}:** {p3_text}"


def sanitize_semantic_prose(text: str, doc_lang: str) -> str:
    """Standardizes technical descriptions and applies declarative style and vocabulary substitutions."""
    if not text:
        return text

    t = str(text).strip()
    lang = str(doc_lang).lower()

    # Apply declarative vocabulary substitutions for standard compliance
    from assessment_engine.infrastructure.localization import (
        apply_vocabulary_substitutions,
    )

    t = apply_vocabulary_substitutions(t, locale=lang)

    from assessment_engine.infrastructure.localization import resolve_base_locale
    sub_rules = _ASIS_ANNEX_DATA.get("linguistic_substitution_rules", {}).get(resolve_base_locale(lang), {})
    for old, new in sub_rules.items():
        if old in t.lower():
            t = t.replace(old, new)
    return t


def resolve_client_currency_context(
    client_id: str, tower_dir: Path | None = None
) -> tuple[str, float]:
    """Dynamically resolves (currency_symbol, exchange_rate) from profiles, never by language guessing."""
    currency = ""
    rate_mult = 1.0

    paths_to_check: list[Path] = []
    if tower_dir:
        paths_to_check.append(tower_dir / "custom_risk_profile.json")
    paths_to_check.append(Path(f"working/{client_id}/custom_risk_profile.json"))
    for t_code in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]:
        paths_to_check.append(Path(f"working/{client_id}/{t_code}/custom_risk_profile.json"))

    for p in paths_to_check:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8-sig"))
                sym = data.get("currency_symbol")
                code = data.get("currency_code")
                if sym:
                    currency = sym
                elif code:
                    currency = {"USD": "$", "EUR": "€", "GBP": "£", "BRL": "R$", "MXN": "$", "CHF": "CHF", "JPY": "¥"}.get(code.upper(), code)
                rate_mult = float(data.get("exchange_rate", rate_mult))
                if currency:
                    break
            except Exception:
                pass

    if not currency:
        intel_file = Path(f"working/{client_id}/client_intelligence.json")
        if intel_file.exists():
            try:
                data = json.loads(intel_file.read_text(encoding="utf-8-sig"))
                curr = data.get("financial", {}).get("currency") or data.get("currency")
                if curr:
                    currency = {"USD": "$", "EUR": "€", "GBP": "£", "BRL": "R$", "MXN": "$", "CHF": "CHF", "JPY": "¥"}.get(curr.upper(), curr)
            except Exception:
                pass

    if not currency:
        currency = "€"

    return currency, rate_mult


def sanitize_and_unify_metrics(text: str, exact_score: float, exact_band: str, total_fair_ale: float, doc_lang: str, total_p90: float = 0.0, total_max: float = 0.0) -> str:
    """Sanitize and unify metrics according to technical specification."""
    import re
    import os
    if not text:
        return text

    client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
    currency, rate_mult = resolve_client_currency_context(client_id)

    from assessment_engine.infrastructure.config_loader import resolve_localized_vocabulary
    vocab = resolve_localized_vocabulary(doc_lang)

    # Scale computed metrics by exchange rate in origin for presentation clarity
    total_fair_ale = total_fair_ale * rate_mult
    total_p90 = total_p90 * rate_mult
    total_max = total_max * rate_mult

    # 1. Format of TRUE ALE (with 2 decimals as requested)
    from assessment_engine.infrastructure.localization import format_number

    formatted_ale = format_number(total_fair_ale, locale=doc_lang, decimals=2)
    true_ale_str = f"{formatted_ale} {currency}"

    formatted_p90 = format_number(total_p90, locale=doc_lang, decimals=0)
    formatted_max = format_number(total_max, locale=doc_lang, decimals=0)
    formatted_score = format_number(exact_score, locale=doc_lang, decimals=2)
    
    # Clean up any mention of currency values (like 35.560.000, 32,120,000, 2.580.552,94, etc.)
    # Robust money_pattern preventing partial matches and ensuring full match of floats/thousands sep
    money_pattern = r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?\s*[€$]"
    text = re.sub(money_pattern, true_ale_str, text)
    
    # Also look for phrases like "35,56 millones de euros" or "32,12 millones" and replace them
    millones_pattern = r"\b\d+[,.]\d+\s*(?:millones|millones de euros|million)\b"
    if "millon" in text.lower() or "million" in text.lower():
        text = re.sub(millones_pattern, f"{formatted_ale} {currency}", text)
        
    # 3. Clean up any mention of global score/band
    score_pattern = r"\b\d+[,.]\d+\s*sobre\s*5(?:[.,]0+)?\b"
    text = re.sub(score_pattern, f"{formatted_score} sobre 5,00", text)
    
    # Match band patterns inside quotes or parentheses and align with the true band
    band_pattern = r"Nivel\s*\d+\s*\([^)]+\)"
    true_band_str = f"Nivel {exact_score:.1f}".replace(".", ",") + f" ({exact_band})"
    text = re.sub(band_pattern, true_band_str, text)
    
    # 6. Inject Cost of Delay (Gap A)
    legacy_keywords = _ASIS_ANNEX_DATA.get("legacy_cleaning_keywords", [])
    has_ale_keyword = "ALE" in text or "Loss Exposure" in text or any(k in text.lower() for k in legacy_keywords[:3])
    has_inaction_keyword = "inaction" in text.lower() or any(k in text.lower() for k in legacy_keywords[1:3])
    if has_ale_keyword and has_inaction_keyword:
        if "demora" not in text.lower() and "delay" not in text.lower():
            text += t("cost_of_delay_text", locale=doc_lang, formatted_ale=formatted_ale, currency=currency)

    # 7. Pedagogical & diplomatic rewrite of executive summary maturity and ALE paragraph (first-time reader alignment)
    has_maturity = any(k in text.lower() for k in ["maturity", "rating"]) or any(k in text.lower() for k in legacy_keywords[5:])
    has_exposure = any(k in text.lower() for k in ["ale", "fair", "exposure"]) or any(k in text.lower() for k in legacy_keywords[3:5])
    if has_maturity and has_exposure:
        from assessment_engine.infrastructure.localization import resolve_base_locale
        loc_base = resolve_base_locale(doc_lang)

        desc_key = "desc_band_definido"
        for k_sub, k_mapped in [
            ("init", "desc_band_inicial"),
            ("repet", "desc_band_repetible"),
            ("defin", "desc_band_definido"),
            ("manag", "desc_band_gestionado"),
            ("gestio", "desc_band_gestionado"),
            ("optim", "desc_band_optimizado"),
        ]:
            if k_sub in str(exact_band).lower():
                desc_key = k_mapped
                break

        default_desc = vocab.get(desc_key, "")
        band_qualitative_desc = vocab.get(desc_key, default_desc)

        maturity_templates = _ASIS_ANNEX_DATA.get("tower_maturity_executive_paragraph", {})
        template_str = maturity_templates.get(loc_base, maturity_templates.get("en", ""))
        new_maturity_p = template_str.format(
            formatted_score=formatted_score,
            exact_band=exact_band,
            band_qualitative_desc=band_qualitative_desc,
            true_ale_str=true_ale_str,
            formatted_p90=formatted_p90,
            currency=currency,
            formatted_max=formatted_max,
        )

        regex_patterns = _ASIS_ANNEX_DATA.get("metric_unification_regexes", [])
        for reg in regex_patterns:
            text, count = re.subn(reg, new_maturity_p, text, flags=re.IGNORECASE | re.DOTALL)
            if count > 0:
                break

    from assessment_engine.infrastructure.localization import (
        apply_vocabulary_substitutions,
    )

    text = apply_vocabulary_substitutions(text, locale=doc_lang)
    return text


def _write_module_06_matriz_riesgos_fair(modules_dir: Path, ctx: dict[str, Any]) -> None:
    """Write 06_matriz_riesgos_fair.csv module."""
    pillars = ctx.get("pillars", [])
    # SECTION MAPPING: Module 6 (Risk Register, FAIR) maps to `06_matriz_riesgos_fair.csv`.
    #
    # Exports data in the three-column format required by the blueprint specification.
    csv_risks_path = modules_dir / "06_matriz_riesgos_fair.csv"
    with open(csv_risks_path, "w", newline="", encoding="utf-8") as cf_out:
        writer = csv.writer(cf_out, delimiter=";")
        doc_lang = ctx.get("doc_lang", "en")
        writer.writerow(
            [
                t("header_evaluated_technical_capability", locale=doc_lang),
                t("header_technical_diagnosis_evidence", locale=doc_lang),
                t("header_business_risk_operational_impact", locale=doc_lang),
                "TEF",
                "LM",
                "ALE",
            ]
        )

        for pilar in pillars:
            p_name = pilar.get("pilar_name", "General")
            for hc in pilar.get("health_check_asis", []):
                #
                not_def_text = t("lbl_not_defined", locale=doc_lang)
                finding = hc.get("finding", hc.get("risk_observed", not_def_text))
                evidence = hc.get("literal_evidence", t("no_literal_evidence_provided", locale=doc_lang))
                biz_risk = hc.get("business_risk", hc.get("impact", not_def_text))

                #
                ev_header = t("header_literal_forensic_evidence", locale=doc_lang)
                finding_full = (
                    f'{finding}\n\n{ev_header}\n"{evidence}"'
                )

                tef = hc.get("threat_event_frequency", 0.0)
                lm = hc.get("loss_magnitude", 0.0)
                ale = hc.get("fair_ale_score", 0.0)

                writer.writerow(
                    [
                        f"{p_name} - {hc.get('target_state', hc.get('capability', 'Capacidad'))}",
                        finding_full,
                        biz_risk,
                        f"{tef:.1f}",
                        f"{lm:.1f}",
                        f"{ale:.0f}",
                    ]
                )

    #


def _write_module_07_conclusiones(modules_dir: Path, ctx: dict[str, Any]) -> None:
    """Write 07_conclusiones.md module."""
    vocab = ctx["vocab"]
    pillars = ctx.get("pillars", [])
    doc_lang = ctx["doc_lang"]
    industry_name = ctx.get("industry_name", "")
    annex_data = ctx.get("annex_data", {})
    tower_meta = ctx.get("tower_meta", {})
    exec_sum = ctx.get("exec_sum", {})
    snap = ctx.get("snap", {})
    exact_score = ctx["exact_score"]
    exact_band = ctx["exact_band"]
    global_fair_ale = ctx["global_fair_ale"]
    global_fair_p90 = ctx.get("global_fair_p90", 0.0)
    global_fair_max = ctx.get("global_fair_max", 0.0)
    # SECTION MAPPING: Module 7 (Conclusions and Gaps) maps to `07_conclusiones.md`.
    conc_content = []
    conc_content.append(f"# {t('annex_conclusions_title', locale=doc_lang)}\n")
    conc_content.append(f"## {t('quick_diagnosis_title', locale=doc_lang)}")
    conc_content.append(t("quick_diagnosis_intro", locale=doc_lang))

    # Structures strengths and gaps as discrete lists for rendering into a two-column table.
    strengths_list = []
    
    # Generate empirical AS-IS baseline strengths directly by sorting capabilities by vulnerability level
    empirical_caps = []
    if pillars:
        for p in pillars:
            p_name = p.get("pilar_name", "Dominio")
            for f in p.get("health_check_asis", []):
                vuln = f.get("vulnerability_level", 5)
                cap = f.get("capability", "")
                if cap:
                    empirical_caps.append((vuln, cap, p_name))
        
        # Sort by vulnerability level (lowest first = healthiest)
        empirical_caps.sort(key=lambda x: x[0])
        
        # Take the top 3 distinct capabilities to build the baseline
        seen_caps = set()
        from assessment_engine.infrastructure.localization import resolve_base_locale
        loc_base = resolve_base_locale(doc_lang)
        strength_tpls = _ASIS_ANNEX_DATA.get("strength_templates", {})
        st_cat = strength_tpls.get(loc_base, strength_tpls.get("en", {}))
        for vuln, cap, p_name in empirical_caps:
            if cap not in seen_caps:
                seen_caps.add(cap)
                tpl = st_cat["low"] if vuln <= 2 else st_cat["norm"]
                strengths_list.append(tpl.format(cap=cap, p_name=p_name))
            if len(strengths_list) >= 3:
                break

    if not strengths_list:
        fallback_tpl = strength_tpls.get(loc_base, strength_tpls["en"])["fallback"]
        strengths_list.append(fallback_tpl)

    gaps_list = []
    # We use the structural risks generated by the executive snapshot as they accurately reflect AS-IS gaps
    weaknesses = snap.get("structural_risks", [])
    if isinstance(weaknesses, str):
        gaps_list.append(weaknesses)
    elif isinstance(weaknesses, list):
        gaps_list.extend(weaknesses)
        
    # If the LLM failed to provide structural risks, we fallback to empirical critical findings
    if not gaps_list and pillars:
        for p in pillars:
            findings = p.get("health_check_asis", [])
            for f in findings:
                f_score = float(f.get("exact_score", 5.0))
                finding_desc = f.get("finding", f.get("risk_observed", ""))
                if f_score < 2.60 and finding_desc:
                    gaps_list.append(finding_desc.strip())
                    if len(gaps_list) >= 4:
                        break

    # Serializes data to a specific format required by the downstream document compilation service.
    conc_content.append("--- TABLA COMPARATIVA FORTALEZAS VS BRECHAS ---")
    conc_content.append("FORTALEZAS_CLAVE:")
    for s in strengths_list:
        conc_content.append(f"* {sanitize_semantic_prose(s, doc_lang)}")
    conc_content.append("BRECHAS_CLAVE:")
    for g in gaps_list:
        conc_content.append(f"* {sanitize_semantic_prose(g, doc_lang)}")
    conc_content.append("--- FIN TABLA --- \n")

    # Implements regulatory terminology harmonization as specified by Requirement 2.
    from assessment_engine.infrastructure.localization import resolve_base_locale
    doc_lang = tower_meta.get("language", "en").lower()
    reg_frameworks = tower_meta.get("regulatory_frameworks")
    if not reg_frameworks:
        reg_frameworks = t("applicable_regulations_default", locale=doc_lang)

    conc_content.append(
        f"## {t('annex_header_key_operational_implications', locale=doc_lang)}"
    )

    bottlenecks_cfg = _ASIS_ANNEX_DATA.get("default_structural_bottlenecks", {})
    loc_b = resolve_base_locale(doc_lang)
    default_bullets = bottlenecks_cfg.get(loc_b, bottlenecks_cfg.get("en", []))

    bottlenecks_txt = vocab.get("bottlenecks_bullet", default_bullets[0] if default_bullets else "")
    delayed_txt = vocab.get("delayed_faults_bullet", default_bullets[1] if len(default_bullets) > 1 else "")
    drift_tmpl = vocab.get("config_drift_bullet", default_bullets[2] if len(default_bullets) > 2 else "")

    conc_content.append(f"* {bottlenecks_txt}")
    conc_content.append(f"* {delayed_txt}")
    conc_content.append(f"* {drift_tmpl.format(reg_frameworks=reg_frameworks)}\n")

    conc_content.append(f"## {t('annex_header_cost_of_inaction', locale=doc_lang)}")
    msg_bottle = exec_sum.get("message_bottleneck", "")
    if msg_bottle:
        msg_bottle_clean = sanitize_and_unify_metrics(msg_bottle, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
        conc_content.append(msg_bottle_clean + "\n")

    coi = snap.get("cost_of_inaction", [])
    if isinstance(coi, str):
        coi_clean = sanitize_and_unify_metrics(coi, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
        conc_content.append(coi_clean + "\n")
    else:
        for item in coi:
            item_clean = sanitize_and_unify_metrics(item, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
            conc_content.append(f"* {item_clean}")

    with open(modules_dir / "07_conclusiones.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(conc_content).strip())



def _write_module_01_introduccion(modules_dir: Path, ctx: dict[str, Any]) -> None:
    """Write 01_introduccion.md module."""
    doc_lang = ctx["doc_lang"]
    tower_name = ctx["tower_name"]
    client_name = ctx["client_name"]
    pillars_list_md = ctx["pillars_list_md"]
    industry_name = ctx.get("industry_name", "")
    # SECTION MAPPING: Appendix B (Objective, Scope, Methodology) maps to `01_introduccion.md`.
    # The following section is designated for Appendix B to conform to the standard report structure.
    from assessment_engine.infrastructure.localization import resolve_base_locale
    intro_templates = _ASIS_ANNEX_DATA.get("chapter_01_intro_templates", {})
    intro_tpl = intro_templates.get(resolve_base_locale(doc_lang), intro_templates.get("en", ""))
    intro_content = intro_tpl.format(
        tower_name=tower_name,
        client_name=client_name,
        pillars_list_md=pillars_list_md,
        industry_name=industry_name,
    )

    with open(modules_dir / "01_introduccion.md", "w", encoding="utf-8") as f_out:
        f_out.write(intro_content.strip())

    #


def _write_module_02_resumen_ejecutivo(modules_dir: Path, ctx: dict[str, Any]) -> None:
    """Write 02_resumen_ejecutivo.md module."""
    exec_sum = ctx.get("exec_sum", {})
    snap = ctx.get("snap", {})
    exact_score = ctx["exact_score"]
    exact_band = ctx["exact_band"]
    global_fair_ale = ctx["global_fair_ale"]
    global_fair_p90 = ctx.get("global_fair_p90", 0.0)
    global_fair_max = ctx.get("global_fair_max", 0.0)
    doc_lang = ctx["doc_lang"]
    from assessment_engine.infrastructure.localization import (
        resolve_base_locale,
        t,
    )
    loc_base = resolve_base_locale(doc_lang)
    cca = ctx.get("cca", {})
    tower_dir = ctx["tower_dir"]
    pillars = ctx.get("pillars", [])
    client_name = ctx["client_name"]
    industry_name = ctx.get("industry_name", "")
    # SECTION MAPPING: Module 2 (Executive Summary) maps to `02_resumen_ejecutivo.md`.
    # Revises section titles to align with formal reporting terminology.
    #
    re_content = []
    re_content.append("# Resumen Ejecutivo\n")

    body_text = exec_sum.get("summary_body", "") if exec_sum else snap.get("bottom_line", "")
    cleaned_paragraphs = []
    if body_text:
        import re
        # Apply bilingually-sanitized and unified metrics on the entire un-split text first to avoid double regex matches
        body_text_sanitized = sanitize_and_unify_metrics(body_text, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
        
        paragraphs = [p.strip() for p in body_text_sanitized.split("\n\n") if p.strip()]
        
        split_markers = _ASIS_ANNEX_DATA.get("paragraph_split_markers", [])
        for p in paragraphs:
            # Force separation of the maturity and ALE if merged in the same paragraph
            for marker in split_markers:
                if marker in p:
                    replacement = f".\n\n{marker.lstrip('. ')}"
                    p = p.replace(marker, replacement)

            # Split again to process them as distinct paragraphs
            sub_ps = [sp.strip() for sp in p.split("\n\n") if sp.strip()]
            regex_clean_patterns = _ASIS_ANNEX_DATA.get("metric_unification_regexes", [])
            clean_score_pattern = regex_clean_patterns[1] if len(regex_clean_patterns) > 1 else r"Quantitative score.*?\.\s*"
            for sp in sub_ps:
                # Remove redundant sentence stating the quantitative score
                sp_clean = re.sub(clean_score_pattern, "", sp)
                
                # Global semicolon removal (replaced by commas or periods) to suit user preference
                sp_clean = sp_clean.replace(";", ",")

                if sp_clean:
                    cleaned_paragraphs.append(sp_clean)

    if cleaned_paragraphs:
        # Dynamic injection of Critical Technical Debt core concept as a separate paragraph
        tech_debt = cca.get("critical_technical_debt", "") if isinstance(cca, dict) else ""
        if tech_debt:
            tech_debt_clean = sanitize_and_unify_metrics(tech_debt, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
            if tech_debt_clean:
                # Remove semicolons from the tech debt paragraph too
                tech_debt_clean = tech_debt_clean.replace(";", ",")
                cleaned_paragraphs.append(tech_debt_clean)
                
        re_content.append("\n\n".join(cleaned_paragraphs) + "\n")

    # Load dynamic exchange rate and currency symbol from custom calibration if exists (FAIR-MAM)
    client_id = ctx.get("client_id") or os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
    currency, rate_mult = resolve_client_currency_context(client_id, tower_dir=tower_dir)

    # Collect and sort all health check risks from all pillars to identify the top 3
    all_risks = []
    for pilar in pillars:
        p_name = pilar.get("pilar_name", "General")
        for hc in pilar.get("health_check_asis", []):
            capability = hc.get("target_state", hc.get("capability", "Capability"))
            ale_val = float(hc.get("fair_ale_score", 0.0))
            finding = hc.get("finding", hc.get("risk_observed", t("lbl_not_defined", locale=doc_lang)))
            all_risks.append({
                "pilar_name": p_name,
                "capability": capability,
                "ale": ale_val,
                "finding": finding
            })
            
    all_risks.sort(key=lambda x: x["ale"], reverse=True)

    # Group risks by strategic mitigation initiative to prevent repetitive mapping of multiple risks to the same project
    mitigation_groups = {}
    for r in all_risks:
        cap = r['capability']
        p_name = r['pilar_name']
        
        strat_cat = _ASIS_ANNEX_DATA.get("strategic_mitigation_catalog", {}).get(loc_base, _ASIS_ANNEX_DATA.get("strategic_mitigation_catalog", {}).get("en", {}))
        if any(k in cap.lower() for k in ["automatiz", "automat", "foundation"]):
            group_key = strat_cat.get("iac", {}).get("key", "Infrastructure-as-Code (IaC) Standardization")
            base_prop = strat_cat.get("iac", {}).get("prop", "")
        elif any(k in cap.lower() for k in ["kubernetes", "container", "contenedor"]) or "container" in p_name.lower():
            group_key = strat_cat.get("k8s", {}).get("key", "Unified Container Orchestration")
            base_prop = strat_cat.get("k8s", {}).get("prop", "")
        elif any(k in cap.lower() for k in ["slo", "observab"]) or "operations" in p_name.lower():
            group_key = strat_cat.get("obs", {}).get("key", "Predictive Observability and SRE")
            base_prop = strat_cat.get("obs", {}).get("prop", "")
        elif "cloud" in p_name.lower():
            group_key = strat_cat.get("cloud", {}).get("key", "Landing Zones and Hybrid Cloud Architecture")
            base_prop = strat_cat.get("cloud", {}).get("prop", "")
        else:
            cn_cat = strat_cat.get("fallback", {})
            if "automation" in p_name.lower() or "provisioning" in p_name.lower():
                clean_pilar_name = cn_cat.get("automation", "Platform Automation")
            elif "hybrid" in p_name.lower() or "compute" in p_name.lower():
                clean_pilar_name = cn_cat.get("compute", "Hybrid Compute")
            else:
                clean_pilar_name = p_name

            if clean_pilar_name in (cn_cat.get("automation"), cn_cat.get("compute")):
                group_key = clean_pilar_name
            else:
                group_key = cn_cat.get("prefix", "Optimization of {name}").format(name=clean_pilar_name)
            base_prop = cn_cat.get("base_prop", "Modernize {p_name}").format(p_name=p_name)
            
        if group_key not in mitigation_groups:
            mitigation_groups[group_key] = {"ale_sum": 0.0, "prop": base_prop}
        mitigation_groups[group_key]["ale_sum"] += r["ale"]

    # Sort grouped mitigations by ALE sum descending
    sorted_groups = sorted(mitigation_groups.items(), key=lambda x: x[1]["ale_sum"], reverse=True)

    # 4. Strategic Value Enablement and Mitigation Pillars (Streamlined Section 1.2 + 1.3 for 1-page fit)
    re_content.append(f"## {t('annex_heading_mitigation_pillars', locale=doc_lang)}")

    if sorted_groups:
        conclusion_cfg = _ASIS_ANNEX_DATA.get("conclusion_tobe_templates", {})
        intro_str = conclusion_cfg.get(loc_base, conclusion_cfg.get("en", {})).get("intro", "").format(
            client_name=client_name, industry_name=industry_name
        )
        re_content.append(intro_str)
        
        top_3_sum = 0.0
        for i, (g_key, g_data) in enumerate(sorted_groups[:3], 1):
            g_ale = g_data["ale_sum"]
            top_3_sum += g_ale
            pct = (g_ale / global_fair_ale * 100) if global_fair_ale > 0 else 0.0
            
            # Scale dynamically by the exchange rate in time of presentation (FAIR-MAM)
            scaled_g_ale = g_ale * rate_mult
            formatted_g_ale = format_number(
                scaled_g_ale, locale=doc_lang, decimals=2
            )

            tail_tpl = _ASIS_ANNEX_DATA.get("conclusion_tobe_templates", {}).get(loc_base, {}).get("value_prop_tail", "")
            tail_str = tail_tpl.format(formatted_g_ale=formatted_g_ale, currency=currency, pct=pct)
            value_proposition = f"{g_data['prop']} {tail_str}".strip()
            re_content.append(f"* **{g_key}:** {value_proposition}")
        re_content.append("")

    top_3_pct = (top_3_sum / global_fair_ale * 100) if global_fair_ale > 0 else 0.0

    cta_catalog = _ASIS_ANNEX_DATA.get("cta_catalog", {})
    cta_data = cta_catalog.get(loc_base, cta_catalog.get("en", {}))
    if top_3_pct >= 80.0:
        mitigation_phrase = cta_data.get("p80", "")
    elif top_3_pct >= 65.0:
        mitigation_phrase = cta_data.get("p65", "")
    elif top_3_pct >= 40.0:
        mitigation_phrase = cta_data.get("p40", "")
    else:
        mitigation_phrase = cta_data.get("default", "")
    c_to_action = cta_data.get("action", "").format(phrase=mitigation_phrase)

    re_content.append(c_to_action)

    # 5. Escribir archivo de resumen ejecutivo consolidador
    with open(modules_dir / "02_resumen_ejecutivo.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(re_content).strip())

    #


def _write_modules_03_04_05(modules_dir: Path, ctx: dict[str, Any]) -> None:
    """Write 03_descripcion_plataforma.md, 04_matriz_madurez.csv, and 05_transversal.md."""
    pillars = ctx.get("pillars", [])
    doc_lang = ctx["doc_lang"]
    cca = ctx.get("cca", {})
    exact_score = ctx["exact_score"]
    exact_band = ctx["exact_band"]
    global_fair_ale = ctx["global_fair_ale"]
    global_fair_p90 = ctx.get("global_fair_p90", 0.0)
    global_fair_max = ctx.get("global_fair_max", 0.0)
    # SECTION MAPPING: Module 3 (Platform Description) maps to `03_descripcion_plataforma.md`.
    desc_parts = []
    if pillars:
        for p in pillars:
            desc_p = p.get("asis_architecture_description", p.get("asis_description", "")).strip()
            if desc_p and desc_p not in desc_parts:
                desc_parts.append(desc_p)

    desc_tpl = _ASIS_ANNEX_DATA.get("chapter_04_templates", {}).get(resolve_base_locale(doc_lang), _ASIS_ANNEX_DATA.get("chapter_04_templates", {}).get("en", {}))
    if desc_parts:
        desc_raw = "\n\n".join(desc_parts)
    else:
        desc_raw = desc_tpl.get("fallback", "")

    desc_clean = sanitize_semantic_prose(desc_raw, doc_lang)
    desc_content = f"{desc_tpl.get('title', '')}\n{desc_tpl.get('intro', '')}{desc_clean}\n"
    with open(
        modules_dir / "03_descripcion_plataforma.md", "w", encoding="utf-8"
    ) as f_out:
        f_out.write(desc_content.strip())

    #
    # SECTION MAPPING: Module 4 (Maturity Matrix) maps to `04_matriz_madurez.csv`.
    #
    csv_mat_path = modules_dir / "04_matriz_madurez.csv"

    with open(csv_mat_path, "w", newline="", encoding="utf-8") as cf_out:
        writer = csv.writer(cf_out, delimiter=";")
        writer.writerow(get_localized_list("justification_table_headers", locale=doc_lang))

        for s_idx, p in enumerate(pillars):
            p_name = p.get("pilar_name", "Pilar")
            
            # We always generate the highly detailed, localized, structured justification dynamically
            justification = derive_pillar_justification(p, s_idx, doc_lang)

            writer.writerow([p_name, f"{p.get('score', 0.0):.2f}", justification])

    #
    # SECTION MAPPING: Module 5 (Cross-Cutting Platform Analysis) maps to `05_transversal.md`.
    #
    trans_tpl = _ASIS_ANNEX_DATA.get("transversal_analysis_templates", {}).get(resolve_base_locale(doc_lang), _ASIS_ANNEX_DATA.get("transversal_analysis_templates", {}).get("en", {}))
    trans_content = []
    trans_content.append(trans_tpl.get("title", ""))

    if cca:
        trans_content.append(trans_tpl.get("tech_debt_heading", ""))
        tech_debt_raw = cca.get("critical_technical_debt", t("lbl_not_defined", locale=doc_lang))
        tech_debt_clean = sanitize_and_unify_metrics(tech_debt_raw, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
        
        # Intercept and refactor the aggressive/rigid default LLM technical debt text into constructive, C-level bullet points
        if "virtualiz" in tech_debt_clean.lower() or "insostenib" in tech_debt_clean.lower() or "fragmentation" in tech_debt_clean.lower():
            tech_debt_clean = trans_tpl.get("refactored_tech_debt", tech_debt_clean)
            
        trans_content.append(tech_debt_clean + "\n")

        trans_content.append(trans_tpl.get("patterns_heading", ""))
        def_patterns = cca.get("common_deficiency_patterns", [])
        if isinstance(def_patterns, str):
            def_patterns_clean = sanitize_and_unify_metrics(def_patterns, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
            trans_content.append(def_patterns_clean + "\n")
        else:
            for pat in def_patterns:
                pat_clean = sanitize_and_unify_metrics(pat, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
                trans_content.append(f"* {pat_clean}")
            trans_content.append("")

    with open(modules_dir / "05_transversal.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(trans_content).strip())

    #


def generate_modules(payload_path: str):
    """Generates a structured set of AS-IS assessment report modules from a JSON payload.

    This function processes a primary JSON payload, enriching it with data from
    supplementary files such as approved annexes, client intelligence reports,
    tower definitions, and localization vocabularies. The aggregated data is then
    serialized into a series of Markdown (.md) and CSV (.csv) files that
    constitute a complete technical AS-IS report.

    All output files are written to an `asis_modules` subdirectory, which is
    created within the same directory as the input `payload_path`.

    Args:
        payload_path (str): The file system path to the main JSON payload file.

    Returns:
        None. The function's primary effect is writing files to the file system.

    Raises:
        FileNotFoundError: If the file specified by `payload_path` does not exist.
        json.JSONDecodeError: If the main payload file contains malformed JSON.
        OSError: If an error occurs during directory creation or file I/O, such as
            insufficient write permissions.
    """
    payload_path_obj = Path(payload_path)
    tower_dir = payload_path_obj.parent
    modules_dir = tower_dir / "asis_modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"📂 Starting Docs-as-Code modules extraction in: {modules_dir}")

    # Loads technical payloads from the blueprint configuration, which serves as the primary data source.
    with open(payload_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    tower_meta = data.get("document_meta", {})
    doc_lang = tower_meta.get("language", "en").lower()

    # Load scoring output to get exact score and band deterministically
    scoring_file = tower_dir / "scoring_output.json"
    exact_score = 3.0
    exact_band = t("band_defined", locale=doc_lang)
    if scoring_file.exists():
        try:
            with open(scoring_file, "r", encoding="utf-8-sig") as sf:
                score_data = json.load(sf)
            exact_score = float(score_data.get("tower_score_exact", score_data.get("score_exact", 3.0)))
            exact_band = score_data.get("maturity_band_from_exact", {}).get("label", score_data.get("current_maturity_band", exact_band))
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Handled exception: {ex}")

    global_fair_ale = data.get("total_fair_ale", 0.0)

    from assessment_engine.infrastructure.config_loader import (
        resolve_localized_vocabulary,
    )

    vocab = resolve_localized_vocabulary(doc_lang)

    tower_name = tower_meta.get("tower_name", "Desconocida")
    tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
    client_name = clean_client_name(tower_meta.get("client_name", "Cliente"))

    # Load client_intelligence.json for industry_name
    intel_data = {}
    client_intel_file = tower_dir.parent / "client_intelligence.json"
    if client_intel_file.exists():
        try:
            with open(client_intel_file, "r", encoding="utf-8-sig") as cif:
                intel_data = json.load(cif)
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Handled exception: {ex}")

    profile_sec = intel_data.get("profile", {}) if isinstance(intel_data, dict) else {}
    raw_industry = profile_sec.get("industry", profile_sec.get("industry_type_es", "Standard Industry"))
    from assessment_engine.infrastructure.localization import resolve_base_locale
    industry_mappings = _ASIS_ANNEX_DATA.get("industry_display_names", {})
    industry_name = industry_mappings.get(resolve_base_locale(doc_lang), {}).get(raw_industry, raw_industry)

    pillars = data.get("pillars_analysis", [])
    
    global_fair_p90 = 0.0
    global_fair_max = 0.0
    try:
        for p in pillars:
            for hc in p.get("health_check_asis", []):
                global_fair_p90 += hc.get("fair_p90_score", 0.0) or 0.0
                global_fair_max += hc.get("fair_max_score", 0.0) or 0.0
    except (OSError, ValueError, KeyError, AttributeError) as ex:

        logger.debug(f"[Fallback] Handled exception: {ex}")

    snap = data.get("executive_snapshot", {})
    cca = data.get("cross_capabilities_analysis", {})

    # Loads the `approved_annex` data if present, which contains curated and validated findings.
    annex_path = tower_dir / f"approved_annex_{tower_id.lower()}.template_payload.json"
    annex_data = {}
    if annex_path.exists():
        with open(annex_path, "r", encoding="utf-8-sig") as af:
            try:
                annex_data = json.load(af)
            except (OSError, ValueError, KeyError, AttributeError) as ex:

                logger.debug(f"[Fallback] Handled exception: {ex}")

    exec_sum = annex_data.get("executive_summary", {})
    score_profile = annex_data.get("pillar_score_profile", {})

    # Dynamically loads the tower definition and integrates KPIs into a narrative paragraph, avoiding bulleted lists to maintain prose flow.
    pillars_list_md = ""
    tower_def_path = (
        Path("engine_config/towers")
        / tower_id
        / f"tower_definition_{tower_id.lower()}.json"
    )
    if not tower_def_path.exists():
        # Provides a fallback for case-insensitive key matching to handle variations in source data.
        tower_def_path = (
            Path("engine_config/towers")
            / tower_id
            / f"tower_definition_{tower_id}.json"
        )

    if tower_def_path.exists():
        with open(tower_def_path, "r", encoding="utf-8-sig") as tdf:
            try:
                t_def = json.load(tdf)
                for p in t_def.get("pillars", []):
                    p_name = p.get("pillar_name", "Pilar")
                    p_weight = p.get("weight_pct", "0")

                    # Extracts Key Performance Indicator (KPI) names for integration into narrative text.
                    kpi_names = []
                    for kpi in p.get("kpis", []):
                        k_name = kpi.get("kpi_name", "KPI").strip()
                        # Normalizes text to lowercase while preserving the case of known acronyms to maintain technical accuracy.
                        if k_name and not k_name.isupper() and len(k_name) > 4:
                            k_name = k_name[0].lower() + k_name[1:]
                        kpi_names.append(k_name)

                    # Formats the KPI list into a grammatically standard series (e.g., 'a, b, and c') for prose integration.
                    conjunction = t("conjunction_and", locale=doc_lang)
                    if len(kpi_names) > 1:
                        kpi_str = ", ".join(kpi_names[:-1]) + conjunction + kpi_names[-1]
                    elif kpi_names:
                        kpi_str = kpi_names[0]
                    else:
                        kpi_str = "the operational pillar capabilities"

                    bullet_cfg = _ASIS_ANNEX_DATA.get("pillar_bullet_template", {}).get(resolve_base_locale(doc_lang), _ASIS_ANNEX_DATA.get("pillar_bullet_template", {}).get("en", {}))
                    w_tpl = bullet_cfg.get("weighted", "* **{p_name} (Weight: {p_weight}%)**: Evaluates operational maturity and technical baselines across key capabilities such as {kpi_str}.\n")
                    pillars_list_md += w_tpl.format(p_name=p_name, p_weight=p_weight, kpi_str=kpi_str)
            except Exception as e:
                logger.info(f"⚠️ Error parsing tower definition: {e}")

    if not pillars_list_md:
        bullet_cfg = _ASIS_ANNEX_DATA.get("pillar_bullet_template", {}).get(resolve_base_locale(doc_lang), _ASIS_ANNEX_DATA.get("pillar_bullet_template", {}).get("en", {}))
        std_tpl = bullet_cfg.get("standard", "* **{p_name}**: Technical assessment and operational gap analysis across the tower perimeter.\n")
        for p in pillars:
            p_name = p.get("pilar_name", "Pilar")
            pillars_list_md += std_tpl.format(p_name=p_name)

    #
    gen_ctx: dict[str, Any] = {
        "vocab": vocab,
        "pillars": pillars,
        "doc_lang": doc_lang,
        "tower_name": tower_name,
        "tower_id": tower_id,
        "client_name": client_name,
        "industry_name": industry_name,
        "pillars_list_md": pillars_list_md,
        "annex_data": annex_data,
        "tower_meta": tower_meta,
        "exec_sum": exec_sum,
        "snap": snap,
        "cca": cca,
        "tower_dir": tower_dir,
        "exact_score": exact_score,
        "exact_band": exact_band,
        "global_fair_ale": global_fair_ale,
        "global_fair_p90": global_fair_p90,
        "global_fair_max": global_fair_max,
    }
    _write_module_01_introduccion(modules_dir, gen_ctx)
    _write_module_02_resumen_ejecutivo(modules_dir, gen_ctx)
    _write_modules_03_04_05(modules_dir, gen_ctx)
    _write_module_06_matriz_riesgos_fair(modules_dir, gen_ctx)
    _write_module_07_conclusiones(modules_dir, gen_ctx)
    logger.info(f"🎉 Docs-as-Code modules extracted successfully in: {modules_dir}!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.info("Usage: python generate_asis_markdown_modules.py <blueprint_payload.json>")
        sys.exit(1)
    generate_modules(sys.argv[1])
