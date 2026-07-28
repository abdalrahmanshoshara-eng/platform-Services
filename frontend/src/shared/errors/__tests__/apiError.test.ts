import { describe, expect, it } from 'vitest';
import { ApiError, toMessage } from '../apiError';

describe('ApiError', () => {
  it('carries code/status/requestId', () => {
    const e = new ApiError('bad', { code: 'X', status: 400, requestId: 'r1' });
    expect(e.code).toBe('X');
    expect(e.status).toBe(400);
    expect(e.requestId).toBe('r1');
  });
  it('toMessage falls back for unknown errors', () => {
    expect(toMessage(null, 'fb')).toBe('fb');
    expect(toMessage(new ApiError('hi', { status: 500 }))).toBe('hi');
  });
});
