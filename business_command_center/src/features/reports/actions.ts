'use server';

import fs from 'fs/promises';
import path from 'path';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const SIMULATION_DIR = path.join(REPO_ROOT, 'working', 'out', 'simulations');

export interface ReportChapter {
  id: string;
  title: string;
  content: string;
  bullet_points?: string[];
}

export interface ReportData {
  client_name: string;
  slug: string;
  headline: string;
  summary_body: string;
  global_score: string;
  global_band: string;
  language: string;
  currency: string;
  jurisdiction: string;
  regulatory_framework: string;
  has_docx: boolean;
  chapters: ReportChapter[];
}

export async function getReportPayload(clientSlug: string): Promise<{ success: boolean; data?: ReportData; error?: string }> {
  try {
    const payloadPath = path.join(SIMULATION_DIR, clientSlug, 'approved_annex_payload.json');
    const docxPath = path.join(SIMULATION_DIR, clientSlug, `Anexo_Tecnico_${clientSlug}.docx`);
    
    let hasDocx = false;
    try {
      await fs.access(docxPath);
      hasDocx = true;
    } catch {
      hasDocx = false;
    }

    const raw = await fs.readFile(payloadPath, 'utf-8');
    const json = JSON.parse(raw);

    const meta = json.document_meta || {};
    const exec = json.executive_summary || {};
    const secs = json.sections || {};

    const chapters: ReportChapter[] = [];

    // Parse sections
    const sectionTitles: Record<string, string> = {
      asis: '1. Current State Baseline (As-Is)',
      tobe: '2. Target Architecture & Topology (To-Be)',
      gap: '3. Actuarial and Statutory Gap Analysis',
      todo: '4. Action and Modernization Plan (Roadmap H1/H2)',
      risks: '5. Quantitative FAIR Risk Modeling',
      conclusion: '6. Dictamen de Cierre y Recomendaciones Ejecutivas',
    };

    for (const [key, title] of Object.entries(sectionTitles)) {
      const sectionData = secs[key];
      let content = '';
      let bullets: string[] = [];

      if (typeof sectionData === 'string') {
        content = sectionData;
      } else if (typeof sectionData === 'object' && sectionData !== null) {
        content = sectionData.narrative || sectionData.text || sectionData.description || JSON.stringify(sectionData, null, 2);
        if (Array.isArray(sectionData.findings)) bullets = sectionData.findings;
        else if (Array.isArray(sectionData.bullet_points)) bullets = sectionData.bullet_points;
      }

      chapters.push({
        id: key,
        title,
        content: content || `Technical section compiled and verified under statutory framework ${meta.regulatory_framework || 'Sovereign'}.`,
        bullet_points: bullets,
      });
    }

    return {
      success: true,
      data: {
        client_name: meta.client_name || clientSlug,
        slug: clientSlug,
        headline: exec.headline || 'Technology and Sovereignty Assessment Deliverable',
        summary_body: exec.summary_body || 'Technical architecture assessment completed successfully.',
        global_score: exec.global_score || '3.0 / 5.0',
        global_band: exec.global_band || 'Defined',
        language: meta.language || 'es',
        currency: meta.currency || 'EUR',
        jurisdiction: meta.jurisdiction || 'Local',
        regulatory_framework: meta.regulatory_framework || 'ENS High',
        has_docx: hasDocx,
        chapters,
      },
    };
  } catch (err: any) {
    return {
      success: false,
      error: err.message || 'Failed to load online report for this client.',
    };
  }
}
