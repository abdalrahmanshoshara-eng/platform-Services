# API contracts

Base: `/api`. Auth via HttpOnly cookies; unsafe methods require `X-CSRFToken`.

## Auth
- `POST /api/auth/login/` `{username,password}` → `200 {user}` + auth cookies.
- `POST /api/auth/refresh/` (refresh cookie) → `200` + rotated cookies.
- `POST /api/auth/logout/` → `200` + cleared cookies.
- `GET /api/auth/me/` → `200 {id,username,email,is_staff,is_superuser}`.

## Report types
- `GET /api/report-types/` → active types (all types for staff).
- `POST|PUT|DELETE /api/report-types/[{id}/]` → staff only.

## Reports
- `POST /api/reports/` `{report_type_id,title,input_data}` → **202** `{...,status:"queued"}`.
- `GET /api/reports/` → paginated; own reports (all for staff).
- `GET /api/reports/{id}/` → detail.
- `GET /api/reports/{id}/status/` → `{id,status,error_message,attempts,download_*_url,updated_at}`.
- `POST /api/reports/{id}/retry/` → **202** re-queued (failed reports).
- `GET /api/reports/{id}/download-docx|download-pdf/` → file stream (owner/staff only).

## Dashboard
- `GET /api/dashboard/stats/` → aggregated counts + latest reports.

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
`POST /api/reports/` returns `409 NO_ACTIVE_TEMPLATE` when no valid active version exists.

## Excel Contacts
- `POST /api/tools/excel-contacts/process/` (authenticated multipart:
  `file=.xlsx|.xls`, `countryCode`) → `200`
  `{fileName,zipBase64,summary,sourceSheetName,previews}`.
- The endpoint enforces the `whatsapp-contacts` service/category access policy, a
  10 MiB upload limit, bounded workbook dimensions, signature validation, and records
  `service.execute`; inputs and results are processed synchronously in memory and are not stored.

## Health
- `GET /health/live` → `{status:"ok"}`. `GET /health/ready` → `200/503` + `{checks}`.

## Error model
`{ "code": "...", "message": "...", "request_id": "...", "details?": {...} }` for all errors.
