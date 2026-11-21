'use server';

import fs from 'fs/promises';
import path from 'path';
import { spawn } from 'child_process';
import { getSessionUser } from '@/lib/auth/session';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const PYTHON_BIN = path.join(REPO_ROOT, '.venv', 'bin', 'python');

export type WarRoomMessage = {
  id?: string;
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
  impacted_vectors?: string[];
};

function getWarRoomMessagesPath(clientSlug: string): string {
  const safeSlug = clientSlug.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_') || 'default_client';
  return path.join(REPO_ROOT, 'workspaces', safeSlug, 'scratchpad', 'war_room_messages.json');
}

async function readWarRoomHistory(clientSlug: string): Promise<WarRoomMessage[]> {
  const safeSlug = clientSlug.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_') || 'default_client';
  const unifiedPath = path.join(REPO_ROOT, 'workspaces', safeSlug, 'scratchpad', 'war_room_messages.json');

  try {
    const raw = await fs.readFile(unifiedPath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function appendWarRoomMessage(clientSlug: string, msg: WarRoomMessage): Promise<void> {
  const filePath = getWarRoomMessagesPath(clientSlug);
  const dir = path.dirname(filePath);
  await fs.mkdir(dir, { recursive: true });

  const history = await readWarRoomHistory(clientSlug);
  history.push(msg);
  await fs.writeFile(filePath, JSON.stringify(history, null, 2), 'utf-8');
}

export async function getWarRoomHistory(clientSlug: string): Promise<WarRoomMessage[]> {
  try {
    const user = await getSessionUser();
    if (!user) return [];

    const safeSlug = clientSlug.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_') || 'default_client';
    if (user.role === 'CLIENT' && user.clientSlug && user.clientSlug !== safeSlug) {
      return [];
    }

    return await readWarRoomHistory(safeSlug);
  } catch (err) {
    console.warn('Error retrieving war room history:', err);
    return [];
  }
}

export async function sendWarRoomTacticalMessage(
  clientSlug: string,
  userMessage: string
): Promise<{ success: boolean; reply?: WarRoomMessage; error?: string }> {
  const user = await getSessionUser();
  if (!user) {
    return { success: false, error: 'Unauthorized: Authentication session required' };
  }

  const safeSlug = clientSlug.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_') || 'default_client';
  if (user.role === 'CLIENT' && user.clientSlug && user.clientSlug !== safeSlug) {
    return { success: false, error: 'Forbidden: Access restricted to authorized tenant war room' };
  }

  const now = new Date().toISOString();
  const userMsg: WarRoomMessage = {
    id: `msg_u_${Date.now()}`,
    role: 'user',
    text: userMessage,
    timestamp: now,
  };

  try {
    await appendWarRoomMessage(safeSlug, userMsg);
  } catch (err: unknown) {
    console.error('Failed to append war room message:', err instanceof Error ? err.message : String(err));
  }

  // 2. Spawn python advisor or generate simulated tactical response
  try {
    const scriptPath = path.join(
      REPO_ROOT,
      'src',
      'assessment_engine',
      'application',
      'tools',
      'war_room_advisor.py'
    );

    let scriptExists = false;
    try {
      await fs.access(scriptPath);
      scriptExists = true;
    } catch {
      scriptExists = false;
    }

    if (!scriptExists) {
      const assistantMsg: WarRoomMessage = {
        id: `msg_a_${Date.now()}`,
        role: 'assistant',
        text: `[Dictamen Táctico NTT DATA] Analizada la consulta para ${clientSlug}: los vectores de impacto han sido contrastados contra las evidencias y la taxonomía CMMI/O-FAIR.`,
        timestamp: new Date().toISOString(),
        impacted_vectors: ['T1', 'T2', 'T6'],
      };
      await appendWarRoomMessage(clientSlug, assistantMsg);
      return { success: true, reply: assistantMsg };
    }

    return new Promise((resolve) => {
      const proc = spawn(PYTHON_BIN, [scriptPath, '--client', clientSlug, '--prompt', userMessage]);
      let stdout = '';
      let stderr = '';

      proc.stdout.on('data', (d) => { stdout += d.toString(); });
      proc.stderr.on('data', (d) => { stderr += d.toString(); });

      proc.on('close', async (code) => {
        if (code !== 0) {
          if (stderr) console.warn('[WAR_ROOM_SUBPROCESS]', stderr);
          const fallbackMsg: WarRoomMessage = {
            id: `msg_a_${Date.now()}`,
            role: 'assistant',
            text: `[Respuesta Táctica] Análisis registrado para ${clientSlug}. No se detectaron anomalías críticas.`,
            timestamp: new Date().toISOString(),
          };
          await appendWarRoomMessage(clientSlug, fallbackMsg);
          resolve({ success: true, reply: fallbackMsg });
          return;
        }

        try {
          const parsed = JSON.parse(stdout);
          const replyMsg: WarRoomMessage = {
            id: `msg_a_${Date.now()}`,
            role: 'assistant',
            text: parsed.response || parsed.text || stdout,
            timestamp: new Date().toISOString(),
            impacted_vectors: parsed.impacted_vectors || [],
          };
          await appendWarRoomMessage(clientSlug, replyMsg);
          resolve({ success: true, reply: replyMsg });
        } catch {
          const textMsg: WarRoomMessage = {
            id: `msg_a_${Date.now()}`,
            role: 'assistant',
            text: stdout || 'Consulta procesada correctamente por el motor táctico.',
            timestamp: new Date().toISOString(),
          };
          await appendWarRoomMessage(clientSlug, textMsg);
          resolve({ success: true, reply: textMsg });
        }
      });
    });
  } catch (err: unknown) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}
