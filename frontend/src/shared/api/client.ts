import { ApiError, type ApiErrorBody } from '@/shared/errors/apiError';

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function buildUrl(path: string): string {
  if (path.startsWith('http')) return path;
  return `${API_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export type ApiOptions = Omit<RequestInit, 'body'> & {
  body?: unknown;
  signal?: AbortSignal;
};

export function isAbortError(error: unknown, signal?: AbortSignal): boolean {
  if (signal?.aborted) return true;
  if (typeof DOMException !== 'undefined' && error instanceof DOMException) {
    return error.name === 'AbortError';
  }
  return error instanceof Error && error.name === 'AbortError';
}

export function abortRequest(controller: AbortController): void {
  if (!controller.signal.aborted) {
    controller.abort(new DOMException('Request cancelled during component cleanup.', 'AbortError'));
  }
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers || {});
  const isForm = options.body instanceof FormData;

  if (options.body !== undefined && !isForm) headers.set('Content-Type', 'application/json');
  if (UNSAFE_METHODS.has(method)) {
    const csrf = readCookie('csrftoken');
    if (csrf) headers.set('X-CSRFToken', csrf);
  }

  const response = await fetch(buildUrl(path), {
    ...options,
    method,
    headers,
    credentials: 'include', // send/receive HttpOnly auth cookies
    body: isForm ? (options.body as FormData) : options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await response.json().catch(() => null)
    : await response.text().catch(() => null);

  if (!response.ok) {
    const body = (data || {}) as ApiErrorBody;
    throw new ApiError(body.message || 'حدث خطأ في الطلب.', {
      code: body.code,
      status: response.status,
      requestId: body.request_id,
      details: body.details,
    });
  }

  return data as T;
}

/** Download a protected file via the API (streams through the permission check). */
export async function downloadFile(url: string, filename: string): Promise<void> {
  const response = await fetch(buildUrl(url), { credentials: 'include' });
  if (!response.ok) throw new ApiError('تعذر تحميل الملف.', { status: response.status });
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
