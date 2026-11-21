import { getSessionUser } from '@/lib/auth/session';
import { getSimulationSummary } from '@/app/actions/assessment';
import { NttDataAuthGate, type AuthUser } from '@/components/NttDataAuthGate';
import { UnifiedCockpitClient } from '@/components/UnifiedCockpitClient';

interface PageProps {
  searchParams: Promise<{
    view?: string;
    client?: string;
    tab?: string;
  }>;
}

/**
 * Root Executive Cockpit (React Server Component - Next.js 16).
 * Pre-hydrates server session and simulation metadata before emitting HTML to the client.
 */
export default async function Page({ searchParams }: PageProps) {
  const sessionUser = await getSessionUser();
  const params = await searchParams;

  if (!sessionUser) {
    return <NttDataAuthGate />;
  }

  const authUser: AuthUser = {
    id: sessionUser.id,
    email: sessionUser.email,
    fullName: sessionUser.fullName,
    role: sessionUser.role,
    clientSlug: sessionUser.clientSlug || undefined,
  };

  const summaryRes = await getSimulationSummary();
  const initialArchetypes = summaryRes.success && summaryRes.data ? summaryRes.data : [];

  return (
    <UnifiedCockpitClient
      initialUser={authUser}
      initialArchetypes={initialArchetypes}
      initialParams={params}
    />
  );
}
