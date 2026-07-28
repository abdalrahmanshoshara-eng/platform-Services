import { describe, expect, it } from 'vitest';
import { TERMINAL_STATUSES } from '../types';

describe('report status', () => {
  it('marks terminal states', () => {
    expect(TERMINAL_STATUSES).toContain('completed');
    expect(TERMINAL_STATUSES).toContain('failed');
    expect(TERMINAL_STATUSES).toContain('cancelled');
    expect(TERMINAL_STATUSES).not.toContain('processing');
  });
});
