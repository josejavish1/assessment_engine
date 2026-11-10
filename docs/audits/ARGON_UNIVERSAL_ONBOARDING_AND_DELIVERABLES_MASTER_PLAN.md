# MASTER ARCHITECTURE & IMPLEMENTATION PLAN: UNIVERSAL MULTI-TENANT GOVERNANCE ENGINE

**Document ID:** ARCH-2026-ARGN-99  
**Author:** `gemini-4-argon` (Supreme Cognitive Arbiter & Chief Enterprise Architect)  
**Status:** MANDATORY EXECUTION SPECIFICATION  
**Codebase Language Policy:** 100% Technical English (Zero Non-English Identifiers, Comments, or Inline Strings)  

---

## EXECUTIVE ARCHITECTURAL DIRECTIVE

The forensic failure observed during the **Cementos Molins** simulation stems from three systemic architectural sins:
1. **Epistemic Hardcoding:** Treating regulatory compliance (`DORA / NIS2 / RGPD`) as a static decorative string rather than a deterministic intersection of **Jurisdiction $\times$ Industry Vertical $\times$ Operational Topology**.
2. **Localization Leakage (Spanglish):** Passing raw database/catalog keys (`Heavy Process Manufacturing`, `Spain`, `~1250M EUR`) directly to the presentation layer without passing through an i18n formatting pipeline and locale-aware `Intl.NumberFormat` engine.
3. **Visual Containeritis & Bureaucratic Copy:** Regressing from an Apple/Linear editorial typography layout into nested gray-bordered HTML boxes accompanied by verbose, robotic taxonomy.

This Master Plan eradicates these anti-patterns permanently, establishing a **Universal Multi-Tenant Architecture** capable of onboarding any mid-market or mega-enterprise globally with zero code changes.

---

## PHASE 1: DECLARATIVE REGULATORY & COMPLIANCE ONTOLOGY (SSOT ARCHITECTURE)

### 1.1 Schema Specification: `engine_config/regulatory_frameworks.json`

All regulatory logic is extracted from Python/TSX code and centralized into a declarative ontology. The resolution engine evaluates the tuple `(jurisdiction_region, country_code, industry_id)` to yield exact, legally defensible frameworks.

```json
{
  "$schema": "https://platform.internal/schemas/regulatory-frameworks-v2.json",
  "version": "2.4.0",
  "frameworks_catalog": {
    "DORA": {
      "code": "DORA",
      "short_label_key": "reg.dora.short",
      "full_name_key": "reg.dora.full",
      "authority": "EU / ESAs (EBA, EIOPA, ESMA)",
      "citation": "Regulation (EU) 2022/2554",
      "risk_weight_multiplier": 1.35
    },
    "NIS2_ESSENTIAL": {
      "code": "NIS2",
      "short_label_key": "reg.nis2_essential.short",
      "full_name_key": "reg.nis2_essential.full",
      "authority": "ENISA / National CSIRTs",
      "citation": "Directive (EU) 2022/2555 (Annex I)",
      "risk_weight_multiplier": 1.25
    },
    "NIS2_IMPORTANT": {
      "code": "NIS2",
      "short_label_key": "reg.nis2_important.short",
      "full_name_key": "reg.nis2_important.full",
      "authority": "ENISA / National CSIRTs",
      "citation": "Directive (EU) 2022/2555 (Annex II)",
      "risk_weight_multiplier": 1.20
    },
    "IEC_62443": {
      "code": "IEC 62443",
      "short_label_key": "reg.iec62443.short",
      "full_name_key": "reg.iec62443.full",
      "authority": "ISA / IEC",
      "citation": "ISA/IEC 62443 Series (OT/IACS)",
      "risk_weight_multiplier": 1.30
    },
    "GDPR": {
      "code": "GDPR",
      "short_label_key": "reg.gdpr.short",
      "full_name_key": "reg.gdpr.full",
      "authority": "EDPB / National DPAs (AEPD, CNIL, BfDI)",
      "citation": "Regulation (EU) 2016/679",
      "risk_weight_multiplier": 1.15
    },
    "ENS": {
      "code": "ENS",
      "short_label_key": "reg.ens.short",
      "full_name_key": "reg.ens.full",
      "authority": "CCN-CERT (Spain)",
      "citation": "Real Decreto 311/2022",
      "risk_weight_multiplier": 1.15
    },
    "ISO_27001": {
      "code": "ISO 27001",
      "short_label_key": "reg.iso27001.short",
      "full_name_key": "reg.iso27001.full",
      "authority": "ISO / IEC",
      "citation": "ISO/IEC 27001:2022",
      "risk_weight_multiplier": 1.00
    },
    "ISO_22237": {
      "code": "ISO 22237",
      "short_label_key": "reg.iso22237.short",
      "full_name_key": "reg.iso22237.full",
      "authority": "ISO / CEN (EN 50600)",
      "citation": "ISO/IEC TS 22237 (Data Center Facilities)",
      "risk_weight_multiplier": 1.05
    },
    "FCA_PRA_OPRES": {
      "code": "FCA/PRA OpRes",
      "short_label_key": "reg.fca_pra.short",
      "full_name_key": "reg.fca_pra.full",
      "authority": "FCA & Bank of England (PRA)",
      "citation": "PS21/3 / SS1/21 Operational Resilience",
      "risk_weight_multiplier": 1.35
    },
    "UK_GDPR": {
      "code": "UK GDPR",
      "short_label_key": "reg.uk_gdpr.short",
      "full_name_key": "reg.uk_gdpr.full",
      "authority": "ICO (UK)",
      "citation": "Data Protection Act 2018 / UK GDPR",
      "risk_weight_multiplier": 1.15
    },
    "LGPD": {
      "code": "LGPD",
      "short_label_key": "reg.lgpd.short",
      "full_name_key": "reg.lgpd.full",
      "authority": "ANPD (Brazil)",
      "citation": "Lei Geral de Proteção de Dados (Lei nº 13.709/2018)",
      "risk_weight_multiplier": 1.20
    },
    "CFM_RDC330": {
      "code": "ANVISA RDC 330 / CFM",
      "short_label_key": "reg.cfm_rdc330.short",
      "full_name_key": "reg.cfm_rdc330.full",
      "authority": "ANVISA & Conselho Federal de Medicina",
      "citation": "RDC Nº 330/2019 & CFM nº 2.299/2021 (Clinical Telemetry/PACS)",
      "risk_weight_multiplier": 1.25
    },
    "BACEN_4893": {
      "code": "BACEN Res. 4.893",
      "short_label_key": "reg.bacen4893.short",
      "full_name_key": "reg.bacen4893.full",
      "authority": "Banco Central do Brasil",
      "citation": "Resolução CMN Nº 4.893/2021",
      "risk_weight_multiplier": 1.35
    },
    "SEC_CYBER": {
      "code": "SEC Cyber / NYDFS",
      "short_label_key": "reg.sec_cyber.short",
      "full_name_key": "reg.sec_cyber.full",
      "authority": "U.S. SEC / NYDFS",
      "citation": "17 CFR Parts 229, 232, 239, 240, 249 / 23 NYCRR 500",
      "risk_weight_multiplier": 1.35
    },
    "NERC_CIP": {
      "code": "NERC CIP",
      "short_label_key": "reg.nerc_cip.short",
      "full_name_key": "reg.nerc_cip.full",
      "authority": "NERC / FERC (North America)",
      "citation": "CIP-002 through CIP-014",
      "risk_weight_multiplier": 1.35
    },
    "HIPAA_HITECH": {
      "code": "HIPAA / HITECH",
      "short_label_key": "reg.hipaa.short",
      "full_name_key": "reg.hipaa.full",
      "authority": "U.S. HHS / OCR",
      "citation": "45 CFR Part 160 and Part 164",
      "risk_weight_multiplier": 1.30
    },
    "PCI_DSS": {
      "code": "PCI-DSS v4.0",
      "short_label_key": "reg.pcidss.short",
      "full_name_key": "reg.pcidss.full",
      "authority": "PCI Security Standards Council",
      "citation": "PCI-DSS v4.0",
      "risk_weight_multiplier": 1.20
    }
  },
  "resolution_matrix": {
    "financial_services": {
      "EU": ["DORA", "NIS2_ESSENTIAL", "GDPR", "ISO_27001"],
      "ES": ["DORA", "NIS2_ESSENTIAL", "GDPR", "ISO_27001"],
      "FR": ["DORA", "NIS2_ESSENTIAL", "GDPR", "ISO_27001"],
      "GB": ["FCA_PRA_OPRES", "DORA", "UK_GDPR", "ISO_27001"],
      "US": ["SEC_CYBER", "PCI_DSS", "ISO_27001"],
      "BR": ["BACEN_4893", "LGPD", "ISO_27001"],
      "DEFAULT": ["ISO_27001", "PCI_DSS"]
    },
    "heavy_manufacturing": {
      "EU": ["NIS2_IMPORTANT", "IEC_62443", "ISO_27001", "GDPR"],
      "ES": ["NIS2_IMPORTANT", "IEC_62443", "ISO_27001", "GDPR"],
      "FR": ["NIS2_IMPORTANT", "IEC_62443", "ISO_27001", "GDPR"],
      "GB": ["IEC_62443", "ISO_27001", "UK_GDPR"],
      "US": ["IEC_62443", "ISO_27001", "ISO_22237"],
      "BR": ["IEC_62443", "ISO_27001", "LGPD"],
      "DEFAULT": ["IEC_62443", "ISO_27001", "ISO_22237"]
    },
    "energy_utilities": {
      "EU": ["NIS2_ESSENTIAL", "IEC_62443", "ISO_27001", "GDPR"],
      "ES": ["NIS2_ESSENTIAL", "IEC_62443", "ENS", "GDPR"],
      "US": ["NERC_CIP", "IEC_62443", "ISO_27001"],
      "DEFAULT": ["IEC_62443", "ISO_27001"]
    },
    "healthcare_lifesciences": {
      "EU": ["NIS2_ESSENTIAL", "GDPR", "ISO_27001"],
      "ES": ["NIS2_ESSENTIAL", "ENS", "GDPR", "ISO_27001"],
      "GB": ["UK_GDPR", "ISO_27001"],
      "US": ["HIPAA_HITECH", "ISO_27001"],
      "BR": ["LGPD", "CFM_RDC330", "ISO_27001"],
      "DEFAULT": ["ISO_27001"]
    },
    "logistics_transport": {
      "EU": ["NIS2_ESSENTIAL", "ISO_27001", "GDPR"],
      "FR": ["NIS2_ESSENTIAL", "ISO_27001", "GDPR"],
      "ES": ["NIS2_ESSENTIAL", "ISO_27001", "GDPR"],
      "US": ["ISO_27001", "PCI_DSS"],
      "BR": ["LGPD", "ISO_27001"],
      "DEFAULT": ["ISO_27001"]
    },
    "retail_ecommerce": {
      "EU": ["PCI_DSS", "NIS2_IMPORTANT", "GDPR", "ISO_27001"],
      "US": ["PCI_DSS", "ISO_27001"],
      "BR": ["PCI_DSS", "LGPD", "ISO_27001"],
      "DEFAULT": ["PCI_DSS", "ISO_27001"]
    }
  }
}
```

### 1.2 Backend Resolution Service (`backend/services/regulatory_resolver.py`)

The backend resolves regulatory tags deterministically and translates them via `locales_ui.json` before sending the payload to the frontend or the `.docx` generator:

```python
from typing import List, Dict, Any
import json
from pathlib import Path

class RegulatoryResolverService:
    """Resolves jurisdiction and vertical-specific regulatory frameworks from SSOT."""

    def __init__(self, config_dir: Path):
        with open(config_dir / "regulatory_frameworks.json", "r", encoding="utf-8") as f:
            self._ontology = json.load(f)
        with open(config_dir / "locales_ui.json", "r", encoding="utf-8") as f:
            self._locales = json.load(f)

    def resolve_frameworks(
        self,
        industry_id: str,
        country_code: str,
        region_code: str,
        ui_locale: str = "en"
    ) -> Dict[str, Any]:
        matrix = self._ontology["resolution_matrix"].get(
            industry_id, self._ontology["resolution_matrix"]["heavy_manufacturing"]
        )
        framework_keys: List[str] = (
            matrix.get(country_code.upper())
            or matrix.get(region_code.upper())
            or matrix.get("DEFAULT", ["ISO_27001"])
        )

        catalog = self._ontology["frameworks_catalog"]
        locale_dict = self._locales.get(ui_locale, self._locales["en"])

        resolved_items = []
        short_tags = []

        for key in framework_keys:
            item = catalog.get(key)
            if not item:
                continue
            short_label = locale_dict.get(item["short_label_key"], item["code"])
            full_name = locale_dict.get(item["full_name_key"], item["code"])
            short_tags.append(short_label)
            resolved_items.append({
                "id": key,
                "code": item["code"],
                "short_label": short_label,
                "full_name": full_name,
                "authority": item["authority"],
                "citation": item["citation"],
                "risk_weight_multiplier": item["risk_weight_multiplier"]
            })

        return {
            "summary_badge": " · ".join(short_tags),
            "frameworks": resolved_items
        }
```

---

## PHASE 2: AUTONOMOUS CONTEXT PRE-HYDRATION & DYNAMIC LOCALE DECOUPLING

### 2.1 Zero-Spanglish Localization Architecture

Every string displayed in the UI—including country names, industry verticals, currencies, number formatting, and regulatory acronyms (e.g., `GDPR` $\rightarrow$ `RGPD` in `es` and `fr`, `LGPD` in `pt-BR`)—must be resolved through `engine_config/locales_ui.json` and formatted via standard ICU/Intl rules.

#### Additions to `engine_config/locales_ui.json`:

```json
{
  "en": {
    "country.ES": "Spain",
    "country.GB": "United Kingdom",
    "country.BR": "Brazil",
    "country.FR": "France",
    "country.US": "United States",
    "industry.heavy_manufacturing": "Industrial Manufacturing & Construction Materials",
    "industry.financial_services": "Banking & Cloud Financial Services",
    "industry.healthcare_lifesciences": "Healthcare & Hospital Networks",
    "industry.logistics_transport": "Global Logistics & Freight Forwarding",
    "industry.energy_utilities": "Energy & Critical Utilities",
    "industry.retail_ecommerce": "Retail & Omnichannel Commerce",
    "reg.dora.short": "DORA",
    "reg.nis2_essential.short": "NIS2",
    "reg.nis2_important.short": "NIS2",
    "reg.iec62443.short": "IEC 62443",
    "reg.gdpr.short": "GDPR",
    "reg.iso27001.short": "ISO 27001",
    "reg.fca_pra.short": "FCA/PRA OpRes",
    "reg.uk_gdpr.short": "UK GDPR",
    "reg.lgpd.short": "LGPD",
    "reg.cfm_rdc330.short": "ANVISA RDC 330",
    "tab2.step_eyebrow": "Step 2 of 4 · Organization & Assessment Scope",
    "tab2.headline": "Confirm your organization profile and assessment boundary",
    "tab2.subheadline": "We pre-configured your baseline parameters from your corporate domain ({domain}). Verify these metrics or narrow the assessment to a single operating unit.",
    "tab2.edit_action": "Edit parameters",
    "tab2.close_edit_action": "Done editing",
    "tab2.meta.industry": "Sector",
    "tab2.meta.jurisdiction": "Jurisdiction",
    "tab2.meta.revenue": "Annual Revenue",
    "tab2.meta.headcount": "Workforce",
    "tab2.meta.regulations": "Applicable Compliance",
    "tab2.scope.heading": "Where are you applying this assessment?",
    "tab2.scope.group.title": "Entire Corporate Group",
    "tab2.scope.group.desc": "Consolidated assessment across all regions, headquarters, and production sites ({revenue}, {employees} employees).",
    "tab2.scope.subsidiary.title": "Specific Operating Unit, Plant, or Subsidiary",
    "tab2.scope.subsidiary.desc": "Focused assessment for a single country, business unit, or facility. Financial risk exposure scales proportionally to the unit's footprint.",
    "tab2.scope.unit_name_label": "Operating unit or facility name",
    "tab2.scope.unit_name_placeholder": "e.g., UK Retail Banking Division, Martorell Plant, São Paulo South Hospital",
    "tab2.scope.unit_share_label": "Share of group operations (%)",
    "tab2.cta.continue": "Continue to Domain Selection"
  },
  "es": {
    "country.ES": "España",
    "country.GB": "Reino Unido",
    "country.BR": "Brasil",
    "country.FR": "Francia",
    "country.US": "Estados Unidos",
    "industry.heavy_manufacturing": "Industria de Procesos y Materiales de Construcción",
    "industry.financial_services": "Banca y Servicios Financieros",
    "industry.healthcare_lifesciences": "Sanidad y Redes Hospitalarias",
    "industry.logistics_transport": "Logística y Transporte Internacional",
    "industry.energy_utilities": "Energía e Infraestructuras Críticas",
    "industry.retail_ecommerce": "Retail y Comercio Omnicanal",
    "reg.dora.short": "DORA",
    "reg.nis2_essential.short": "NIS2",
    "reg.nis2_important.short": "NIS2",
    "reg.iec62443.short": "IEC 62443 (OT)",
    "reg.gdpr.short": "RGPD",
    "reg.iso27001.short": "ISO 27001",
    "reg.fca_pra.short": "FCA/PRA OpRes",
    "reg.uk_gdpr.short": "UK GDPR",
    "reg.lgpd.short": "LGPD",
    "reg.cfm_rdc330.short": "ANVISA RDC 330",
    "tab2.step_eyebrow": "Paso 2 de 4 · Organización y Alcance",
    "tab2.headline": "Confirme el perfil de su organización y el alcance del análisis",
    "tab2.subheadline": "Hemos configurado los parámetros base a partir de su dominio corporativo ({domain}). Verifique los datos o acote el análisis a una unidad operativa o planta concreta.",
    "tab2.edit_action": "Editar parámetros",
    "tab2.close_edit_action": "Guardar cambios",
    "tab2.meta.industry": "Sector de actividad",
    "tab2.meta.jurisdiction": "Jurisdicción",
    "tab2.meta.revenue": "Facturación anual",
    "tab2.meta.headcount": "Plantilla",
    "tab2.meta.regulations": "Marco normativo aplicable",
    "tab2.scope.heading": "¿Sobre qué perímetro desea realizar el diagnóstico?",
    "tab2.scope.group.title": "Grupo Corporativo Completo",
    "tab2.scope.group.desc": "Evaluación consolidada de todas las geografías, sedes centrales y plantas productivas ({revenue}, {employees} empleados).",
    "tab2.scope.subsidiary.title": "Filial, División Operativa o Planta Específica",
    "tab2.scope.subsidiary.desc": "Evaluación acotada a un país, unidad de negocio o centro productivo concreto. El modelo de riesgo financiero se ajustará al tamaño real de la unidad.",
    "tab2.scope.unit_name_label": "Nombre de la filial, división o planta",
    "tab2.scope.unit_name_placeholder": "Ej. Planta de Sant Vicenç dels Horts, División Hormigones España",
    "tab2.scope.unit_share_label": "Peso estimado sobre el grupo (%)",
    "tab2.cta.continue": "Seleccionar Áreas Técnicas"
  },
  "pt": {
    "country.ES": "Espanha",
    "country.GB": "Reino Unido",
    "country.BR": "Brasil",
    "country.FR": "França",
    "country.US": "Estados Unidos",
    "industry.heavy_manufacturing": "Manufatura Industrial e Materiais de Construção",
    "industry.financial_services": "Bancos e Serviços Financeiros em Nuvem",
    "industry.healthcare_lifesciences": "Saúde e Redes Hospitalares",
    "industry.logistics_transport": "Logística e Transporte Internacional",
    "industry.energy_utilities": "Energia e Utilidades Críticas",
    "industry.retail_ecommerce": "Varejo e Comércio Omnicanal",
    "reg.dora.short": "DORA",
    "reg.nis2_essential.short": "NIS2",
    "reg.nis2_important.short": "NIS2",
    "reg.iec62443.short": "IEC 62443 (OT)",
    "reg.gdpr.short": "GDPR",
    "reg.iso27001.short": "ISO 27001",
    "reg.fca_pra.short": "FCA/PRA OpRes",
    "reg.uk_gdpr.short": "UK GDPR",
    "reg.lgpd.short": "LGPD",
    "reg.cfm_rdc330.short": "ANVISA RDC 330 / CFM",
    "tab2.step_eyebrow": "Passo 2 de 4 · Organização e Escopo",
    "tab2.headline": "Confirme o perfil da sua organização e o escopo da avaliação",
    "tab2.subheadline": "Configuramos os parâmetros iniciais com base no seu domínio corporativo ({domain}). Revise os indicadores ou direcione a avaliação para uma unidade ou hospital específico.",
    "tab2.edit_action": "Editar parâmetros",
    "tab2.close_edit_action": "Concluir edição",
    "tab2.meta.industry": "Setor de atuação",
    "tab2.meta.jurisdiction": "Jurisdição",
    "tab2.meta.revenue": "Receita anual",
    "tab2.meta.headcount": "Colaboradores",
    "tab2.meta.regulations": "Conformidade regulatória",
    "tab2.scope.heading": "Qual é a abrangência desta avaliação?",
    "tab2.scope.group.title": "Grupo Corporativo Consolidado",
    "tab2.scope.group.desc": "Avaliação integrada de todas as regionais, centros corporativos e unidades operacionais ({revenue}, {employees} colaboradores).",
    "tab2.scope.subsidiary.title": "Unidade de Negócio, Regional ou Hospital Específico",
    "tab2.scope.subsidiary.desc": "Avaliação focada em uma operação ou complexo específico. A exposição financeira (FAIR) será dimensionada proporcionalmente à unidade.",
    "tab2.scope.unit_name_label": "Nome da unidade, regional ou complexo hospitalar",
    "tab2.scope.unit_name_placeholder": "Ex: Regional São Paulo, Hospital Copa Star, Divisão Diagnósticos",
    "tab2.scope.unit_share_label": "Participação estimada no grupo (%)",
    "tab2.cta.continue": "Selecionar Domínios Técnicos"
  }
}
```

### 2.2 Locale-Aware Currency & Headcount Formatter (`frontend/src/utils/formatters.ts`)

Never concatenate `~` + `revenue_m` + `EUR` in JSX. All numerical displays must use a deterministic formatter:

```typescript
export function formatCompactRevenue(
  revenueMillions: number,
  currencyCode: "EUR" | "GBP" | "USD" | "BRL",
  locale: "en" | "es" | "pt" | "fr"
): string {
  const bcp47Map: Record<string, string> = {
    es: "es-ES",
    en: "en-GB",
    pt: "pt-BR",
    fr: "fr-FR",
  };
  const bcp47 = bcp47Map[locale] || "en-GB";
  const formattedNumber = new Intl.NumberFormat(bcp47, {
    maximumFractionDigits: 0,
  }).format(Math.round(revenueMillions));

  if (locale === "es") {
    const symbol = currencyCode === "EUR" ? "M€" : `M ${currencyCode}`;
    return `${formattedNumber} ${symbol}`;
  }
  if (locale === "pt") {
    const symbol = currencyCode === "BRL" ? "R$" : currencyCode;
    return `${symbol} ${formattedNumber} mi`;
  }
  const symbolMap: Record<string, string> = {
    GBP: "£",
    EUR: "€",
    USD: "$",
    BRL: "R$",
  };
  const sym = symbolMap[currencyCode] || `${currencyCode} `;
  return `${sym}${formattedNumber}M`;
}

export function formatIntegerCount(
  value: number,
  locale: "en" | "es" | "pt" | "fr"
): string {
  const bcp47Map: Record<string, string> = {
    es: "es-ES",
    en: "en-GB",
    pt: "pt-BR",
    fr: "fr-FR",
  };
  return new Intl.NumberFormat(bcp47Map[locale] || "en-GB").format(Math.round(value));
}
```

*Result verification:*
- `formatCompactRevenue(1250, "EUR", "es")` $\rightarrow$ **`1.250 M€`** (Zero `~1250M EUR` Spanglish!).
- `formatCompactRevenue(680, "GBP", "en")` $\rightarrow$ **`£680M`**.
- `formatCompactRevenue(25000, "BRL", "pt")` $\rightarrow$ **`R$ 25.000 mi`**.

---

## PHASE 3: EDITORIAL TAB 2 ARCHITECTURE (ZERO CONTAINERITIS)

### 3.1 Elimination of Nested Gray Cages

Tab 2 must follow the exact **Apple / Linear Tier-1 Editorial Design System** established in Tab 1:
- **Zero outer cards (`bg-white border`) wrapping the screen.** The page background is a single, continuous editorial canvas (`#fbfbfd` or `#ffffff`) with a left-aligned `max-w-3xl` column.
- **Profile Summary Strip:** Rendered as a clean, horizontal hairline-divided architectural ledger (`border-y border-neutral-200 py-5 grid grid-cols-2 sm:grid-cols-5 gap-6`) with crisp uppercase micro-labels (`text-[11px] font-medium tracking-wider text-neutral-400 uppercase`) and high-contrast values (`text-[15px] font-semibold text-neutral-900`).
- **Inline Calibration Drawer:** Hidden by default. Clicking `"Edit parameters"` (`text-xs font-medium text-blue-600 hover:text-blue-700`) expands a smooth inline row directly below the ledger to adjust Industry, Country, Currency, Annual Revenue, or Headcount without modal popups or card clutter.
- **Perimeter Selection:** Two clean, interactive rows separated by a single hairline (`divide-y divide-neutral-200 border-y border-neutral-200`), using a custom minimalist indicator circle on the left and clean typography on the right. If **"Specific Operating Unit, Plant, or Subsidiary"** is selected, a clean 2-column inline input row (`Unit Name` + `Share of Group Operations %` slider/input) expands smoothly, dynamically recalculating the effective FAIR revenue and workforce baseline in real time.
- **Zero Viewport Overflow:** Designed to fit comfortably within `1440x900` and `1920x1080` with `scrollHeight <= clientHeight`.

### 3.2 Editorial Tab 2 Component Specification (`frontend/src/components/assessment/Step2PerimeterEditorial.tsx`)

```tsx
import React, { useState } from "react";
import { formatCompactRevenue, formatIntegerCount } from "../../utils/formatters";

export interface OrganizationProfile {
  entityName: string;
  domain: string;
  industryId: string;
  industryLabel: string;
  countryCode: string;
  countryLabel: string;
  currency: "EUR" | "GBP" | "USD" | "BRL";
  annualRevenueMillions: number;
  employees: number;
  regulatorySummaryBadge: string;
  scopeType: "GROUP" | "SUBSIDIARY";
  subsidiaryName: string;
  subsidiarySharePercent: number;
}

interface Step2Props {
  profile: OrganizationProfile;
  locale: "en" | "es" | "pt" | "fr";
  t: (key: string, vars?: Record<string, string>) => string;
  onUpdateProfile: (updated: Partial<OrganizationProfile>) => void;
  onContinue: () => void;
}

export const Step2PerimeterEditorial: React.FC<Step2Props> = ({
  profile,
  locale,
  t,
  onUpdateProfile,
  onContinue,
}) => {
  const [isEditingBaseline, setIsEditingBaseline] = useState(false);

  const effectiveMultiplier =
    profile.scopeType === "SUBSIDIARY"
      ? Math.max(0.01, Math.min(1, profile.subsidiarySharePercent / 100))
      : 1.0;

  const effectiveRevenue = profile.annualRevenueMillions * effectiveMultiplier;
  const effectiveEmployees = Math.round(profile.employees * effectiveMultiplier);

  return (
    <section className="max-w-3xl mx-auto pt-6 pb-10 px-4 sm:px-0">
      {/* Eyebrow & Editorial Header */}
      <div className="mb-6">
        <p className="text-xs font-medium tracking-wide text-neutral-400 uppercase mb-2">
          {t("tab2.step_eyebrow")}
        </p>
        <div className="flex items-baseline justify-between gap-4">
          <h1 className="text-2xl sm:text-[28px] font-semibold tracking-tight text-neutral-900 leading-tight">
            {profile.entityName}
          </h1>
          <button
            type="button"
            onClick={() => setIsEditingBaseline(!isEditingBaseline)}
            className="text-xs font-medium text-neutral-500 hover:text-neutral-900 underline underline-offset-4 transition-colors shrink-0"
          >
            {isEditingBaseline ? t("tab2.close_edit_action") : t("tab2.edit_action")}
          </button>
        </div>
        <p className="mt-2 text-sm text-neutral-600 leading-relaxed max-w-2xl">
          {t("tab2.subheadline", { domain: profile.domain })}
        </p>
      </div>

      {/* Hairline Architectural Ledger (Zero Box Containeritis) */}
      <div className="border-y border-neutral-200 py-4 grid grid-cols-2 sm:grid-cols-5 gap-y-4 gap-x-6">
        <div>
          <dt className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">
            {t("tab2.meta.industry")}
          </dt>
          <dd className="mt-1 text-sm font-medium text-neutral-900 leading-snug">
            {profile.industryLabel}
          </dd>
        </div>

        <div>
          <dt className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">
            {t("tab2.meta.jurisdiction")}
          </dt>
          <dd className="mt-1 text-sm font-medium text-neutral-900">
            {profile.countryLabel} ({profile.currency})
          </dd>
        </div>

        <div>
          <dt className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">
            {t("tab2.meta.revenue")}
          </dt>
          <dd className="mt-1 text-sm font-semibold text-neutral-900 tabular-nums">
            {formatCompactRevenue(effectiveRevenue, profile.currency, locale)}
          </dd>
        </div>

        <div>
          <dt className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">
            {t("tab2.meta.headcount")}
          </dt>
          <dd className="mt-1 text-sm font-semibold text-neutral-900 tabular-nums">
            {formatIntegerCount(effectiveEmployees, locale)}
          </dd>
        </div>

        <div className="col-span-2 sm:col-span-1">
          <dt className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">
            {t("tab2.meta.regulations")}
          </dt>
          <dd
            data-testid="regulatory-summary-badge"
            className="mt-1 text-xs font-semibold text-neutral-800 leading-snug"
          >
            {profile.regulatorySummaryBadge}
          </dd>
        </div>
      </div>

      {/* Optional Inline Parameter Calibration Row */}
      {isEditingBaseline && (
        <div className="py-4 border-b border-neutral-200 grid grid-cols-1 sm:grid-cols-3 gap-4 bg-neutral-50/50 px-3 -mx-3">
          <label className="block">
            <span className="text-xs font-medium text-neutral-600">
              {t("tab2.meta.revenue")} (M {profile.currency})
            </span>
            <input
              type="number"
              min={1}
              value={profile.annualRevenueMillions}
              onChange={(e) =>
                onUpdateProfile({ annualRevenueMillions: Number(e.target.value) || 1 })
              }
              className="mt-1 block w-full border-b border-neutral-300 bg-transparent py-1 text-sm font-medium text-neutral-900 focus:border-neutral-900 focus:outline-none"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-neutral-600">
              {t("tab2.meta.headcount")}
            </span>
            <input
              type="number"
              min={1}
              value={profile.employees}
              onChange={(e) =>
                onUpdateProfile({ employees: Number(e.target.value) || 1 })
              }
              className="mt-1 block w-full border-b border-neutral-300 bg-transparent py-1 text-sm font-medium text-neutral-900 focus:border-neutral-900 focus:outline-none"
            />
          </label>
        </div>
      )}

      {/* Perimeter Scope Decision */}
      <div className="mt-8">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-3">
          {t("tab2.scope.heading")}
        </h2>

        <div className="divide-y divide-neutral-200 border-y border-neutral-200">
          {/* Option 1: Consolidated Group */}
          <label
            onClick={() => onUpdateProfile({ scopeType: "GROUP" })}
            className="flex items-start gap-3.5 py-4 cursor-pointer group"
          >
            <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-neutral-400 group-hover:border-neutral-900">
              {profile.scopeType === "GROUP" && (
                <span className="h-2 w-2 rounded-full bg-neutral-900" />
              )}
            </span>
            <div className="flex-1">
              <div className="text-sm font-semibold text-neutral-900">
                {t("tab2.scope.group.title")}
              </div>
              <p className="mt-0.5 text-xs text-neutral-500 leading-relaxed">
                {t("tab2.scope.group.desc", {
                  revenue: formatCompactRevenue(
                    profile.annualRevenueMillions,
                    profile.currency,
                    locale
                  ),
                  employees: formatIntegerCount(profile.employees, locale),
                })}
              </p>
            </div>
          </label>

          {/* Option 2: Specific Operating Unit / Subsidiary / Plant */}
          <div className="py-4">
            <label
              onClick={() => onUpdateProfile({ scopeType: "SUBSIDIARY" })}
              className="flex items-start gap-3.5 cursor-pointer group"
            >
              <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-neutral-400 group-hover:border-neutral-900">
                {profile.scopeType === "SUBSIDIARY" && (
                  <span className="h-2 w-2 rounded-full bg-neutral-900" />
                )}
              </span>
              <div className="flex-1">
                <div className="text-sm font-semibold text-neutral-900">
                  {t("tab2.scope.subsidiary.title")}
                </div>
                <p className="mt-0.5 text-xs text-neutral-500 leading-relaxed">
                  {t("tab2.scope.subsidiary.desc")}
                </p>
              </div>
            </label>

            {profile.scopeType === "SUBSIDIARY" && (
              <div className="mt-4 pl-7 grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-neutral-600">
                    {t("tab2.scope.unit_name_label")}
                  </label>
                  <input
                    type="text"
                    value={profile.subsidiaryName}
                    onChange={(e) =>
                      onUpdateProfile({ subsidiaryName: e.target.value })
                    }
                    placeholder={t("tab2.scope.unit_name_placeholder")}
                    className="mt-1 w-full border-b border-neutral-300 bg-transparent py-1.5 text-sm text-neutral-900 placeholder-neutral-400 focus:border-neutral-900 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-neutral-600">
                    {t("tab2.scope.unit_share_label")}:{" "}
                    <span className="font-semibold text-neutral-900">
                      {profile.subsidiarySharePercent}%
                    </span>
                  </label>
                  <input
                    type="range"
                    min={5}
                    max={100}
                    step={5}
                    value={profile.subsidiarySharePercent}
                    onChange={(e) =>
                      onUpdateProfile({
                        subsidiarySharePercent: Number(e.target.value),
                      })
                    }
                    className="mt-2.5 w-full accent-neutral-900"
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Primary Action Footer */}
      <div className="mt-7 flex items-center justify-between">
        <button
          type="button"
          onClick={onContinue}
          data-testid="step2-continue-btn"
          className="inline-flex items-center gap-2 rounded-md bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-neutral-800 transition-colors"
        >
          <span>{t("tab2.cta.continue")}</span>
          <span aria-hidden="true">→</span>
        </button>
      </div>
    </section>
  );
};
```

---

## PHASE 4: MODULAR DOMAIN SELECTION & DISCOVERY PIPELINE (TAB 3 PRE-FLIGHT)

### 4.1 Eradicating the "10 Mandatory Towers" Fallacy

1. **Header & Tab 1 Cleanup:**
   - Remove all premature `0 / 10` counters and hardcoded `10 Towers` badges from the global navigation header and Tab 1.
   - Until the user confirms their domain selection in Step 3, the header displays only the active corporate context (`Cementos Molins · ES · 1.250 M€`) and the 4-step progress indicator.
2. **Step 3 Sub-State A: Intelligent Domain Selector (Pre-Flight):**
   - Upon clicking **"Continue to Domain Selection"** in Step 2, Step 3 opens in **Scope Selection Mode** before showing any technical questionnaire items.
   - The platform pre-recommends domains based on the tenant's **Operating Topology** (resolved from the corporate profile):
     - **Cloud-Native FinTech (`Starling Bank`):** Pre-selects Cloud Infrastructure, Cybersecurity, DevSecOps/SRE, Data/AI, Observability, and Network/Zero-Trust; leaves legacy Mainframe/Physical Data Center Facility unselected by default (though toggleable).
     - **Heavy Process Manufacturing (`Cementos Molins`):** Pre-selects Industrial OT/Edge & Plant Networks, Hybrid Compute, Cybersecurity (IEC 62443 / NIS2), IT/OT Continuity & DR, and ERP/Core Systems.
     - **Hospital Network (`Rede D'Or`):** Pre-selects Clinical Infrastructure & PACS Storage, Network High Availability, Cybersecurity & Patient Data Privacy (LGPD), and Continuity/DR.
3. **Flexible Quick-Presets & Granular Toggles:**
   - Users can choose a preset pill (`Recommended for your sector`, `Cloud & Security Core (4 domains)`, `Full 360° Architecture (10 domains)`) or toggle individual domains on/off.
   - Once the user clicks **"Start Technical Discovery ({N} domains)"**, the progress bar locks onto the exact denominator (`0 / {N}`), and the `.docx` generation engine dynamically generates Tome 1 + only the `{N}` selected Technical Annexes.

---

## PHASE 5: AUTOMATED PLAYWRIGHT CROSS-TENANT VERIFICATION MATRIX

### 5.1 Multi-Tenant Seed Profiles (`engine_config/corporate_profiles_seed.json`)

The backend domain-enrichment catalog must contain accurate baseline records for our global verification matrix:

| Email Domain | Entity Name | Country (`country_code`) | Industry (`industry_id`) | Currency | Revenue (M) | Employees | Default UI Locale | Expected Regulatory Badge |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `molins.com` / `cemolins.es` | **Cementos Molins** | `ES` (`España`) | `heavy_manufacturing` | `EUR` | `1250` | `6500` | `es` | `NIS2 · IEC 62443 (OT) · ISO 27001 · RGPD` |
| `starlingbank.co.uk` | **Starling Bank** | `GB` (`United Kingdom`) | `financial_services` | `GBP` | `680` | `3200` | `en` | `FCA/PRA OpRes · DORA · UK GDPR · ISO 27001` |
| `rededor.com.br` | **Rede D'Or São Luiz** | `BR` (`Brasil`) | `healthcare_lifesciences` | `BRL` | `25000` | `71000` | `pt` | `LGPD · ANVISA RDC 330 / CFM · ISO 27001` |
| `geodis.com` | **Geodis** | `FR` (`France`) | `logistics_transport` | `EUR` | `11600` | `49400` | `fr` | `NIS2 · ISO 27001 · RGPD` |

### 5.2 Automated Playwright Specification (`tests/e2e/multi_tenant_governance.spec.ts`)

```typescript
import { test, expect } from "@playwright/test";

const TENANT_MATRIX = [
  {
    name: "Case A: Cementos Molins (Spain, Heavy Manufacturing, ES)",
    email: "cto@molins.com",
    expectedEntity: "Cementos Molins",
    expectedCountry: "España (EUR)",
    expectedRevenue: "1.250 M€",
    expectedIndustry: "Industria de Procesos y Materiales de Construcción",
    mustIncludeRegulations: ["NIS2", "IEC 62443", "ISO 27001", "RGPD"],
    forbiddenStrings: ["DORA", "Spain", "Heavy Process Manufacturing", "~1250M EUR", "Expediente Pre-Configurado"],
  },
  {
    name: "Case B: Starling Bank (UK, FinTech, EN)",
    email: "head.infrastructure@starlingbank.co.uk",
    expectedEntity: "Starling Bank",
    expectedCountry: "United Kingdom (GBP)",
    expectedRevenue: "£680M",
    expectedIndustry: "Banking & Cloud Financial Services",
    mustIncludeRegulations: ["FCA/PRA OpRes", "DORA", "UK GDPR", "ISO 27001"],
    forbiddenStrings: ["IEC 62443", "RGPD", "LGPD", "Paso 2 de 4"],
  },
  {
    name: "Case C: Rede D'Or São Luiz (Brazil, Healthcare, PT)",
    email: "diretor.ti@rededor.com.br",
    expectedEntity: "Rede D'Or São Luiz",
    expectedCountry: "Brasil (BRL)",
    expectedRevenue: "R$ 25.000 mi",
    expectedIndustry: "Saúde e Redes Hospitalares",
    mustIncludeRegulations: ["LGPD", "ANVISA RDC 330", "ISO 27001"],
    forbiddenStrings: ["DORA", "RGPD", "Spain", "Brazil", "~25000M BRL"],
  },
];

test.describe("Multi-Tenant Regulatory, Linguistic & Editorial UX Verification", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  for (const tenant of TENANT_MATRIX) {
    test(`Verifies epistemic & linguistic purity for ${tenant.name}`, async ({ page }) => {
      await page.goto("/login");
      await page.fill('input[type="email"]', tenant.email);
      await page.click('button[type="submit"]');

      // Step 1: Verify zero premature "0 / 10" counters and advance to Step 2
      const bodyTextStep1 = await page.locator("body").innerText();
      expect(bodyTextStep1).not.toContain("0 / 10");
      await page.click('[data-testid="step1-start-btn"]');

      // Step 2: Verify Entity, Country, Revenue, Industry, and Regulatory Accuracy
      await expect(page.locator("h1")).toContainText(tenant.expectedEntity);
      const bodyTextStep2 = await page.locator("body").innerText();

      expect(bodyTextStep2).toContain(tenant.expectedCountry);
      expect(bodyTextStep2).toContain(tenant.expectedRevenue);
      expect(bodyTextStep2).toContain(tenant.expectedIndustry);

      const regBadge = await page.getByTestId("regulatory-summary-badge").innerText();
      for (const reqReg of tenant.mustIncludeRegulations) {
        expect(regBadge).toContain(reqReg);
      }

      // Verify absolute absence of Spanglish, bureaucratic copy, and wrong regulations
      for (const forbidden of tenant.forbiddenStrings) {
        expect(bodyTextStep2).not.toContain(forbidden);
      }

      // Verify Zero Vertical Scrollbar on 1440x900 desktop viewport
      const isOverflowing = await page.evaluate(() => {
        return document.documentElement.scrollHeight > document.documentElement.clientHeight;
      });
      expect(isOverflowing).toBe(false);
    });
  }
});
```

---

## SUMMARY OF EXECUTION CHECKLIST

1. **Create `engine_config/regulatory_frameworks.json`** and wire `RegulatoryResolverService` into the backend profile hydration endpoint and `.docx` builder.
2. **Update `engine_config/locales_ui.json`** with localized country names, industry labels, regulatory short-codes, and natural executive copy across `en`, `es`, `pt`, and `fr`.
3. **Refactor Tab 2 (`Step2PerimeterEditorial.tsx`)** to use the hairline architectural ledger, `formatCompactRevenue()`, and the Group vs. Subsidiary perimeter selector with zero gray container boxes.
4. **Remove premature `0 / 10` badges** from the header and Tab 1, placing the modular Domain Selector at the entry of Step 3.
5. **Execute the Playwright Multi-Tenant Suite** across `molins.com`, `starlingbank.co.uk`, and `rededor.com.br` until 100% of assertions pass with zero scrollbars.