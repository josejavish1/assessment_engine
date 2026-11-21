import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { getSessionUser } from '@/lib/auth/session';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const WORKSPACES_ROOT = path.join(REPO_ROOT, 'workspaces');

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB
const ALLOWED_EXTENSIONS = new Set([
  '.docx',
  '.txt',
  '.json',
  '.csv',
  '.pdf',
  '.xlsx',
  '.png',
  '.jpg',
  '.jpeg',
]);

export async function POST(req: NextRequest) {
  try {
    const user = await getSessionUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized: Authentication session required' }, { status: 401 });
    }

    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    let clientSlug = (formData.get('client_slug') as string | null) || 'generic_client';

    // Tenant isolation: if user is CLIENT, strictly restrict to their own clientSlug
    if (user.role === 'CLIENT') {
      if (!user.clientSlug) {
        return NextResponse.json(
          { error: 'Forbidden: Client account is missing assigned tenant boundary.' },
          { status: 403 }
        );
      }
      clientSlug = user.clientSlug;
    }

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    // Enforce quota limit (50MB)
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return NextResponse.json(
        { error: 'File size exceeds maximum permitted quota (50MB).' },
        { status: 413 }
      );
    }

    // Enforce extension allowlist to prevent Stored XSS or executable ingestion
    const ext = path.extname(file.name).toLowerCase();
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      return NextResponse.json(
        { error: `File type '${ext}' is not authorized. Permitted: .docx, .txt, .json, .csv, .pdf, .xlsx, .png, .jpg` },
        { status: 415 }
      );
    }

    // Sanitize client slug and filename to prevent path traversal
    const safeSlug = clientSlug.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
    const baseName = path.basename(file.name, ext).replace(/[^a-zA-Z0-9_-]/g, '_');
    const safeName = `${baseName || 'evidence'}${ext}`;

    const evidenceDir = path.join(WORKSPACES_ROOT, safeSlug, 'evidence');
    await fs.mkdir(evidenceDir, { recursive: true });

    const targetPath = path.join(evidenceDir, safeName);
    const bytes = await file.arrayBuffer();
    await fs.writeFile(targetPath, Buffer.from(bytes));

    return NextResponse.json({
      success: true,
      filename: safeName,
      size: bytes.byteLength,
      targetPath,
      message: `Evidencia ${safeName} ingestada en workspaces/${safeSlug}/evidence`,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Error al procesar subida';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
