# API Reference

All browser requests use HttpOnly JWT cookies. Unsafe requests also require the CSRF
cookie value in `X-CSRFToken`. Admin endpoints require an authenticated staff or
superuser account and return `403` for regular users.
`/api/v1/` is canonical. The corresponding `/api/...` application paths are deprecated
compatibility aliases and must not be used by new clients.

## Authentication

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login/` | Create cookie session |
| GET | `/api/v1/auth/me/` | Current user |
| POST | `/api/v1/auth/refresh/` | Rotate session |
| POST | `/api/v1/auth/logout/` | Revoke and clear session |

## Admin dashboard and analytics

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/admin/dashboard/` | Counts, job statuses, recent activity |
| GET | `/api/v1/admin/analytics/?days=30` | Daily reports and service usage |

## Users

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/admin/users/` | Paginated search and filters |
| GET | `/api/v1/admin/users/{id}/` | User details and restrictions |
| POST | `/api/v1/admin/users/{id}/activate/` | Activate account |
| POST | `/api/v1/admin/users/{id}/deactivate/` | Deactivate with `reason` |
| POST | `/api/v1/admin/users/{id}/restrictions/` | Atomic bulk add/remove |

Restriction input:

```json
{
  "mode": "add",
  "service_ids": [1, 2],
  "starts_at": "2026-07-25T12:00:00+03:00",
  "expires_at": "2026-08-01T12:00:00+03:00"
}
```

Use `"mode": "remove"` with the selected IDs to remove restrictions.

`starts_at`, `expires_at`, and `reason` are optional. Omitting `expires_at` creates a
permanent restriction. Future `starts_at` values schedule the restriction.

## Services

| Method | Path | Purpose |
|---|---|---|
| GET/PATCH | `/api/v1/admin/services/{id}/` | Read or update a service |
| POST | `/api/v1/admin/services/{id}/activate/` | Activate service |
| POST | `/api/v1/admin/services/{id}/deactivate/` | Deactivate with `reason` |

## Operations

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/admin/jobs/` | Search/filter report jobs |
| POST | `/api/v1/admin/jobs/{id}/retry/` | Retry a failed job |
| POST | `/api/v1/admin/jobs/{id}/cancel/` | Cancel an active job |
| GET | `/api/v1/admin/audit-logs/` | Read-only audit log |
| GET/POST/PATCH | `/api/v1/admin/report-types/` | Report template inventory |

List endpoints support page-number pagination. Relevant endpoints also support `search`,
`ordering`, `status`, `role`, `kind`, `outcome`, and `action` query filters.
