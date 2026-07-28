'use client';

import { useEffect, useState } from 'react';
import { abortRequest, apiFetch, isAbortError } from '@/shared/api/client';
import { toMessage } from '@/shared/errors/apiError';
import type { DashboardStats } from '@/shared/api/types';

export function useDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    apiFetch<DashboardStats>('/dashboard/stats/', { signal: controller.signal })
      .then(setStats)
      .catch((err) => {
        if (!isAbortError(err, controller.signal)) setError(toMessage(err, 'تعذر تحميل الإحصاءات.'));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => abortRequest(controller);
  }, []);

  return { stats, loading, error };
}
