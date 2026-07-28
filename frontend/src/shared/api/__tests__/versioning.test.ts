import { describe, expect, it } from 'vitest';
import { API_URL } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';

describe('canonical API routing', () => {
  it('uses the v1 API base and centralized relative endpoints', () => {
    expect(API_URL).toBe('http://localhost:8000/api/v1');
    expect(`${API_URL}${API_ENDPOINTS.auth.login}`).toContain('/api/v1/auth/login/');
    expect(`${API_URL}${API_ENDPOINTS.reports.list}`).toContain('/api/v1/reports/');
    expect(`${API_URL}${API_ENDPOINTS.services.list}`).toContain('/api/v1/services/');
    expect(`${API_URL}${API_ENDPOINTS.excelContacts.process}`).toContain(
      '/api/v1/tools/excel-contacts/process/',
    );
    expect(`${API_URL}${API_ENDPOINTS.admin.dashboard}`).toContain(
      '/api/v1/admin/dashboard/',
    );
  });
});
