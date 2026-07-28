import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/shared/errors/apiError';
import {
  excelContactsErrorMessage,
  processExcelContacts,
  type ExcelContactsResult,
} from '@/features/excel-contacts/api';

const successPayload: ExcelContactsResult = {
  fileName: 'contacts-output.zip',
  zipBase64: 'UEsDBA==',
  summary: { totalRows: 1, validCount: 1, duplicateCount: 0, invalidCount: 0 },
  sourceSheetName: 'جهات الاتصال',
  previews: {
    valid: [{ 'الاسم الكامل': 'مستخدم تجريبي' }],
    duplicate: [],
    invalid: [],
  },
};

afterEach(() => {
  vi.unstubAllGlobals();
});

it('calls the authenticated Django processing endpoint and preserves the result model', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(successPayload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );
  vi.stubGlobal('fetch', fetchMock);
  const file = new File(['workbook'], 'contacts.xlsx');

  await expect(processExcelContacts(file, '963')).resolves.toEqual(successPayload);
  expect(fetchMock).toHaveBeenCalledWith(
    'http://localhost:8000/api/tools/excel-contacts/process/',
    expect.objectContaining({
      method: 'POST',
      credentials: 'include',
      body: expect.any(FormData),
    }),
  );
});

describe.each([
  [401, 'NOT_AUTHENTICATED', 'بيانات الاعتماد غير متوفرة.'],
  [403, 'SERVICE_ACCESS_DENIED', 'لا تملك صلاحية استخدام هذه الخدمة.'],
])('HTTP %i handling', (status, code, message) => {
  it('maps authorization errors without bypassing the shared API client', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ code, message }), {
          status,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    const error = await processExcelContacts(new File(['x'], 'contacts.xlsx'), '963').catch(
      (caught: unknown) => caught,
    );
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(status);
    expect(excelContactsErrorMessage(error)).toBe(message);
  });
});

it('shows safe validation errors and hides unknown client details', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          code: 'INVALID_WORKBOOK',
          message: 'ملف Excel تالف أو غير صالح.',
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } },
      ),
    ),
  );
  const validationError = await processExcelContacts(
    new File(['bad'], 'contacts.xlsx'),
    '963',
  ).catch((caught: unknown) => caught);

  expect(excelContactsErrorMessage(validationError)).toBe('ملف Excel تالف أو غير صالح.');
  expect(excelContactsErrorMessage(new Error('C:\\private\\parser failure'))).not.toContain(
    'private',
  );
});
