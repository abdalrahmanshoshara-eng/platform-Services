export type UserSummary = {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  is_superuser: boolean;
  is_active: boolean;
};

export type FieldSchema = {
  name: string;
  label_ar: string;
  type: 'text' | 'date' | 'textarea' | 'select' | 'number';
  required?: boolean;
  options?: string[];
  placeholder?: string;
  min_length?: number;
  max_length?: number;
};

export type ReportType = {
  id: number;
  name: string;
  slug: string;
  description: string;
  template_file: string;
  fields_schema: FieldSchema[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ReportStatus =
  | 'pending'
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type GeneratedReport = {
  id: number;
  report_type: ReportType;
  created_by: UserSummary;
  title: string;
  input_data: Record<string, string>;
  docx_file: string | null;
  pdf_file: string | null;
  status: ReportStatus;
  error_message: string;
  download_docx_url: string | null;
  download_pdf_url: string | null;
  created_at: string;
  updated_at: string;
};

export type ReportStatusPayload = {
  id: number;
  status: ReportStatus;
  error_message: string;
  attempts: number;
  download_docx_url: string | null;
  download_pdf_url: string | null;
  updated_at: string;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type DashboardStats = {
  total_reports: number;
  today_reports: number;
  report_types: number;
  completed_reports: number;
  failed_reports: number;
  latest_reports: GeneratedReport[];
};

export type ServiceCategory = {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  sort_order: number;
};

export type PlatformService = {
  id: number;
  name: string;
  slug: string;
  description: string;
  kind: 'internal' | 'external';
  icon: string;
  accent: 'green' | 'teal' | 'gold' | string;
  category: ServiceCategory;
  is_available: boolean;
  restriction_reason: string;
};

export type ServiceLaunch = {
  target: string;
  kind: 'internal' | 'external';
};

export const TERMINAL_STATUSES: ReportStatus[] = ['completed', 'failed', 'cancelled'];

export type AdminSummary = {
  users: number;
  active_users: number;
  services: number;
  active_services: number;
  reports: number;
  reports_last_24h: number;
  queued_jobs: number;
  failed_jobs: number;
};

export type AuditEvent = {
  id: number;
  actor: number | null;
  actor_name: string;
  action: string;
  target_type: string;
  target_id: string;
  outcome: string;
  request_id: string;
  ip_address: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type AdminDashboard = {
  summary: AdminSummary;
  recent_activity: AuditEvent[];
  job_statuses: { status: string; count: number }[];
};

export type AdminRestriction = {
  id: number;
  target_id: number;
  target_name: string;
  target_type: 'service';
  reason: string;
  starts_at: string | null;
  expires_at: string | null;
  created_at: string;
  is_expired: boolean;
};

export type AdminUser = UserSummary & {
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
  disabled_reason: string;
  reports_count: number;
  restrictions_count: number;
  restrictions?: AdminRestriction[];
};

export type AdminService = {
  id: number;
  name: string;
  slug: string;
  description: string;
  kind: 'internal' | 'external';
  launch_target: string;
  icon: string;
  accent: string;
  sort_order: number;
  requires_staff: boolean;
  is_active: boolean;
  category: number;
  category_name: string;
  disabled_reason: string;
  disabled_at: string | null;
  settings: Record<string, unknown>;
  restrictions_count: number;
  launches_count: number;
  created_at: string;
  updated_at: string;
};

export type AdminJob = {
  id: number;
  title: string;
  user: string;
  report_type_name: string;
  status: ReportStatus;
  attempts: number;
  task_id: string;
  error_message: string;
  queued_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
  duration_seconds: number | null;
};

export type AdminReportType = ReportType & {
  versions_count: number;
  reports_count: number;
};
