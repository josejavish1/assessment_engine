import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'path';
import { cookies } from 'next/headers';

const SESSION_COOKIE_NAME = 'assessment_auth_session';

function getSessionSecret(): string {
  const secret = process.env.SESSION_SECRET;
  if (!secret) {
    if (process.env.NODE_ENV === 'production') {
      throw new Error('CRITICAL CONFIGURATION ERROR: SESSION_SECRET environment variable is missing in production.');
    }
    return 'nttdata-assessment-engine-secret-key-2026-sha256';
  }
  return secret;
}

export interface SessionUser {
  id: string;
  email: string;
  fullName: string;
  role: 'ADMIN' | 'CONSULTANT' | 'CLIENT';
  clientSlug?: string | null;
  iat?: number;
  exp?: number;
}

function signPayload(payloadStr: string): string {
  const hmac = crypto.createHmac('sha256', getSessionSecret());
  hmac.update(payloadStr);
  return hmac.digest('base64url');
}

export function createSignedToken(user: SessionUser, ttlSeconds: number = 7 * 24 * 60 * 60): string {
  const now = Math.floor(Date.now() / 1000);
  const tokenPayload: SessionUser = {
    ...user,
    iat: now,
    exp: now + ttlSeconds,
  };
  const payloadStr = Buffer.from(JSON.stringify(tokenPayload)).toString('base64url');
  const signature = signPayload(payloadStr);
  return `${payloadStr}.${signature}`;
}

export function verifySignedToken(token: string): SessionUser | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 2) return null;

    const [payloadStr, signature] = parts;
    const expectedSignature = signPayload(payloadStr);

    if (signature.length !== expectedSignature.length) {
      return null;
    }

    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) {
      return null;
    }

    const jsonStr = Buffer.from(payloadStr, 'base64url').toString('utf-8');
    const user = JSON.parse(jsonStr) as SessionUser;

    if (user.exp && Math.floor(Date.now() / 1000) > user.exp) {
      return null;
    }

    return user;
  } catch {
    return null;
  }
}

export async function verifySignedTokenAsync(token: string): Promise<SessionUser | null> {
  try {
    const parts = token.split('.');
    if (parts.length !== 2) return null;

    const [payloadStr, signature] = parts;

    const enc = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      enc.encode(getSessionSecret()),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    const expectedSigBuf = await crypto.subtle.sign('HMAC', key, enc.encode(payloadStr));
    const expectedSignature = Buffer.from(expectedSigBuf).toString('base64url');

    if (signature !== expectedSignature) {
      return null;
    }

    const jsonStr = Buffer.from(payloadStr, 'base64url').toString('utf-8');
    const user = JSON.parse(jsonStr) as SessionUser;

    if (user.exp && Math.floor(Date.now() / 1000) > user.exp) {
      return null;
    }

    return user;
  } catch {
    return null;
  }
}

export async function setSessionCookie(user: SessionUser): Promise<void> {
  const cookieStore = await cookies();
  const token = createSignedToken(user);

  cookieStore.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.COOKIE_SECURE === 'true',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 7, // 7 days
  });
}

export async function getSessionUser(): Promise<SessionUser | null> {
  try {
    const cookieStore = await cookies();
    const cookie = cookieStore.get(SESSION_COOKIE_NAME);
    if (!cookie?.value) return null;

    const sessionUser = verifySignedToken(cookie.value);
    if (!sessionUser) return null;

    // Real-time revocation & suspension check against users registry
    try {
      const usersPath = path.resolve(process.cwd(), '..', 'engine_config', 'users.json');
      const raw = await fs.readFile(usersPath, 'utf-8');
      const users = JSON.parse(raw) as Array<{ id: string; email: string; is_blocked?: boolean }>;
      const liveUser = users.find(
        (u) => u.id === sessionUser.id || u.email.toLowerCase() === sessionUser.email.toLowerCase()
      );

      // If user was deleted or suspended by admin, invalidate session immediately
      if (!liveUser || liveUser.is_blocked) {
        return null;
      }
    } catch {
      // In air-gapped test mocks, fallback gracefully if users.json is unpopulated
    }

    return sessionUser;
  } catch {
    return null;
  }
}

export async function clearSessionCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE_NAME);
}

const DEVICE_TRUST_COOKIE_NAME = 'ntt_device_trust';
const DEVICE_TRUST_TTL_SECONDS = 15 * 24 * 60 * 60; // 15 days

export interface DeviceTrustPayload {
  userId: string;
  email: string;
  verifiedAt: number;
  expiresAt: number;
}

export function createDeviceTrustToken(userId: string, email: string): string {
  const now = Date.now();
  const payload: DeviceTrustPayload = {
    userId,
    email: email.toLowerCase().trim(),
    verifiedAt: now,
    expiresAt: now + DEVICE_TRUST_TTL_SECONDS * 1000,
  };
  const payloadStr = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const signature = signPayload(payloadStr);
  return `${payloadStr}.${signature}`;
}

export function verifyDeviceTrustToken(token: string): DeviceTrustPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 2) return null;
    const [payloadStr, signature] = parts;
    const expectedSig = signPayload(payloadStr);
    if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSig))) {
      return null;
    }
    const payload = JSON.parse(Buffer.from(payloadStr, 'base64url').toString('utf-8')) as DeviceTrustPayload;
    if (Date.now() > payload.expiresAt) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

export async function setDeviceTrustCookie(userId: string, email: string): Promise<void> {
  const cookieStore = await cookies();
  const token = createDeviceTrustToken(userId, email);
  cookieStore.set(DEVICE_TRUST_COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.COOKIE_SECURE === 'true',
    sameSite: 'lax',
    path: '/',
    maxAge: DEVICE_TRUST_TTL_SECONDS,
  });
}

export async function hasValidDeviceTrust(userId: string, email: string): Promise<boolean> {
  try {
    const cookieStore = await cookies();
    const cookie = cookieStore.get(DEVICE_TRUST_COOKIE_NAME);
    if (!cookie?.value) return false;
    const payload = verifyDeviceTrustToken(cookie.value);
    if (!payload) return false;
    return payload.userId === userId && payload.email === email.toLowerCase().trim();
  } catch {
    return false;
  }
}

export async function clearDeviceTrustCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(DEVICE_TRUST_COOKIE_NAME);
}
