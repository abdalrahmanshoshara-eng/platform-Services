# Deferred features (documented, not implemented)

Structure is ready for these; they were intentionally not built (out of scope / need a
product decision / require external services).

- **Approval workflow** (draft/under_review/approved/rejected for reports): a business feature,
  not an engineering fix. Needs a Product Owner decision. Kept separate from the technical
  generation states. Add as a new module/state machine without disturbing generation.
- **Public/non-admin template upload**: B6 added an admin-only REST upload endpoint and UI.
  Accepting templates from ordinary or untrusted users remains intentionally unsupported.
- **Antivirus scanning** of uploaded templates (e.g. ClamAV): only structural checks exist.
  Recommended before accepting templates from untrusted sources in production.
- **S3 / object storage adapter**: `DocumentStorage` supports it; only local storage is implemented.
- **Cloud** (managed Postgres/Redis, secret managers, Kubernetes/Terraform/Helm, CDN, TLS/DNS),
  **WebSockets** (polling used instead), and richer Django-group role mapping.
- **SQLite → PostgreSQL migration tooling**: N/A — the project has no SQLite.
