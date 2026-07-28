// Deprecated module path (Phase 8). Kept for backward compatibility.
// New code should import from '@/shared/api/client' and '@/shared/api/types'.
export { apiFetch as fetchApi, downloadFile, API_URL } from '@/shared/api/client';
export type {
  UserSummary,
  FieldSchema,
  ReportType,
  ReportStatus,
  GeneratedReport,
  ReportStatusPayload,
  PaginatedResponse,
  DashboardStats,
} from '@/shared/api/types';
