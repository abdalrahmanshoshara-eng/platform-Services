import { describe, expect, it } from 'vitest';
import { validateInput } from '../useCreateReport';
import type { FieldSchema } from '@/shared/api/types';

const fields: FieldSchema[] = [
  { name: 'org', label_ar: 'الجهة', type: 'text', required: true },
  { name: 'notes', label_ar: 'ملاحظات', type: 'textarea', required: false },
];

describe('validateInput', () => {
  it('flags missing required fields', () => {
    const errors = validateInput(fields, { notes: 'x' });
    expect(errors.org).toBeTruthy();
  });
  it('passes when required fields are present', () => {
    const errors = validateInput(fields, { org: 'Acme' });
    expect(Object.keys(errors)).toHaveLength(0);
  });
});
