import { z } from 'zod';
import { getSessionUser, type SessionUser } from '@/lib/auth/session';

export type UserRole = 'ADMIN' | 'CONSULTANT' | 'CLIENT';

export type SafeActionResult<T> =
  | { success: true; data: T; error?: never }
  | { success: false; error: string; data?: never };

export interface ActionContext {
  user: SessionUser;
}

export interface SafeActionOptions {
  roles?: UserRole[];
  enforceTenantScope?: boolean;
}

/**
 * Higher-order Server Action wrapper implementing the Tier-1 Safe Action pattern.
 * Enforces Zod schema validation, session authentication, RBAC, and multi-tenant scoping.
 */
export function createSafeAction<TInput, TOutput>(
  schema: z.ZodType<TInput>,
  handler: (input: TInput, ctx: ActionContext) => Promise<TOutput>,
  options: SafeActionOptions = {}
) {
  return async (rawInput: unknown): Promise<SafeActionResult<TOutput>> => {
    try {
      // 1. Session authentication
      const user = await getSessionUser();
      if (!user) {
        return { success: false, error: 'Unauthorized: Authentication session required.' };
      }

      // 2. Role-Based Access Control (RBAC)
      if (options.roles && options.roles.length > 0) {
        if (!options.roles.includes(user.role)) {
          return {
            success: false,
            error: `Forbidden: Operation requires ${options.roles.join(' or ')} privileges.`,
          };
        }
      }

      // 3. Zod schema input validation
      const parseResult = schema.safeParse(rawInput);
      if (!parseResult.success) {
        const errorMsg = parseResult.error.issues
          .map((i) => `${i.path.join('.') || 'input'}: ${i.message}`)
          .join('; ');
        return { success: false, error: `Validation failed: ${errorMsg}` };
      }

      // 4. Multi-Tenant isolation
      if (options.enforceTenantScope && user.role === 'CLIENT') {
        const inputObj = parseResult.data as Record<string, unknown>;
        const requestedSlug = (inputObj?.clientSlug || inputObj?.slug) as string | undefined;
        if (requestedSlug && user.clientSlug && requestedSlug !== user.clientSlug) {
          return {
            success: false,
            error: 'Forbidden: Access restricted to authorized tenant resources.',
          };
        }
      }

      // 5. Execute handler
      const result = await handler(parseResult.data, { user });
      return { success: true, data: result };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Internal server error occurred.';
      console.error('[SAFE_ACTION_ERROR]', message);
      return { success: false, error: message };
    }
  };
}

/**
 * Safe query wrapper for parameterless Server Actions.
 */
export function createSafeQuery<TOutput>(
  handler: (ctx: ActionContext) => Promise<TOutput>,
  options: SafeActionOptions = {}
) {
  return async (): Promise<SafeActionResult<TOutput>> => {
    try {
      const user = await getSessionUser();
      if (!user) {
        return { success: false, error: 'Unauthorized: Authentication session required.' };
      }

      if (options.roles && options.roles.length > 0) {
        if (!options.roles.includes(user.role)) {
          return {
            success: false,
            error: `Forbidden: Operation requires ${options.roles.join(' or ')} privileges.`,
          };
        }
      }

      const result = await handler({ user });
      return { success: true, data: result };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Internal query error occurred.';
      console.error('[SAFE_QUERY_ERROR]', message);
      return { success: false, error: message };
    }
  };
}
