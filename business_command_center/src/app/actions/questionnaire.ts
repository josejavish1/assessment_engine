'use server';

import fs from 'fs/promises';
import path from 'path';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const ENGINE_CONFIG_DIR = path.join(REPO_ROOT, 'engine_config');
const TOWERS_DIR = path.join(ENGINE_CONFIG_DIR, 'towers');
const QUESTIONS_JSON_PATH = path.join(ENGINE_CONFIG_DIR, 'questions_multilingual.json');
const TOWER_CATALOG_PATH = path.join(TOWERS_DIR, 'tower_catalog.json');
const RISK_MAP_PATH = path.join(ENGINE_CONFIG_DIR, 'taxonomy', 'universal_question_risk_map.json');

export interface QuestionOption {
  level: number;
  label: string;
  description: string;
}

export interface QuestionItem {
  questionId: string;
  kpiId: string;
  kpiName: string;
  textEn: string;
  textEs: string;
  options: QuestionOption[];
}

export interface PillarItem {
  pillarId: string;
  pillarName: string;
  weightPct: number;
  questions: QuestionItem[];
}

export interface TowerMetadata {
  towerId: string;
  towerName: string;
  canonicalCode: string;
  purpose: string;
  primaryStandard: string;
  complianceFramework: string;
  pillars: PillarItem[];
  totalQuestions: number;
}

export interface QuestionnaireBundle {
  towers: TowerMetadata[];
  totalQuestions: number;
}

export interface SavedQuestionResponse {
  score: number;
  comment?: string;
  updatedAt?: string;
}

export type QuestionnaireAnswers = Record<string, SavedQuestionResponse>;

/**
 * Loads and aggregates all 10 tower definitions along with bilingual question texts
 * and question-specific maturity options (Levels 1 to 5) from the universal risk map.
 */
interface QuestionLookupEntry {
  en?: string;
  es?: string;
  category?: string;
  [key: string]: unknown;
}

interface QuestionRiskEntry {
  question_text?: string;
  level_1_failure_mode?: string;
  level_2_vulnerability?: string;
  level_3_baseline?: string;
  level_4_measured?: string;
  level_5_optimized?: string;
  [key: string]: unknown;
}

interface TowerCatalogEntry {
  canonical_code?: string;
  name?: string;
  title?: string;
  description?: string;
  primary_engineering_standard?: string;
  regulatory_compliance_framework?: string;
  framework?: string;
  domain?: string;
  [key: string]: unknown;
}

export async function getQuestionnaireBundle(): Promise<QuestionnaireBundle> {
  let questionsLookup: Record<string, QuestionLookupEntry> = {};
  try {
    const rawQuestions = await fs.readFile(QUESTIONS_JSON_PATH, 'utf-8');
    questionsLookup = JSON.parse(rawQuestions);
  } catch (error) {
    console.error('Failed to load multilingual questions lookup:', error);
  }

  let catalogLookup: Record<string, TowerCatalogEntry> = {};
  try {
    const rawCatalog = await fs.readFile(TOWER_CATALOG_PATH, 'utf-8');
    catalogLookup = JSON.parse(rawCatalog);
  } catch (error) {
    console.error('Failed to load tower catalog:', error);
  }

  let riskMapLookup: Record<string, QuestionRiskEntry> = {};
  try {
    const rawRisk = await fs.readFile(RISK_MAP_PATH, 'utf-8');
    riskMapLookup = JSON.parse(rawRisk);
  } catch (error) {
    console.error('Failed to load universal question risk map:', error);
  }

  const towerCodes = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10'];
  const towers: TowerMetadata[] = [];
  let grandTotalQuestions = 0;

  for (const code of towerCodes) {
    const defPath = path.join(TOWERS_DIR, code, `tower_definition_${code}.json`);
    try {
      const rawDef = await fs.readFile(defPath, 'utf-8');
      const def = JSON.parse(rawDef);
      const catalogEntry = catalogLookup[code] || {};

      const pillars: PillarItem[] = [];
      let towerQuestionCount = 0;

      for (const p of def.pillars || []) {
        const pillarQuestions: QuestionItem[] = [];

        for (const k of p.kpis || []) {
          for (const q of k.questions || []) {
            const qid = q.question_id;
            const mult = questionsLookup[qid] || {};
            const riskEntry = riskMapLookup[qid] || {};

            const options: QuestionOption[] = [
              {
                level: 1,
                label: '1 - Inicial',
                description:
                  riskEntry.level_1_failure_mode ||
                  'Prácticas ad-hoc no estandarizadas o ausencia de evidencias formales.',
              },
              {
                level: 2,
                label: '2 - Gestionado',
                description:
                  riskEntry.level_2_vulnerability ||
                  'Controles operativos básicos y repetibles pero con brechas de automatización.',
              },
              {
                level: 3,
                label: '3 - Definido',
                description:
                  riskEntry.level_3_baseline ||
                  'Estándar formalizado, documentado y aplicado en la organización.',
              },
              {
                level: 4,
                label: '4 - Cuantitativo',
                description:
                  riskEntry.level_4_measured ||
                  'Medición continua con métricas, telemetría y revisiones periódicas.',
              },
              {
                level: 5,
                label: '5 - Optimizado',
                description:
                  riskEntry.level_5_optimized ||
                  'Automatización predictiva, resiliencia continua y optimización de capacidades.',
              },
            ];

            const item: QuestionItem = {
              questionId: qid,
              kpiId: k.kpi_id,
              kpiName: k.kpi_name || '',
              textEn: mult.en || q.question_text || '',
              textEs: riskEntry.question_text || mult.es || q.question_text || '',
              options,
            };
            pillarQuestions.push(item);
            towerQuestionCount++;
          }
        }

        pillars.push({
          pillarId: p.pillar_id,
          pillarName: p.pillar_name || '',
          weightPct: p.weight_pct || 0,
          questions: pillarQuestions,
        });
      }

      grandTotalQuestions += towerQuestionCount;

      towers.push({
        towerId: code,
        towerName: def.tower_name || `Domain ${code}`,
        canonicalCode: catalogEntry.canonical_code || code,
        purpose: def.purpose || '',
        primaryStandard: catalogEntry.primary_engineering_standard || 'Industry Best Practice',
        complianceFramework: catalogEntry.regulatory_compliance_framework || 'Governance Baseline',
        pillars,
        totalQuestions: towerQuestionCount,
      });
    } catch (err) {
      console.error(`Failed to load tower definition for ${code}:`, err);
    }
  }

  return {
    towers,
    totalQuestions: grandTotalQuestions,
  };
}

/**
 * Saves current questionnaire answers and generates canonical responses.txt
 */
export async function saveAssessmentResponses(
  clientSlug: string,
  answers: QuestionnaireAnswers
): Promise<{ success: boolean; formattedTxt: string; filePath?: string }> {
  const lines: string[] = [];
  const validSlugs = clientSlug.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_') || 'cliente';

  // Format canonical text output: T1.P1.K1.PR1 \t score
  // Sort questions by ID deterministically
  const sortedQids = Object.keys(answers).sort();
  for (const qid of sortedQids) {
    const item = answers[qid];
    if (item && typeof item.score === 'number' && !isNaN(item.score)) {
      lines.push(`${qid}\t${item.score.toFixed(1)}`);
    }
  }

  const formattedTxt = lines.join('\n');

  try {
    const clientWorkingDir = path.join(REPO_ROOT, 'workspaces', validSlugs, 'evidence');
    await fs.mkdir(clientWorkingDir, { recursive: true });

    // 1. Write responses.txt
    const responsesPath = path.join(clientWorkingDir, 'responses.txt');
    await fs.writeFile(responsesPath, formattedTxt, 'utf-8');

    // 2. Write full draft JSON (including comments)
    const draftPath = path.join(clientWorkingDir, 'questionnaire_answers.json');
    await fs.writeFile(draftPath, JSON.stringify(answers, null, 2), 'utf-8');

    // 3. Store user comments in a dedicated notes file for context ingestion
    const observations = Object.entries(answers)
      .filter(([, data]) => data.comment && data.comment.trim().length > 0)
      .map(([qid, data]) => `[${qid}] (Nota: ${data.score}/5): ${data.comment?.trim()}`);

    if (observations.length > 0) {
      const notesPath = path.join(clientWorkingDir, 'assessment_user_observations.txt');
      await fs.writeFile(notesPath, observations.join('\n\n'), 'utf-8');
    }

    return {
      success: true,
      formattedTxt,
      filePath: responsesPath,
    };
  } catch (err: unknown) {
    console.error('Error saving assessment responses:', err instanceof Error ? err.message : String(err));
    return {
      success: false,
      formattedTxt,
    };
  }
}

/**
 * Loads previously saved answers if they exist on disk.
 */
export async function loadSavedAssessmentResponses(clientSlug: string): Promise<QuestionnaireAnswers> {
  const validSlugs = clientSlug.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_') || 'cliente';
  const draftPath = path.join(REPO_ROOT, 'workspaces', validSlugs, 'evidence', 'questionnaire_answers.json');

  try {
    const raw = await fs.readFile(draftPath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return {};
  }
}
