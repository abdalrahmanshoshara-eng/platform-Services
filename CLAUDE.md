# Contributor & AI-Agent Guide

Verified project guide (audit dated 2026-07-28). Read `docs/CODEBASE_MAP.md` for the
full map and `docs/ENGINEERING_BACKLOG.md` for known issues before changing code.
These rules are mandatory.

## What this project actually is
A **report-generation platform**: users fill a JSON-schema form, the backend renders a
DOCX from a stored template (`docxtpl`) and converts it to PDF, asynchronously via Celery.
A lightweight **service catalog** (internal/external service cards) and an **Admin Control
Center** are layered on top. It is *not* the generic multi-tool platform the requirements
describe: there is no generic Job model, no Asset/object-storage model, no Tool Registry,
and no `ServiceUsageEvent`. See `docs/CODEBASE_MAP.md` → "Deviations from requirements".

## Stack (verified from manifests)
- Backend: Django 5.2, DRF 3.17, SimpleJWT 5.5, `psycopg` 3, Celery 5.6 + Redis, `docxtpl`
  + LibreOffice (PDF). PostgreSQL. Single Django project `config`, single app `reports`.
- Frontend: Next.js 16 (App Router) + React 19 + TypeScript 5.9 (strict), Vitest.
- Orchestration: `docker-compose.yml` (db, redis, setup, backend[gunicorn], worker, frontend).
  Files are stored on a local `backend_media` volume via `FileField` — **no S3/MinIO**.

## Repository layout
```
backend/config/            settings, urls, celery, health, wsgi/asgi
backend/reports/           models.py (all models), admin.py, urls.py
  accounts/                auth: login(username|email), refresh, logout, me; cookie JWT
  catalog/                 ReportType + template versioning use cases, validation, security
  generation/              GeneratedReport: views→application→domain(state machine)→tasks
  services_catalog/        Service list/detail + launch endpoint + access policy
  dashboard/               user dashboard stats (selectors)
  admin_api/               /api/v1/admin/* viewsets, admin permissions, analytics
  audit/                   AuditEvent writer
  services/                LibreOffice/PDF + report rendering (external boundary)
  shared/                  storage, permissions, errors, exception_handler, logging, correlation
frontend/src/
  app/                     App Router pages incl. app/admin/* and app/api/excel-contacts/*
  features/, components/, shared/{api,auth,admin,errors}, lib/excel-contacts
```

## Architectural boundaries (layering)
- Writes: View → Input Serializer → Use Case (`application.py`) → Domain (`domain.py`) →
  ORM → Output Serializer. Reads: View → `selectors.py` → Output Serializer.
- Report state transitions happen **only** through `generation/domain.py:transition()`.
- Keep business logic out of Views, Serializers, Celery tasks, and React components.
- Do not cross module boundaries via private imports; use public selectors/use cases.
- All access decisions go through `services_catalog/policy.py` and
  `admin_api/permissions.py` / `shared/permissions.py` — do not scatter `is_staff` checks.

## Backend rules
- One `models.py` owns the schema. No schema change without a migration; never edit or
  delete an existing migration (`0001`–`0008`).
- Never expose raw exception text to clients. `tasks.py` sanitizes to a safe message; keep
  it that way (`ReportGenerationService.generate()` in `services/` is dead & unsafe — do
  not wire it up without sanitizing, see backlog).
- Use `DocumentStorage` (`shared/storage.py`); no `FileField.path`/`MEDIA_ROOT` in logic.
- An HTTP request must never wait for generation — enqueue via
  `transaction.on_commit(... .delay())` and return **202**.
- Bulk admin operations must be a single `transaction.atomic` request, not N calls.
- Sensitive admin mutations (enable/disable, restrict, template state) must write an
  `AuditEvent`; never bypass the audited `activate`/`deactivate` actions.

## Frontend rules
- TypeScript strict; keep `any`-free (currently zero `any`). New excel-contacts code is
  plain JS and untyped — prefer TS.
- Never store JWTs in `localStorage`/`sessionStorage`; auth is HttpOnly cookies. Unsafe
  methods must echo `X-CSRFToken` and use `credentials:'include'` (`shared/api/client.ts`).
- Prefer the `@/shared/api` + `@/shared/auth` stack; the `@/lib/*` shims are deprecated.
- Admin gating in `components/admin/AdminChrome.tsx` is client-side only — **backend
  authorization is the real gate**; never rely on hiding routes/cards.
- Business data (services, categories) comes from the API, never hardcoded.

## Security guardrails
- Cookie JWT (HttpOnly), refresh rotation + blacklist, CSRF on unsafe methods, CORS
  restricted to configured origins. Keep `AUTH_COOKIE_SECURE`/`DEBUG` correct per env.
- External `launch_target` must be HTTPS, internal must start with `/` (enforced in
  `Service.clean()`). Do not let users supply launch URLs.
- Do not log file contents, tokens, or passwords. Audit must not store file content.

## Migration rules
- Additive, reversible migrations only; run `makemigrations --check --dry-run` in CI.
- Never delete history; historical rows back analytics/audit — soft-disable, don't delete.

## Minimal-diff rules
- Prefer the smallest correct change. No broad refactors, no new deps or abstractions
  without a verified need. Update `docs/CODEBASE_MAP.md` and `docs/api-contracts.md` when
  behavior or contracts change; add an ADR for significant decisions.

## Definition of done
- Backend: `ruff check .` · `black --check .` · `python manage.py check` ·
  `python manage.py makemigrations --check --dry-run` · `pytest` (SQLite by default;
  `TEST_USE_POSTGRES=true` for PostgreSQL).
- Frontend: `npm run typecheck` · `npm run test` (Vitest) · `npm run build`.
  There is **no `lint` script / ESLint config** — add one or rely on `next build` lint.
- Note: backend needs its deps installed (project `.venv` is Windows-only); the frontend
  `node_modules` is platform-specific — Vitest needs the matching native rollup binary.
```
```
