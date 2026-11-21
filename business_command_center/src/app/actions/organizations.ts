'use server';

import fs from 'fs/promises';
import path from 'path';
import { getSessionUser } from '@/lib/auth/session';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const REGISTRY_PATH = path.join(REPO_ROOT, 'engine_config', 'enterprise_registry.json');
const WORKSPACES_ROOT = path.join(REPO_ROOT, 'workspaces');

export interface OrganizationItem {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

interface DomainRecord {
  company_name?: string;
  country_code?: string;
  country_name?: string;
  currency?: string;
  industry?: string;
}

interface RegistryFile {
  domains?: Record<string, DomainRecord>;
}

export async function getOrganizations(): Promise<OrganizationItem[]> {
  try {
    const user = await getSessionUser();
    if (!user) return [];

    const raw = await fs.readFile(REGISTRY_PATH, 'utf-8');
    const reg = JSON.parse(raw) as RegistryFile;
    const domains = reg.domains || {};

    const items: OrganizationItem[] = [];
    const seenSlugs = new Set<string>();

    for (const [dom, data] of Object.entries(domains)) {
      const slug = dom.split('.')[0];
      if (!seenSlugs.has(slug)) {
        seenSlugs.add(slug);
        items.push({
          id: slug,
          name: data.company_name || slug,
          slug,
          created_at: '2026-01-01T00:00:00Z',
        });
      }
    }

    if (user.role === 'CLIENT' && user.clientSlug) {
      return items.filter((item) => item.slug === user.clientSlug);
    }

    return items;
  } catch (err: unknown) {
    console.error('Error reading organizations:', err instanceof Error ? err.message : String(err));
    return [];
  }
}

export async function createOrganization(name: string, slug: string): Promise<{ success: boolean; error?: string }> {
  const user = await getSessionUser();
  if (!user) {
    return { success: false, error: 'Unauthorized: Authentication session required' };
  }

  if (user.role === 'CLIENT') {
    return { success: false, error: 'Forbidden: Organization creation requires Consultant or Admin privileges' };
  }

  const safeSlug = slug.toLowerCase().trim().replace(/[^a-z0-9_-]/g, '_');
  if (!safeSlug || !name.trim()) {
    return { success: false, error: 'Datos de organización incompletos' };
  }

  try {
    let reg: RegistryFile = { domains: {} };
    try {
      const raw = await fs.readFile(REGISTRY_PATH, 'utf-8');
      reg = JSON.parse(raw) as RegistryFile;
    } catch {
      // Fallback
    }

    reg.domains = reg.domains || {};
    reg.domains[`${safeSlug}.com`] = {
      company_name: name.trim(),
      country_code: 'ES',
      country_name: 'Spain',
      currency: 'EUR',
      industry: 'technology',
    };

    await fs.writeFile(REGISTRY_PATH, JSON.stringify(reg, null, 2), 'utf-8');
    const tenantWorkspace = path.join(WORKSPACES_ROOT, safeSlug);
    await fs.mkdir(path.join(tenantWorkspace, 'evidence'), { recursive: true });
    await fs.mkdir(path.join(tenantWorkspace, 'scratchpad'), { recursive: true });
    await fs.mkdir(path.join(tenantWorkspace, 'deliverables'), { recursive: true });

    return { success: true };
  } catch (err: unknown) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}
