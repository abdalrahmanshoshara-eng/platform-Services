'use client';

import { useState } from 'react';
import { apiFetch } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import { useAuth } from '@/shared/auth/AuthContext';
import { toMessage } from '@/shared/errors/apiError';
import type { UserSummary } from '@/shared/api/types';

export function useLogin() {
  const { refresh } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function login(username: string, password: string): Promise<UserSummary | null> {
    setLoading(true);
    setError('');
    try {
      const response = await apiFetch<{ user: UserSummary }>(API_ENDPOINTS.auth.login, {
        method: 'POST',
        body: { username, password },
      });
      await refresh(); // populate auth state from the cookie session
      return response.user;
    } catch (err) {
      setError(toMessage(err, 'تعذر تسجيل الدخول.'));
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { login, loading, error };
}
