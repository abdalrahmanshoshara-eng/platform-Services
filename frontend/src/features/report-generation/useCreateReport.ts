'use client';

import { useState } from 'react';
import { apiFetch } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import { ApiError, toMessage } from '@/shared/errors/apiError';
import type { FieldSchema, GeneratedReport } from '@/shared/api/types';

export function validateInput(fields: FieldSchema[], data: Record<string, string>): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const field of fields) {
    if (field.required && !String(data[field.name] || '').trim()) {
      errors[field.name] = 'هذا الحقل مطلوب.';
    }
  }
  return errors;
}

export function useCreateReport() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function create(reportTypeId: number, title: string, inputData: Record<string, string>) {
    setSubmitting(true);
    setError('');
    setFieldErrors({});
    try {
      // 202 Accepted — generation runs in the background; caller polls status.
      return await apiFetch<GeneratedReport>(API_ENDPOINTS.reports.list, {
        method: 'POST',
        body: { report_type_id: reportTypeId, title, input_data: inputData },
      });
    } catch (err) {
      if (err instanceof ApiError && err.details && typeof err.details === 'object') {
        setFieldErrors(err.details as Record<string, string>);
      }
      setError(toMessage(err, 'فشل إرسال التقرير.'));
      return null;
    } finally {
      setSubmitting(false);
    }
  }

  return { create, submitting, error, fieldErrors };
}
