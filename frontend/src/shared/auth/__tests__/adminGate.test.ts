import { describe, expect, it } from 'vitest';
import { adminGate } from '@/shared/auth/adminGate';
import type { UserSummary } from '@/shared/api/types';

const staff = { is_staff: true, is_superuser: false } as UserSummary;
const superuser = { is_staff: false, is_superuser: true } as UserSummary;
const normal = { is_staff: false, is_superuser: false } as UserSummary;

describe('adminGate', () => {
  it('waits while auth is still loading', () => {
    expect(adminGate(null, true)).toBe('checking');
    expect(adminGate(staff, true)).toBe('checking');
  });

  it('sends anonymous visitors to login', () => {
    expect(adminGate(null, false)).toBe('redirect-login');
  });

  it('sends authenticated non-admins to the user dashboard', () => {
    expect(adminGate(normal, false)).toBe('redirect-dashboard');
  });

  it('allows staff and superusers', () => {
    expect(adminGate(staff, false)).toBe('allowed');
    expect(adminGate(superuser, false)).toBe('allowed');
  });
});
