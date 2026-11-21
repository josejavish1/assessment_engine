'use server';

import fs from 'fs/promises';
import path from 'path';
import { clientSchema, type ClientFormValues } from './schema';
import { getSessionUser } from '@/lib/auth/session';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const WORKSPACES_ROOT = path.join(REPO_ROOT, 'workspaces');
const SIMULATION_DIR = path.join(REPO_ROOT, 'workspaces', 'simulations');
const SIMULATION_SUMMARY_PATH = path.join(SIMULATION_DIR, 'SIMULATION_SUMMARY.json');
const REGISTRY_PATH = path.join(REPO_ROOT, 'engine_config', 'enterprise_registry.json');

export interface ClientAccount {
  id: string;
  slug: string;
  name: string;
  domain: string;
  sector: string;
  country: string;
  currency: string;
  standard: string;
  assessmentsEnCurso: number;
  assessmentsFinalizados: number;
  maturityScore: string;
  aleFormatted: string;
  status: 'Activa' | 'Completada' | 'En Pausa';
  description: string;
}

interface EnterpriseRegistryEntry {
  company_name?: string;
  industry?: string;
  country_name?: string;
  currency?: string;
  standard?: string;
  description?: string;
}

interface EnterpriseRegistryFile {
  domains?: Record<string, EnterpriseRegistryEntry>;
}

interface SimulationSummaryItem {
  client_slug?: string;
  company_name?: string;
  country?: string;
  currency?: string;
  industry?: string;
  standard?: string;
  global_score?: string;
  global_band?: string;
  ale_formatted?: string;
  overall_fair_score?: number;
}

export async function getAllClientAccountsAction(): Promise<{ success: boolean; data: ClientAccount[] }> {
  const user = await getSessionUser();
  if (!user) {
    return { success: false, data: [] };
  }

  const baseAccounts: ClientAccount[] = [
    {
      id: 'acc_01',
      slug: 'nordic_grid_power_gmbh',
      name: 'Nordic Grid Power GmbH',
      domain: 'nordicgrid.de',
      sector: 'Energía & Utilities',
      country: 'Alemania (DE)',
      currency: 'EUR (€)',
      standard: 'NIS2 / Critical Infrastructure',
      assessmentsEnCurso: 1,
      assessmentsFinalizados: 1,
      maturityScore: '2.9 / 5.0',
      aleFormatted: '131.574,57 €',
      status: 'Activa',
      description: 'Operador europeo de red eléctrica con estrictos requisitos de resiliencia física y protección de datos soberanos.',
    },
    {
      id: 'acc_02',
      slug: 'global_nippon_financial_group',
      name: 'Global Nippon Financial Group',
      domain: 'globalnippon.jp',
      sector: 'Banca & Finanzas',
      country: 'Japón (JP)',
      currency: 'JPY (¥)',
      standard: 'Basel III / Operational Resilience DORA',
      assessmentsEnCurso: 1,
      assessmentsFinalizados: 0,
      maturityScore: '2.9 / 5.0',
      aleFormatted: '20.500.000 ¥',
      status: 'Activa',
      description: 'Conglomerado bancario internacional sometido a auditoría continua de resiliencia operativa y gestión de riesgo sistémico.',
    },
    {
      id: 'acc_03',
      slug: 'meridian_biohealth_inc',
      name: 'Meridian BioHealth Inc.',
      domain: 'meridianbio.com',
      sector: 'Salud & Farmacia',
      country: 'Estados Unidos (US)',
      currency: 'USD ($)',
      standard: 'HIPAA / Clinical Data Privacy',
      assessmentsEnCurso: 1,
      assessmentsFinalizados: 0,
      maturityScore: '2.9 / 5.0',
      aleFormatted: '185.000,00 $',
      status: 'Activa',
      description: 'Líder biotecnológico global que realiza ensayos clínicos con estricta gobernanza de metadatos genómicos y cadena de custodia.',
    },
    {
      id: 'acc_04',
      slug: 'iberia_retail_logistics_sa',
      name: 'Iberia Retail Logistics S.A.',
      domain: 'iberialogistics.es',
      sector: 'Industria & Logística',
      country: 'España (ES)',
      currency: 'EUR (€)',
      standard: 'ENS Categoría Alta / DMBOK',
      assessmentsEnCurso: 1,
      assessmentsFinalizados: 0,
      maturityScore: '2.9 / 5.0',
      aleFormatted: '95.000,00 €',
      status: 'Activa',
      description: 'Operador logístico y de distribución con certificación de seguridad nacional y auditoría de gobernanza de datos DMBOK.',
    },
    {
      id: 'acc_05',
      slug: 'once',
      name: 'Organización Nacional de Ciegos Españoles',
      domain: 'once.es',
      sector: 'Sector Público',
      country: 'España (ES)',
      currency: 'EUR (€)',
      standard: 'ENS Alto / Esquema Nacional de Seguridad',
      assessmentsEnCurso: 1,
      assessmentsFinalizados: 0,
      maturityScore: '3.2 / 5.0',
      aleFormatted: '140.000,00 €',
      status: 'Activa',
      description: 'Institución pública española de carácter social con infraestructuras críticas y CPDs híbridos.',
    },
  ];

  try {
    const raw = await fs.readFile(REGISTRY_PATH, 'utf-8');
    const registry = JSON.parse(raw) as EnterpriseRegistryFile;
    const domains = registry.domains || {};

    const result = [...baseAccounts];

    for (const [dom, meta] of Object.entries(domains)) {
      const cleanDom = dom.toLowerCase().replace(/https?:\/\//, '').replace(/^www\./, '').split('/')[0];
      if (
        result.some(
          (a) => a.domain.toLowerCase() === cleanDom || a.name.toLowerCase() === meta.company_name?.toLowerCase()
        )
      ) {
        continue;
      }

      const slug = cleanDom.split('.')[0].replace(/[^a-z0-9]+/g, '_');
      const friendlySector =
        cleanDom.includes('repsol')
          ? 'Energía & Utilities'
          : meta.industry === 'banking'
          ? 'Banca & Finanzas'
          : meta.industry === 'healthcare'
          ? 'Salud & Farmacia'
          : meta.industry === 'critical_infrastructure'
          ? 'Energía & Utilities'
          : meta.industry === 'heavy_manufacturing'
          ? 'Industria & Logística'
          : meta.industry || 'Servicios Corporativos';

      result.push({
        id: `acc_${slug}`,
        slug: slug,
        name: meta.company_name || slug.toUpperCase(),
        domain: cleanDom,
        sector: friendlySector,
        country: meta.country_name || (cleanDom.endsWith('.es') ? 'España (ES)' : 'Internacional'),
        currency: (meta.currency || 'EUR') + ' (€)',
        standard: meta.standard || 'NIS2 / Critical Infrastructure',
        assessmentsEnCurso: 1,
        assessmentsFinalizados: 0,
        maturityScore: '2.8 / 5.0',
        aleFormatted: '95.000,00 €',
        status: 'Activa',
        description: meta.description || `Expediente de cuenta para ${meta.company_name} (${cleanDom}) inicializado.`,
      });
    }

    const filtered = (user.role === 'CLIENT' && user.clientSlug)
      ? result.filter((a) => a.slug === user.clientSlug)
      : result;

    return { success: true, data: filtered };
  } catch {
    const fallback = (user.role === 'CLIENT' && user.clientSlug)
      ? baseAccounts.filter((a) => a.slug === user.clientSlug)
      : baseAccounts;
    return { success: true, data: fallback };
  }
}

export async function createNewClientAssessment(
  rawValues: ClientFormValues
): Promise<{ success: boolean; message: string; slug?: string; error?: string }> {
  const user = await getSessionUser();
  if (!user) {
    return { success: false, message: 'Unauthorized: Authentication session required', error: 'Unauthorized' };
  }

  if (user.role === 'CLIENT') {
    return {
      success: false,
      message: 'Forbidden: Client creation requires NTT DATA Consultant or Admin privileges',
      error: 'Forbidden',
    };
  }

  const parsed = clientSchema.safeParse(rawValues);
  if (!parsed.success) {
    const issue = parsed.error.issues[0]?.message || 'Invalid form input data';
    return { success: false, message: issue, error: issue };
  }

  const { name, slug, sector, country, currency, standard, description, domain } = parsed.data;

  try {
    // 1. Provision Physical Directories
    const tenantWorkspace = path.join(WORKSPACES_ROOT, slug);
    await fs.mkdir(path.join(tenantWorkspace, 'evidence'), { recursive: true });
    await fs.mkdir(path.join(tenantWorkspace, 'scratchpad'), { recursive: true });
    await fs.mkdir(path.join(tenantWorkspace, 'deliverables'), { recursive: true });
    const clientSimDir = path.join(SIMULATION_DIR, slug);
    await fs.mkdir(clientSimDir, { recursive: true });

    // Derive domain key
    const domainKey = (domain || `${slug}.com`)
      .toLowerCase()
      .replace(/https?:\/\//, '')
      .replace(/^www\./, '')
      .split('/')[0];

    // Infer Country and Currency based on domain TLD if default
    let resolvedCountry = country;
    let resolvedCurrency = currency;
    if (domainKey.endsWith('.es')) {
      resolvedCountry = 'España (ES)';
      resolvedCurrency = 'EUR (€)';
    } else if (domainKey.endsWith('.de')) {
      resolvedCountry = 'Alemania (DE)';
      resolvedCurrency = 'EUR (€)';
    } else if (domainKey.endsWith('.jp')) {
      resolvedCountry = 'Japón (JP)';
      resolvedCurrency = 'JPY (¥)';
    } else if (domainKey.endsWith('.uk')) {
      resolvedCountry = 'Reino Unido (UK)';
      resolvedCurrency = 'GBP (£)';
    }

    // 2. Register in Enterprise Registry (Declarative JSON)
    try {
      let reg: EnterpriseRegistryFile = { domains: {} };
      try {
        const raw = await fs.readFile(REGISTRY_PATH, 'utf-8');
        reg = JSON.parse(raw) as EnterpriseRegistryFile;
      } catch {
        // Fallback
      }

      reg.domains = reg.domains || {};
      reg.domains[domainKey] = {
        company_name: name,
        country_name: resolvedCountry,
        currency: resolvedCurrency.split(' ')[0],
        industry: sector,
        standard,
        description: description || `Expediente corporativo de ${name} (${domainKey}) inicializado.`,
      };

      await fs.writeFile(REGISTRY_PATH, JSON.stringify(reg, null, 2), 'utf-8');
    } catch (regErr: unknown) {
      console.warn('Warning: Enterprise registry write error:', regErr instanceof Error ? regErr.message : String(regErr));
    }

    // 3. Create Seed Actuarial Model and Payload
    const fairModel = {
      ale_mean: 95000.0,
      ale_formatted: `95.000,00 ${resolvedCurrency.split(' ')[0]}`,
      p95_loss: 250000.0,
      iterations: 5000,
      currency: resolvedCurrency.split(' ')[0],
      sector,
      standard,
    };
    await fs.writeFile(path.join(clientSimDir, 'fair_actuarial_model.json'), JSON.stringify(fairModel, null, 2));

    const approvedPayload = {
      client_name: name,
      client_slug: slug,
      industry: sector,
      currency: resolvedCurrency.split(' ')[0],
      executive_summary: description || `Global assessment initiated for ${name} under ${standard}.`,
      overall_maturity_score: 2.8,
      maturity_band: 'Definido (Level 2)',
      total_calculated_ale: 95000.0,
      ale_formatted: `95.000,00 ${resolvedCurrency.split(' ')[0]}`,
      towers: [],
    };
    await fs.writeFile(path.join(clientSimDir, 'APPROVED_AST_PAYLOAD.json'), JSON.stringify(approvedPayload, null, 2));

    // 4. Update Summary Index if present
    let summaryData: SimulationSummaryItem[] = [];
    try {
      const rawSummary = await fs.readFile(SIMULATION_SUMMARY_PATH, 'utf-8');
      summaryData = JSON.parse(rawSummary) as SimulationSummaryItem[];
    } catch {
      summaryData = [];
    }

    const existingIndex = summaryData.findIndex((s) => s.client_slug === slug);
    const newEntry: SimulationSummaryItem = {
      client_slug: slug,
      company_name: name,
      country: resolvedCountry,
      currency: resolvedCurrency.split(' ')[0],
      industry: sector,
      standard,
      global_score: '2.8 / 5.0',
      global_band: 'Definido',
      ale_formatted: `€95,000/yr`,
      overall_fair_score: 2.8,
    };

    if (existingIndex >= 0) {
      summaryData[existingIndex] = newEntry;
    } else {
      summaryData.push(newEntry);
    }

    await fs.writeFile(SIMULATION_SUMMARY_PATH, JSON.stringify(summaryData, null, 2));

    return {
      success: true,
      message: `Expediente corporativo '${name}' inicializado correctamente.`,
      slug,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Error al provisionar empresa';
    console.error('Error creating client workspace:', message);
    return {
      success: false,
      message,
      error: message,
    };
  }
}
