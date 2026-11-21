import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const SESSION_COOKIE_NAME = 'assessment_auth_session';

function getEdgeSessionSecret(): string {
  const secret = process.env.SESSION_SECRET;
  if (!secret) {
    if (process.env.NODE_ENV === 'production') {
      throw new Error('CRITICAL: SESSION_SECRET is not configured in production.');
    }
    return 'nttdata-assessment-engine-secret-key-2026-sha256';
  }
  return secret;
}

interface SessionPayload {
  id: string;
  email: string;
  fullName: string;
  role: 'ADMIN' | 'CONSULTANT' | 'CLIENT';
  clientSlug?: string | null;
  iat?: number;
  exp?: number;
}

async function verifyEdgeToken(token: string): Promise<SessionPayload | null> {
  try {
    const parts = token.split('.');
    if (parts.length !== 2) return null;
    const [payloadStr, signature] = parts;

    const enc = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      enc.encode(getEdgeSessionSecret()),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    const expectedSigBuf = await crypto.subtle.sign('HMAC', key, enc.encode(payloadStr));

    let binary = '';
    const bytes = new Uint8Array(expectedSigBuf);
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    const expectedSig = btoa(binary)
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    if (signature !== expectedSig) {
      return null;
    }

    const base64 = payloadStr.replace(/-/g, '+').replace(/_/g, '/');
    const jsonStr = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    const payload = JSON.parse(jsonStr) as SessionPayload;

    if (payload.exp && Math.floor(Date.now() / 1000) > payload.exp) {
      return null;
    }

    return payload;
  } catch {
    return null;
  }
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protect sensitive API routes
  if (pathname.startsWith('/api/')) {
    const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME);
    if (!sessionCookie?.value) {
      return NextResponse.json(
        { error: 'Unauthorized: Authentication session required' },
        { status: 401 }
      );
    }

    const user = await verifyEdgeToken(sessionCookie.value);
    if (!user) {
      const response = NextResponse.json(
        { error: 'Unauthorized: Invalid or expired session' },
        { status: 401 }
      );
      response.cookies.delete(SESSION_COOKIE_NAME);
      return response;
    }

    if (pathname.startsWith('/api/pipeline') && user.role === 'CLIENT') {
      return NextResponse.json(
        { error: 'Forbidden: Pipeline simulation requires NTT DATA Consultant or Admin privileges' },
        { status: 403 }
      );
    }
  }

  // Redirect legacy routes to unified root cockpit
  if (
    pathname === '/login' ||
    pathname === '/admin' ||
    pathname === '/company' ||
    pathname === '/portal'
  ) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/api/:path*',
    '/login',
    '/admin',
    '/company',
    '/portal',
  ],
};
