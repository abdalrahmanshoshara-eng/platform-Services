export type ApiErrorBody = {
  code?: string;
  message?: string;
  request_id?: string;
  details?: unknown;
};

/** Normalized error thrown by the API client (mirrors the backend error model). */
export class ApiError extends Error {
  code: string;
  status: number;
  requestId?: string;
  details?: unknown;

  constructor(message: string, opts: { code?: string; status: number; requestId?: string; details?: unknown }) {
    super(message);
    this.name = 'ApiError';
    this.code = opts.code ?? 'ERROR';
    this.status = opts.status;
    this.requestId = opts.requestId;
    this.details = opts.details;
  }
}

export function toMessage(error: unknown, fallback = 'حدث خطأ غير متوقع.'): string {
  if (error instanceof ApiError) return error.message || fallback;
  if (error instanceof Error) return error.message || fallback;
  return fallback;
}
