import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import { getSessionUser } from '@/lib/auth/session';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const PYTHON_BIN = path.join(REPO_ROOT, '.venv', 'bin', 'python');
const SCRIPT_PATH = path.join(REPO_ROOT, 'scripts', 'simulate_multinational_archetypes.py');

export async function GET() {
  const user = await getSessionUser();
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized: Authentication session required' }, { status: 401 });
  }

  if (user.role === 'CLIENT') {
    return NextResponse.json(
      { error: 'Forbidden: Pipeline simulation requires NTT DATA Consultant or Admin privileges' },
      { status: 403 }
    );
  }

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      let isClosed = false;

      const safeEnqueue = (data: Uint8Array) => {
        if (!isClosed) {
          try {
            controller.enqueue(data);
          } catch {
            isClosed = true;
          }
        }
      };

      const safeClose = () => {
        if (!isClosed) {
          isClosed = true;
          try {
            controller.close();
          } catch {}
        }
      };

      const proc = spawn(PYTHON_BIN, [SCRIPT_PATH], {
        cwd: REPO_ROOT,
        env: process.env,
      });

      safeEnqueue(
        encoder.encode(
          `[${new Date().toLocaleTimeString()}] [PIPELINE] Dispatching actuarial simulation across all archetypes...\n`
        )
      );

      proc.stdout.on('data', (chunk) => {
        safeEnqueue(chunk);
      });

      proc.stderr.on('data', (chunk) => {
        safeEnqueue(chunk);
      });

      proc.on('close', (code) => {
        safeEnqueue(encoder.encode(`\n[${new Date().toLocaleTimeString()}] [PIPELINE] Execution completed with status code ${code}.\n`));
        safeClose();
      });

      proc.on('error', (err) => {
        safeEnqueue(encoder.encode(`\n[${new Date().toLocaleTimeString()}] [ERROR] Process spawn failure: ${err.message}\n`));
        safeClose();
      });
    },
  });

  return new NextResponse(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
      'Cache-Control': 'no-cache, no-transform',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}
