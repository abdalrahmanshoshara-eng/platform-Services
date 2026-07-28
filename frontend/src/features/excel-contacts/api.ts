import { apiFetch } from '@/shared/api/client';
import { API_ENDPOINTS } from '@/shared/api/endpoints';
import { ApiError } from '@/shared/errors/apiError';

export type ExcelContactPreviewRow = Record<string, string | number | null>;

export type ExcelContactsResult = {
  fileName: string;
  zipBase64: string;
  summary: {
    totalRows: number;
    validCount: number;
    duplicateCount: number;
    invalidCount: number;
  };
  sourceSheetName: string;
  previews: {
    valid: ExcelContactPreviewRow[];
    duplicate: ExcelContactPreviewRow[];
    invalid: ExcelContactPreviewRow[];
  };
};

export function processExcelContacts(file: File, countryCode: string): Promise<ExcelContactsResult> {
  const body = new FormData();
  body.append('file', file);
  body.append('countryCode', countryCode);
  return apiFetch<ExcelContactsResult>(API_ENDPOINTS.excelContacts.process, {
    method: 'POST',
    body,
  });
}

export function excelContactsErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.message) return error.message;
  return 'تعذّرت معالجة الملف. تحقق من الملف وصلاحية الوصول ثم حاول مجددًا.';
}
