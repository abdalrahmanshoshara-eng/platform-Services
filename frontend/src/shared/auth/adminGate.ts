import type { UserSummary } from '@/shared/api/types';

export type AdminGate = 'checking' | 'redirect-login' | 'redirect-dashboard' | 'allowed';

/**
 * Pure admin-access decision shared by the AdminChrome guard for both its redirect
 * effect and its render guard, so the two can never disagree.
 *
 * This drives UX only — the backend remains the authoritative gate (every admin_api
 * view declares `IsPlatformAdmin`; see ADR-009 / backlog B8).
 */
export function adminGate(user: UserSummary | null, loading: boolean): AdminGate {
  if (loading) return 'checking';
  if (!user) return 'redirect-login';
  if (!user.is_staff && !user.is_superuser) return 'redirect-dashboard';
  return 'allowed';
}
