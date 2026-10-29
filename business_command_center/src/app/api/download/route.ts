import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const ALLOWED_DIR = path.join(REPO_ROOT, 'working', 'out', 'simulations');

export async function GET(req: NextRequest) {
  const filePath = req.nextUrl.searchParams.get('path');
  const viewMode = req.nextUrl.searchParams.get('view');

  if (!filePath) {
    return NextResponse.json({ error: 'Missing path parameter' }, { status: 400 });
  }

  const resolved = path.resolve(filePath);
  if (!resolved.startsWith(ALLOWED_DIR)) {
    return NextResponse.json({ error: 'Access denied: Path out of bounds' }, { status: 403 });
  }

  try {
    const data = await fs.readFile(resolved);
    const fileName = path.basename(resolved);
    const ext = path.extname(fileName).toLowerCase();

    let contentType = 'application/octet-stream';
    if (ext === '.docx') {
      contentType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    } else if (ext === '.json') {
      contentType = 'application/json';
    } else if (ext === '.png') {
      contentType = 'image/png';
    }

    const disposition = (viewMode === 'inline')
      ? 'inline'
      : `attachment; filename="${fileName}"`;

    return new Response(data, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': disposition,
        'Content-Length': data.length.toString(),
      },
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 404 });
  }
}
