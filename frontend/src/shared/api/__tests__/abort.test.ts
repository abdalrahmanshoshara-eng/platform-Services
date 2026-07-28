import { describe, expect, it } from 'vitest';
import { abortRequest, isAbortError } from '@/shared/api/client';

describe('request cancellation', () => {
  it('aborts with an explicit AbortError reason', () => {
    const controller = new AbortController();

    abortRequest(controller);

    expect(controller.signal.aborted).toBe(true);
    expect(controller.signal.reason).toBeInstanceOf(DOMException);
    expect(controller.signal.reason.name).toBe('AbortError');
    expect(isAbortError(controller.signal.reason, controller.signal)).toBe(true);
  });

  it('does not classify normal errors as aborts', () => {
    expect(isAbortError(new Error('network failed'))).toBe(false);
  });
});
