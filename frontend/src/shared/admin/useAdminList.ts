'use client';

import { useEffect, useState } from 'react';
import { abortRequest, apiFetch, isAbortError } from '@/shared/api/client';
import type { PaginatedResponse } from '@/shared/api/types';
import { toMessage } from '@/shared/errors/apiError';

export function useAdminList<T>(path: string, query: string) {
  const [data, setData] = useState<PaginatedResponse<T> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError('');
    apiFetch<PaginatedResponse<T>>(`${path}?${query}`, { signal: controller.signal })
      .then(setData)
      .catch((err) => {
        if (!isAbortError(err, controller.signal)) setError(toMessage(err, 'تعذر تحميل البيانات.'));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => abortRequest(controller);
  }, [path, query, reloadKey]);

  return { data, loading, error, reload: () => setReloadKey((value) => value + 1) };
}
