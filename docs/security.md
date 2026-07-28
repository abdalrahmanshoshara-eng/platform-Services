# Security

- **Authentication**: JWT in HttpOnly cookies (`CookieJWTAuthentication`). Short-lived access
  token; refresh rotation + blacklist via `/api/auth/refresh/`; logout blacklists + clears.
  Tokens are never in the response body or readable by JS.
- **CSRF**: enforced for cookie-authenticated unsafe methods; `csrftoken` cookie set on
  login/me; SPA echoes `X-CSRFToken`. CSRF is never disabled.
- **Permissions**: enforced server-side (`IsOwnerOrAdmin`, `IsAdminOrReadOnly`); users access
  only their own reports/downloads. See `permissions-matrix.md`.
- **Rate limiting**: per-IP login/refresh throttles (no account-existence leak); scoped
  create/download; `429` on limit. Disabled in tests.
- **Audit log**: append-only `AuditEvent`; read-only in admin; no secrets/tokens/full input.
- **Error handling**: unified `{code,message,request_id}`; internals logged, never returned.
- **Template uploads**: `TemplateSecurityScanner` (signature, ZIP structure, zip-slip,
  zip-bomb, macros/executables). Antivirus is a deferred pre-production item.
- **Secrets**: `.env` git-ignored; `.env.example` carries no real secrets; production
  safety checks fail on default secret/DB-password/insecure cookies when `DEBUG=False`.
