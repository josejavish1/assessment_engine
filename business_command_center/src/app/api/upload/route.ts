import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const SOURCE_DOCS_ROOT = path.join(REPO_ROOT, 'source_docs');

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    const clientSlug = (formData.get('client_slug') as string | null) || 'generic_client';

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    // Sanitize client slug and filename to prevent path traversal
    const safeSlug = clientSlug.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
    const safeName = path.basename(file.name).replace(/[^a-zA-Z0-9._-]/g, '_');

    const clientDir = path.join(SOURCE_DOCS_ROOT, safeSlug);
    await fs.mkdir(clientDir, { recursive: true });

    const targetPath = path.join(clientDir, safeName);
    const bytes = await file.arrayBuffer();
    await fs.writeFile(targetPath, Buffer.from(bytes));

    return NextResponse.json({
      success: true,
      filename: safeName,
      size: bytes.byteLength,
      targetPath,
      message: `Evidencia ${safeName} ingestada en source_docs/${safeSlug}`,
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message || 'Error al procesar subida' }, { status: 500 });
  }
}
