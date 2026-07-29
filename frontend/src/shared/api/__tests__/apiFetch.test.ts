import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiFetch } from '@/shared/api/client';
import { ApiError } from '@/shared/errors/apiError';

type FetchInit = { method?: string; headers: Headers; credentials?: string; body?: unknown };

function jsonResponse(body: unknown, { ok = true, status = 200 } = {}): Response {
  return {
    ok,
    status,
    headers: { get: (h: string) => (h.toLowerCase() === 'content-type' ? 'application/json' : null) },
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response;
}

function lastInit(mock: ReturnType<typeof vi.fn>): FetchInit {
  return mock.mock.calls[mock.mock.calls.length - 1][1] as FetchInit;
}

describe('apiFetch', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async () => jsonResponse({ ok: true }));
    vi.stubGlobal('fetch', fetchMock);
    // node test environment has no document; provide a cookie jar for CSRF reads.
    vi.stubGlobal('document', { cookie: 'csrftoken=tok-123; other=x' } as Document);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sends credentials and no CSRF header on GET', async () => {
    await apiFetch('/services/');
    const init = lastInit(fetchMock);
    expect(init.method).toBe('GET');
    expect(init.credentials).toBe('include');
    expect(init.headers.get('X-CSRFToken')).toBeNull();
  });

  it('adds X-CSRFToken and JSON Content-Type on unsafe JSON requests', async () => {
    await apiFetch('/reports/', { method: 'POST', body: { title: 'x' } });
    const init = lastInit(fetchMock);
    expect(init.method).toBe('POST');
    expect(init.credentials).toBe('include');
    expect(init.headers.get('X-CSRFToken')).toBe('tok-123');
    expect(init.headers.get('Content-Type')).toBe('application/json');
    expect(init.body).toBe(JSON.stringify({ title: 'x' }));
  });

  it('does not force Content-Type for FormData (lets the browser set the boundary)', async () => {
    const form = new FormData();
    form.append('file', 'data');
    await apiFetch('/tools/excel-contacts/process/', { method: 'POST', body: form });
    const init = lastInit(fetchMock);
    expect(init.headers.get('Content-Type')).toBeNull();
    expect(init.headers.get('X-CSRFToken')).toBe('tok-123');
    expect(init.body).toBe(form);
  });

  it('omits CSRF header when no csrftoken cookie is present', async () => {
    vi.stubGlobal('document', { cookie: 'other=x' } as Document);
    await apiFetch('/reports/', { method: 'POST', body: {} });
    expect(lastInit(fetchMock).headers.get('X-CSRFToken')).toBeNull();
  });

  it('normalizes an error response into a typed ApiError', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        { code: 'SERVICE_ACCESS_DENIED', message: 'ممنوع', request_id: 'rid-9', details: { field: ['bad'] } },
        { ok: false, status: 403 },
      ),
    );
    await expect(apiFetch('/services/x/launch/', { method: 'POST' })).rejects.toMatchObject({
      name: 'ApiError',
      status: 403,
      code: 'SERVICE_ACCESS_DENIED',
      requestId: 'rid-9',
    });
  });

  it('throws ApiError instances (so callers can branch on type)', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ message: 'boom' }, { ok: false, status: 500 }));
    const error = await apiFetch('/reports/').catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
  });
});
