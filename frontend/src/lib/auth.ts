// Deprecated (Phase 8). Auth now uses HttpOnly cookies + AuthProvider.
// These stubs remain only so old imports do not break; they are no-ops.
export function getAccessToken(): string | null {
  return null;
}
export function saveAuth(): void {}
export function logoutLocal(): void {}
export function getStoredUser(): null {
  return null;
}
