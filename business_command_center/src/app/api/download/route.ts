import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import { existsSync, realpathSync } from 'fs';
import path from 'path';

const REPO_ROOT = path.resolve(process.cwd(), '..');

const ALLOWED_ROOT_DIRS: readonly string[] = [
  path.resolve(REPO_ROOT, 'working', 'out'),
  path.resolve(REPO_ROOT, 'deliverables'),
];

const MIME_TYPES: Record<string, string> = {
  '.pdf': 'application/pdf',
  '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  '.json': 'application/json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

function isPathWithinAllowedRoots(targetPath: string): boolean {
  try {
    const realTarget = existsSync(targetPath)
      ? realpathSync(targetPath)
      : path.resolve(targetPath);

    return ALLOWED_ROOT_DIRS.some((allowedRoot) => {
      const resolvedRoot = existsSync(allowedRoot)
        ? realpathSync(allowedRoot)
        : path.resolve(allowedRoot);
      const relative = path.relative(resolvedRoot, realTarget);
      return (
        relative !== '' &&
        !relative.startsWith('..') &&
        !path.isAbsolute(relative)
      );
    });
  } catch {
    return false;
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const rawFileParam = searchParams.get('path') || searchParams.get('file');
  const viewMode = searchParams.get('view');

  if (!rawFileParam) {
    return NextResponse.json({ error: 'Missing path or file parameter' }, { status: 400 });
  }

  // Handle both relative paths to REPO_ROOT and absolute paths
  const candidatePath = path.isAbsolute(rawFileParam)
    ? path.normalize(rawFileParam)
    : path.resolve(REPO_ROOT, rawFileParam);

  if (!isPathWithinAllowedRoots(candidatePath)) {
    return NextResponse.json(
      { error: 'Access denied: Requested resource is outside authorized output boundaries.' },
      { status: 403 }
    );
  }

  try {
    const data = await fs.readFile(candidatePath);
    const fileName = path.basename(candidatePath);
    const ext = path.extname(fileName).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    // Magic-byte integrity verification for PDF deliverables
    if (ext === '.pdf') {
      const header = data.subarray(0, 5).toString('ascii');
      if (header !== '%PDF-') {
        return NextResponse.json(
          { error: 'Deliverable integrity failure: Invalid PDF magic header.' },
          { status: 500 }
        );
      }
    }

    const encodedFileName = encodeURIComponent(fileName);
    const disposition = (viewMode === 'inline')
      ? 'inline'
      : `attachment; filename="${fileName}"; filename*=UTF-8''${encodedFileName}`;

    return new Response(data, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': disposition,
        'Content-Length': data.length.toString(),
        'Cache-Control': 'no-store, max-age=0',
        'X-Content-Type-Options': 'nosniff',
      },
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message || 'File not found' }, { status: 404 });
  }
}
