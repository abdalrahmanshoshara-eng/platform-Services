# API contracts

Canonical base: `/api/v1`. Auth uses HttpOnly cookies; unsafe methods require
`X-CSRFToken`. Existing `/api/...` application routes remain temporary deprecated aliases
to the same views. New clients must use `/api/v1/...`; alias removal will be planned only
after consumers have migrated (no removal date is currently scheduled). Health routes are
not API-versioned.

## Auth
- `POST /api/v1/auth/login/` `{username,password}` → `200 {user}` + auth cookies.
- `POST /api/v1/auth/refresh/` (refresh cookie) → `200` + rotated cookies.
- `POST /api/v1/auth/logout/` → `200` + cleared cookies.
- `GET /api/v1/auth/me/` → `200 {id,username,email,is_staff,is_superuser}`.

## Report types
- `GET /api/v1/report-types/` → active types (all types for staff).
- `POST|PUT|DELETE /api/v1/report-types/[{id}/]` → staff only.

## Reports
- `POST /api/v1/reports/` `{report_type_id,title,input_data}` → **202** `{...,status:"queued"}`.
- `GET /api/v1/reports/` → paginated; own reports (all for staff).
- `GET /api/v1/reports/{id}/` → detail.
- `GET /api/v1/reports/{id}/status/` → `{id,status,error_message,attempts,download_*_url,updated_at}`.
- `POST /api/v1/reports/{id}/retry/` → **202** re-queued (failed reports).
- `GET /api/v1/reports/{id}/download-docx|download-pdf/` → file stream (owner/staff only).

## Dashboard
- `GET /api/v1/dashboard/stats/` → aggregated counts + latest reports.

## Admin template versions
All endpoints require a platform administrator and live below `/api/v1/admin`.

- `GET /report-types/{report_type_id}/template-versions/` → version metadata, newest first.
- `POST /report-types/{report_type_id}/template-versions/` multipart
  `template_file=.docx` → `201` draft version. Upload is size/signature/ZIP bounded and
  rejects traversal, bombs, macros/executables, embedded OLE/packages, external
  relationships, XML entities, and malformed DOCX packages.
- `GET /report-types/{report_type_id}/template-versions/{id}/` → metadata and validation state.
- `POST .../{id}/validate/` → validates schema/placeholders and records a checksum.
- `POST .../{id}/activate/` → atomically makes the validated version the sole active version.
- `POST .../{id}/deactivate/` → makes an active version unavailable for new reports.
- `POST .../{id}/archive/` → archives a non-active version without deleting its file/history.

Lifecycle actions accept optional `{reason}` and write audit events. Template-version
`PATCH`/`DELETE` are unsupported; `ReportType.template_file` is read-only in the admin API.
`POST /api/v1/reports/` returns `409 NO_ACTIVE_TEMPLATE` when no valid active version exists.

## Excel Contacts
- `POST /api/v1/tools/excel-contacts/process/` (authenticated multipart:
  `file=.xlsx|.xls`, `countryCode`) → `200`
  `{fileName,zipBase64,summary,sourceSheetName,previews}`.
- The endpoint enforces the `whatsapp-contacts` service/category access policy, a
  10 MiB upload limit, bounded workbook dimensions, signature validation, and records
  `service.execute`; inputs and results are processed synchronously in memory and are not stored.

## Health
- `GET /health/live` → `{status:"ok"}`. `GET /health/ready` → `200/503` + `{checks}`.

## Error model
`{ "code": "...", "message": "...", "request_id": "...", "details?": {...} }` for all errors.
