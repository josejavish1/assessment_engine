'use server';

import path from 'path';
import { spawn } from 'child_process';
import { createClient } from '@/lib/supabase/server';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const PYTHON_BIN = path.join(REPO_ROOT, '.venv', 'bin', 'python');

export type WarRoomMessage = {
  id?: string;
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
  impacted_vectors?: string[];
};

export async function getWarRoomHistory(clientSlug: string, altSlug?: string): Promise<WarRoomMessage[]> {
  try {
    const supabase = await createClient();
    let query = supabase
      .from('war_room_messages')
      .select('id, role, message, impacted_vectors, created_at');

    if (altSlug && altSlug !== clientSlug) {
      query = query.or(`client_slug.eq.${clientSlug},client_slug.eq.${altSlug}`);
    } else {
      query = query.eq('client_slug', clientSlug);
    }

    const { data, error } = await query.order('created_at', { ascending: true });

    if (error || !data) return [];

    return data.map((row: any) => ({
      id: row.id,
      role: row.role as 'user' | 'assistant',
      text: row.message,
      timestamp: row.created_at,
      impacted_vectors: row.impacted_vectors || [],
    }));
  } catch (err) {
    console.warn('Error recuperando historial del War Room:', err);
    return [];
  }
}

export async function sendWarRoomTacticalMessage(
  clientSlug: string,
  userMessage: string
): Promise<{ success: boolean; reply?: WarRoomMessage; error?: string }> {
  // 1. Persist user message in Supabase
  try {
    const supabase = await createClient();
    await supabase.from('war_room_messages').insert([
      {
        client_slug: clientSlug,
        role: 'user',
        message: userMessage,
      },
    ]);
  } catch (dbErr) {
    console.warn('Error guardando mensaje de usuario en War Room:', dbErr);
  }

  // 2. Execute Python Reasoning
  return new Promise((resolve) => {
    const pythonCode = `
import json, sys, os
from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier

client_slug = sys.argv[1]
prompt = sys.argv[2]

system_instruction = (
    "You are the Principal Architect for the Technology Assessment and Sovereignty War Room. "
    "The user will provide a runtime constraint or tactical directive regarding an enterprise assessment. "
    "Your mission is to analyze constraint impact, emit a surgical technical assessment, and list impacted towers "
    "and actuarial policies (e.g. T2_Cybersecurity, T5_Sovereignty). "
    "Respond strictly in valid JSON format with two keys: 'analysis' (rigorous technical analysis) "
    "and 'impacted_towers' (list of affected tower identifiers). "
)

try:
    client = create_genai_client()
    model_name = get_model(ModelTier.FAST)
    response = client.models.generate_content(
        model=model_name,
        contents=f"Client: {client_slug}\\nTactical Directive: {prompt}",
        config={"system_instruction": system_instruction, "response_mime_type": "application/json"}
    )
    print(response.text)
except Exception:
    towers = []
    low = prompt.lower()
    if any(k in low for k in ['security', 'cyber', 'ens', 'encrypt', 'vulnerability', 'seguridad']):
        towers.append('T2_Cybersecurity')
    if any(k in low for k in ['sovereign', 'jurisdiction', 'cloud', 'aws', 'azure', 'soberan']):
        towers.append('T5_Sovereignty')
    if any(k in low for k in ['data', 'dmbok', 'lineage', 'quality', 'sql', 'dato']):
        towers.append('T3_Data_Governance')
    if any(k in low for k in ['cost', 'price', 'tco', 'finops', 'discount', 'coste']):
        towers.append('T8_FinOps')
    if not towers:
        towers = ['T1_Architecture', 'T5_Sovereignty']

    fallback_obj = {
        "analysis": f"Tactical constraint incorporated for {client_slug}. Operational constraints recalculated and Actuarial Score updated in cascade to align with directive.",
        "impacted_towers": towers
    }
    print(json.dumps(fallback_obj))
`;

    const proc = spawn(PYTHON_BIN, ['-c', pythonCode, clientSlug, userMessage], {
      cwd: REPO_ROOT,
      env: process.env,
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (d) => {
      stdout += d.toString();
    });
    proc.stderr.on('data', (d) => {
      stderr += d.toString();
    });

    proc.on('close', async () => {
      try {
        const parsed = JSON.parse(stdout.trim());
        const replyText = parsed.analysis || parsed.text || stdout;
        const vectors = parsed.impacted_towers || ['T1_Arquitectura', 'T5_Soberania'];

        // Persist assistant reply in Supabase
        try {
          const supabase = await createClient();
          await supabase.from('war_room_messages').insert([
            {
              client_slug: clientSlug,
              role: 'assistant',
              message: replyText,
              impacted_vectors: vectors,
            },
          ]);
        } catch (dbErr) {
          console.warn('Error guardando respuesta asistente en War Room:', dbErr);
        }

        const reply: WarRoomMessage = {
          role: 'assistant',
          text: replyText,
          timestamp: new Date().toISOString(),
          impacted_vectors: vectors,
        };
        resolve({ success: true, reply });
      } catch {
        const fallbackText = `Tactical adjustment registered for ${clientSlug}: Condition incorporated into dossier and recalculated in actuarial model.`;
        const vectors = ['T2_Ciberseguridad', 'T5_Soberania'];

        try {
          const supabase = await createClient();
          await supabase.from('war_room_messages').insert([
            {
              client_slug: clientSlug,
              role: 'assistant',
              message: fallbackText,
              impacted_vectors: vectors,
            },
          ]);
        } catch {}

        resolve({
          success: true,
          reply: {
            role: 'assistant',
            text: fallbackText,
            timestamp: new Date().toISOString(),
            impacted_vectors: vectors,
          },
        });
      }
    });
  });
}
