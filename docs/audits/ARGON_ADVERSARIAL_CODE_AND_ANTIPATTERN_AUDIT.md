### FORENSIC AUDIT REPORT: `gemini-4-argon`
**Classification:** CRITICAL ARCHITECTURAL DEVIATION  
**Target Files:** `server.py`, `web/src/components/ExecutiveFastAssessmentJourney.tsx`  
**Audit Verdict:** **REJECTED FOR PRODUCTION.** The inspected codebase violates the Zero-Hardcoding Mandate, the 100% Technical English Codebase Policy, and True Multi-Tenant Universality. It currently operates as a brittle "Demo-Ware" facade tailored to a handful of Spanish/UK/Brazilian companies rather than an enterprise-grade global actuarial platform.

---

### VECTOR 1: ZERO HARDCODING & TRUE UNIVERSAL MULTI-TENANCY VIOLATIONS

#### 1.1 Backend Corporate Name & Context Hardcoding (`server.py`)
* **Location:** `login()` endpoint (`server.py`).
  * **Violation:**
    ```python
    if "molins" in email:
        org_name = "Cementos Molins"
    elif "santander" in email:
        org_name = "Banco Santander"
    elif "bbva" in email:
        org_name = "BBVA"
    elif "telefonica" in email:
        org_name = "Telefónica"
    ```
  * **Location:** `resolve_context()` endpoint (`server.py`).
  * **Violation:**
    ```python
    if "molins" in raw:
        detected_company = "Cementos Molins"
        ...
    elif "starling" in raw:
        detected_company = "Starling Bank"
        ...
    elif "rededor" in raw or "dor" in raw:
        detected_company = "Rede D'Or São Luiz"
    ```
  * **Forensic Impact:** First, `"dor" in raw` is a catastrophic substring collision bug. Any input containing the English word `"vendor"`, `"director"`, `"corridor"`, or `"dormitory"` (or Spanish `"administrador"`, `"servidor"`, `"operador"`) will falsely resolve the enterprise to **"Rede D'Or São Luiz"** in Brazil (`BR`, `BRL`, `75,000` employees). Second, embedding specific corporate entities inside application control flow violates multi-tenant architecture.

#### 1.2 Frontend Inline Ternary Localization & Sector Switching (`ExecutiveFastAssessmentJourney.tsx`)
* **Location:** Tab 2 (`activeTab === 'context'`) Readout Grid.
  * **Violation 1 (Jurisdiction Name):**
    ```tsx
    {context.country === 'ES' && currentLocale === 'es'
      ? 'España'
      : context.country === 'GB' && currentLocale === 'es'
      ? 'Reino Unido'
      : context.country === 'BR' && currentLocale === 'es'
      ? 'Brasil'
      : (countries.find((c) => c.code === context.country)?.name || context.country)}
    ```
  * **Violation 2 (Regulatory Frameworks Fallback):**
    ```tsx
    : (context.industry === 'heavy_manufacturing' ? 'Directiva NIS2 · Directiva CER · RGPD' : 'DORA · NIS2 · RGPD')}
    ```
  * **Violation 3 (Industry Display Name):**
    ```tsx
    {context.industry === 'heavy_manufacturing' && currentLocale === 'es'
      ? 'Materiales de Construcción e Industria'
      : context.industry === 'banking' && currentLocale === 'es'
      ? 'Banca y Servicios Financieros'
      : context.industry === 'healthcare' && currentLocale === 'es'
      ? 'Sanidad y Redes Hospitalarias'
      : (industries.find((i) => i.id === context.industry)?.name || context.industry)}
    ```
  * **Violation 4 (Currency Symbol Formatting):**
    ```tsx
    ~{context.currency === 'GBP' ? `£${context.revenueM.toLocaleString()}M` : context.currency == ...
    ```
  * **Forensic Impact:** When a mid-sized manufacturing firm in Poland (`PL`, `PLN`), a bank in Japan (`JP`, `JPY`), an energy operator in Egypt (`EG`, `EGP`), or a US healthcare network (`US`, `USD`) logs in:
    1. If their regulatory array is empty, the UI forces European Union Spanish-language directives (`Directiva NIS2 · Directiva CER · RGPD` or `DORA · NIS2 · RGPD`) onto a US, Japanese, or Egyptian company, regardless of the active UI locale.
    2. Country and industry translations fail for any country other than `ES`, `GB`, `BR` or any industry other than the 3 hardcoded branches.

---

### VECTOR 2: 100% TECHNICAL ENGLISH CODEBASE POLICY VIOLATIONS

Every single string below violates the strict English-only source code mandate:

1. **`ExecutiveFastAssessmentJourney.tsx` (Tab 1 Welcome Headlines):**
   * `t('welcome_headline_line1', 'Diagnóstico de Infraestructura TI')` -> Default fallback in TSX is in Spanish! Must be 100% English (`'IT Infrastructure Diagnostic'`).
   * `t('welcome_headline_line2', 'y Hoja de Ruta de Modernización')` -> Default fallback is in Spanish! Must be `'& Modernization Roadmap'`.
   * `t('welcome_sub_line1', 'Evaluación modular de sus dominios operativos para identificar deuda técnica,')` -> Spanish fallback in TSX!
   * `t('welcome_sub_line2', 'cuantificar el impacto económico del riesgo y definir prioridades de inversión.')` -> Spanish fallback in TSX!
2. **`ExecutiveFastAssessmentJourney.tsx` (Tab 2 Readout Grid):**
   * `'España'`, `'Reino Unido'`, `'Brasil'` -> Hardcoded Spanish literals inside JSX.
   * `'Directiva NIS2 · Directiva CER · RGPD'`, `'DORA · NIS2 · RGPD'` -> Hardcoded Spanish regulatory literals inside JSX.
   * `'Materiales de Construcción e Industria'`, `'Banca y Servicios Financieros'`, `'Sanidad y Redes Hospitalarias'` -> Hardcoded Spanish industry literals inside JSX.
3. **`server.py` (Backend Heuristics & Login):**
   * `"Telefónica"`, `"españa"`, `"seguro"`, `"clínic"`, `"comercio"`, `"planta"`, `"fábrica"`, `"emplead"`, `"millon"`, `"pracownik"`, `"produkcyjn"`, `"kairze"`, `"warszawie"`, `"mitarbeiter"`.
   * **Audit Rule:** Multilingual NLP keyword dictionaries or domain registries do **not** belong inside Python source code (`server.py`). They must be externalized into a declarative JSON ontology (`engine_config/context_heuristics.json` and `engine_config/enterprise_registry.json`) so `server.py` remains 100% pure Technical English.

---

### VECTOR 3: DATA INTEGRITY & REGULATORY ONTOLOGY DEFECTS

1. **Incomplete Jurisdiction Mapping in `server.py`:**
   * `country_map` detects `EG` (Egypt), `PL` (Poland), `MX` (Mexico), and `CH` (Switzerland).
   * However, `jurisdiction_key_map` only maps `ES`, `GB`, `UK`, `US`, `DE`, `FR`, `JP`, `BR`.
   * When `EG`, `PL`, `MX`, or `CH` is resolved, `jurisdiction_key_map.get(detected_country_code)` returns `None` or falls back to `en-US` / empty list, causing a mismatch between the detected jurisdiction (`Poland`) and the regulatory frameworks applied (`US` or empty).
2. **Broken Revenue Regex Parsing (`server.py`):**
   * `rev_match = re.search(r"(\d+[\d,\.]*)\s*(?:m|million|millon|m€|m\$|m\b)", raw)`
   * In `float(rev_match.group(1).replace(",", "."))`: if the input is `"1,250.50 million"`, `.replace(",", ".")` turns it into `"1.250.50"`, which raises a `ValueError` on `float()`, silently failing and reverting to `500.0`.
3. **Naive Domain-to-Company Extraction (`server.py`):**
   * If a user enters an email `john.doe@group-enterprise.co.uk` or `cto@holding.com.br`, `resolve_context` checks `if "." in raw and not " " in raw:`. If `raw` is an email address, `clean_domain` retains `john.doe@group-enterprise.co.uk`, and `clean_domain.split(".")[0]` extracts `"John"` instead of the domain! It failed to strip the `local-part@` prefix of an email address.

---

### VECTOR 4: ARCHITECTURAL PURITY & ROBUSTNESS

1. **Dynamic Internationalization (`Intl.DisplayNames` + `locales_ui.json`):**
   * Never translate country names via `if/else` in React. Use the native browser standard `new Intl.DisplayNames([currentLocale], { type: 'region' }).of(context.country)` with a fallback to the `countries` catalog, and translate industry names strictly via `t(\`industry_${context.industry}\`, defaultName)`.
   * Never format currencies with ternary chains (`context.currency === 'GBP' ? '£' : ...`). Use `selectedCurrencySymbol` or `Intl.NumberFormat`.

---

### ACTIONABLE REFACTORING SPECIFICATIONS

#### 1. Externalize Domain & NLP Heuristics to `engine_config/context_intelligence.json`
Move all TLD mappings, currency codes, industry keywords, known global enterprise profiles (optional seed catalog), and baseline regulatory frameworks per region into `engine_config/context_intelligence.json`.

#### 2. Refactor `server.py` (`login` and `resolve_context`) — 100% Pure English, Zero Hardcoded Entities

```python
def extract_organization_from_email(email: str, registry: Dict[str, Any]) -> str:
    """Generically derives an organization name from any corporate email address."""
    if "@" not in email:
        return "Enterprise Client"
    domain = email.split("@", 1)[1].strip().lower()
    
    # 1. Check declarative enterprise registry if domain is known
    known_domains = registry.get("domains", {})
    if domain in known_domains:
        return known_domains[domain].get("company_name", "Enterprise Client")
    
    # 2. Generic algorithmic extraction from second-level domain (SLD)
    parts = domain.split(".")
    # Handle compound TLDs like .co.uk, .com.br, .com.mx, .co.jp
    compound_tlds = {"co", "com", "org", "net", "gov", "edu", "ac"}
    if len(parts) >= 3 and parts[-2] in compound_tlds:
        sld = parts[-3]
    elif len(parts) >= 2:
        sld = parts[-2]
    else:
        sld = parts[0]

    generic_providers = {"gmail", "outlook", "hotmail", "yahoo", "icloud", "protonmail", "live"}
    if sld in generic_providers:
        return "Enterprise Client"

    return " ".join(word.capitalize() for word in sld.replace("-", " ").replace("_", " ").split())
```

And in `resolve_context(req: ResolveContextRequest)`:
* Strip `mailto:` and `user@` prefixes before domain analysis.
* Use regex word boundaries (`\b`) when matching heuristic keywords from `context_intelligence.json` so substring collisions (like `"dor"` inside `"vendor"`) are mathematically impossible.
* Resolve regulatory frameworks dynamically from `regulatory_jurisdictions.json` with a universal regional fallback (`EU_BASELINE`, `GLOBAL_BASELINE` — e.g., `ISO/IEC 27001 · NIST CSF 2.0 · SOC 2`) so no non-European company is ever assigned EU directives by default.

#### 3. Refactor `ExecutiveFastAssessmentJourney.tsx` — 100% English Fallbacks & Universal i18n

Replace the contaminated Tab 1 & Tab 2 blocks with pure declarative i18n calls:

```tsx
{/* Bold Headline (Strictly 2 lines guaranteed, 100% English default fallbacks) */}
<div className="space-y-3">
  <h1 className="text-2xl sm:text-3xl lg:text-[40px] xl:text-[44px] font-extrabold tracking-tight text-[#1d1d1f] leading-tight sm:leading-[1.18]">
    <span className="block sm:whitespace-nowrap">
      {t('welcome_headline_line1', 'IT Infrastructure Diagnostic')}
    </span>
    <span className="block sm:whitespace-nowrap">
      {t('welcome_headline_line2', '& Modernization Roadmap')}
    </span>
  </h1>
  <p className="text-base sm:text-lg text-[#6e6e73] leading-relaxed max-w-2xl font-normal">
    <span className="block sm:whitespace-nowrap">
      {t('welcome_sub_line1', 'Modular assessment of your operational domains to identify technical debt,')}
    </span>
    <span className="block sm:whitespace-nowrap">
      {t('welcome_sub_line2', 'quantify economic risk exposure, and define investment priorities.')}
    </span>
  </p>
</div>
```

And in the Tab 2 Readout Grid:

```tsx
{/* Jurisdiction */}
<div className="space-y-1">
  <div className="text-[11px] font-bold text-[#8e8e93] uppercase tracking-wide">
    {t('jurisdiction_label', 'Regulatory Jurisdiction')}
  </div>
  <div className="text-base font-bold text-[#1d1d1f]">
    {(() => {
      try {
        return new Intl.DisplayNames([currentLocale], { type: 'region' }).of(context.country) || context.country;
      } catch {
        return countries.find((c) => c.code === context.country)?.name || context.country;
      }
    })()}
  </div>
  <div className="text-xs text-[#0072BC] font-mono">
    {context.regulatoryFrameworks && context.regulatoryFrameworks.length > 0
      ? context.regulatoryFrameworks.join(' · ')
      : t('default_regulatory_frameworks', 'ISO/IEC 27001 · NIST CSF 2.0 · SOC 2')}
  </div>
</div>

{/* Industry */}
<div className="space-y-1">
  <div className="text-[11px] font-bold text-[#8e8e93] uppercase tracking-wide">
    {t('industry_label', 'Operational Sector')}
  </div>
  <div className="text-base font-bold text-[#1d1d1f]">
    {t(
      `industry_${context.industry}`,
      industries.find((i) => i.id === context.industry)?.name || context.industry
    )}
  </div>
  <div className="text-xs text-[#6e6e73]">
    {t('benchmark_sectorial_sub', 'Sector Benchmark')}
  </div>
</div>

{/* Scale */}
<div className="space-y-1">
  <div className="text-[11px] font-bold text-[#8e8e93] uppercase tracking-wide">
    {t('scale_label', 'Baseline Scale')}
  </div>
  <div className="text-base font-bold text-[#1d1d1f]">
    {context.employees.toLocaleString(currentLocale)} {t('employees_abbr', 'empl.')}
  </div>
  <div className="text-xs text-[#6e6e73] font-mono">
    ~{selectedCurrencySymbol}{context.revenueM.toLocaleString(currentLocale)}M {t('annual_rev_abbr', 'rev.')}
  </div>
</div>
```

---
**DIRECTIVE TO ENGINEERING AGENT:**  
Execute the above remediations immediately across `server.py`, `engine_config/`, and `web/src/components/ExecutiveFastAssessmentJourney.tsx`, rebuild the static production bundle, and verify via automated Playwright assertions that zero hardcoded entity branches or Spanish literals remain in the source code.