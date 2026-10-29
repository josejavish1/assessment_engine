import { NextRequest } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const PYTHON_BIN = path.join(REPO_ROOT, '.venv', 'bin', 'python');
const SCRIPT_PATH = path.join(REPO_ROOT, 'scripts', 'simulate_multinational_archetypes.py');

export async function GET(req: NextRequest) {
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

      safeEnqueue(encoder.encode(`[${new Date().toLocaleTimeString()}] [PIPELINE] Dispatching actuarial simulation across all archetypes...\n`));

      proc.stdout.on('data', (chunk) => {
        safeEnqueue(chunk);
      });

      proc.stderr.on('data', (chunk) => {
        safeEnqueue(chunk);
      });

      proc.on('close', (code) => {
        if (code === 0) {
          safeEnqueue(encoder.encode(`\n[${new Date().toLocaleTimeString()}] [OK] Pipeline completado exitosamente. All los arquetipos y entregables actualizados.\n`));
        } else {
          safeEnqueue(encoder.encode(`\n[${new Date().toLocaleTimeString()}] [ERROR] Pipeline terminated with error code ${code}.\n`));
        }
        safeClose();
      });

      proc.on('error', (err) => {
        safeEnqueue(encoder.encode(`\n[${new Date().toLocaleTimeString()}] [ERROR] Execution error: ${err.message}\n`));
        safeClose();
      });
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
      'Cache-Control': 'no-cache, no-transform',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}
