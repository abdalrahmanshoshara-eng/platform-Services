import { describe, expect, it } from 'vitest';
import type { PlatformService, UserSummary } from '@/shared/api/types';
import { serviceActionFor, serviceActionLabel } from '../serviceAction';

const service: PlatformService = {
  id: 1,
  name: 'منشئ التقارير',
  slug: 'report-builder',
  description: 'إنشاء تقرير',
  kind: 'internal',
  icon: 'file-text',
  accent: 'green',
  category: {
    id: 1,
    name: 'المستندات',
    slug: 'documents',
    description: '',
    icon: 'file-text',
    sort_order: 0,
  },
  is_available: true,
  restriction_reason: '',
};

const user: UserSummary = {
  id: 7,
  username: 'user',
  email: 'user@example.com',
  is_staff: false,
  is_superuser: false,
  is_active: true,
};

describe('serviceActionFor', () => {
  it('asks anonymous visitors to sign in even when the public catalog is visible', () => {
    expect(serviceActionFor(null, { ...service, is_available: false })).toBe('login');
    expect(serviceActionLabel('login', false)).toBe('سجّل الدخول للاستخدام');
  });

  it('launches only services available to the authenticated account', () => {
    expect(serviceActionFor(user, service)).toBe('launch');
    expect(serviceActionFor(user, { ...service, is_available: false })).toBe('unavailable');
  });
});
