'use server';

import fs from 'fs/promises';
import path from 'path';
import { getSessionUser } from '@/lib/auth/session';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const TRACE_PATH = path.join(REPO_ROOT, 'workspaces', 'live_trace.txt');

export async function readLiveTrace(): Promise<string> {
  const user = await getSessionUser();
  if (!user) {
    return 'Unauthorized: Session required.';
  }

  try {
    const content = await fs.readFile(TRACE_PATH, 'utf-8');
    const lines = content.split('\n').filter((l) => l.trim() !== '');
    if (lines.length > 0) {
      return lines[lines.length - 1];
    }
    return 'Analyzing context and refining plan...';
  } catch {
    return 'Exploring repository state...';
  }
}
