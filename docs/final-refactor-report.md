# Final Refactor Report

Date: 2026-07-14 · Scope: MVP → maintainable Modular Monolith (local development).

## 1. Executive summary

The single-app Django MVP was refactored into a modular monolith with a use-case/selector
layering, asynchronous report generation, immutable template versioning, a storage
abstraction, cookie-based auth with CSRF, rate limiting, an audit log, structured logging,
a test safety net, and CI — while preserving existing behavior and data (no table renames).
Backend: **51 tests passing**. Frontend: **`tsc` clean, 5 Vitest tests, `next build` succeeds**.

## 2. Architecture before

One Django app (`reports`) mixing auth, catalog, generation, and dashboard in
`views.py`/`serializers.py`; synchronous generation blocking the HTTP request; JWT in
`localStorage`; no tests, no git, no versioning, no audit, no storage abstraction.

## 3. Architecture after

See `architecture.md`. Feature packages (`accounts`, `catalog`, `generation`, `dashboard`,
`audit`, `shared`) inside the `reports` app; Celery/Redis async generation with a state
machine; `DocumentStorage`; immutable `ReportTemplateVersion`; cookie JWT + CSRF + rotation;
throttling; `AuditEvent`; unified error model + correlation id; JSON logging; health probes.

## 4. Final project tree

See `architecture.md` §5–6.

## 5. Modules & responsibilities

See `architecture.md` §10.

## 6. Database changes

Additive only, no table renames. New tables: `reports_reporttemplateversion`,
`reports_auditevent`. New columns on `reports_generatedreport`
(`task_id, attempts, queued_at, started_at, finished_at, template_version_id`) and two new
status values (`queued`, `cancelled`).

## 7. Migrations

- `0001_initial` (baseline)
- `0002_...attempts_finished_at...` — task-tracking fields + new statuses
- `0003_template_versioning` — `ReportTemplateVersion` + `template_version` FK
- `0004_backfill_template_versions` — data: active v1 per type + link existing reports
- `0005_audit_event` — `AuditEvent`

All apply cleanly from an empty DB (verified).

## 8. SQLite → PostgreSQL

**N/A** — the project has no SQLite; it already runs on PostgreSQL. Documented rather than
building unused tooling.

## 9. Fresh development setup

```bash
cp .env.example .env
docker compose up --build
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py seed_dev_data
```

## 10. Existing-data migration setup

Additive migrations run in place (`python manage.py migrate`); `0004` backfills template
versions and links existing reports. No destructive steps.

## 11. Run locally

`docker compose up --build` → frontend :3000, API :8000, admin /admin. See `operations.md`.

## 12. Run the Celery worker

`worker` service in compose; standalone `celery -A config worker --loglevel=info`.

## 13. Run tests

`cd backend && pytest` (PostgreSQL); `cd frontend && npm run test`.

## 14. Lint / typecheck

`ruff check .` · `black --check .` (backend); `npm run typecheck` (frontend).

## 15. Frontend production build

`cd frontend && npm run build` (verified) or `docker build -f Dockerfile.prod ./frontend`.

## 16. Backup / 17. Restore

See `backup-and-restore.md` (`scripts/backup_postgres.sh`, `restore_postgres.sh`, `verify_backup.sh`).

## 18. Authentication changes

JWT moved from `localStorage` to HttpOnly cookies; login body no longer returns tokens;
short access lifetime; refresh rotation + blacklist; CSRF enforced; logout clears + blacklists.

## 19. API changes

Report creation now returns **202 + queued** (was 200/500 + completed). New endpoints:
`/api/auth/refresh/`, `/api/reports/{id}/status/`, `/api/reports/{id}/retry/`,
`/health/live`, `/health/ready`. Unified error body `{code,message,request_id}`. See `api-contracts.md`.

## 20. Template versioning changes

Immutable `ReportTemplateVersion` with checksum + statuses; reports pin the version used;
central schema/placeholder validation; DOCX structural security scanner. See ADR-005.

## 21. Permissions matrix

See `permissions-matrix.md`.

## 22. Audit events

login success/failure, logout, token refresh, report created, generation completed/failed,
report downloaded, template activated. Read-only; no secrets stored.

## 23. Rate-limit policies

Per-IP `login`/`refresh`; scoped `report_create`, `download`; `user`/`anon` defaults; `429`
on limit; disabled in tests.

## 24. Security improvements

Cookie JWT + CSRF + rotation; throttling; audit log; safe error model; DOCX security scanner;
production settings safety checks; secret cleanup; no tokens in JS.

## 25. ADRs

ADR-001 modular monolith · 002 postgresql · 003 background generation · 004 storage
abstraction · 005 template versioning · 006 cookie auth · 007 permissions · 008 status polling.

## 26. Deferred features

See `deferred-features.md` (approval workflow, template-upload endpoint, antivirus, S3, cloud,
WebSockets, richer role mapping).

## 27. Remaining technical debt

- Full REST endpoints + UI for template upload/version management (services + scanner ready).
- Detail page (`reports/[id]`) reads once; could reuse the polling hook for in-flight reports.
- Non-root container user deferred (local media-volume permissions).
- Django-group → role mapping is reserved but not fully wired (ownership + staff enforced today).

## 28. Known risks

- Async paths verified with Celery **eager mode** + SQLite in the sandbox; a full run on real
  PostgreSQL + Redis + a live worker should be exercised locally/CI.
- `docker build`, `docker compose up`, and a real backup→restore were **not executed** in the
  build environment (no Docker/Postgres/Redis there).

## 29. Key commands run (real results)

- Backend: `pytest` → **51 passed**; `ruff check .` clean; `black --check .` clean;
  `python manage.py check` clean; `makemigrations --check` → no changes; `migrate` from empty DB OK.
- Frontend: `npm ci` OK; `tsc --noEmit` clean; `vitest run` → **5 passed**; `next build` → success.

## 30. Real test results

Backend **51 passed** (auth/cookies, catalog, async generation + polling + retries + state
machine, storage + downloads, template versioning + validation + DOCX security, audit,
throttling, error model, health, logging). Frontend **5 passed** + typecheck + build.

## 31. Last commit

`8e3ee06 ops: local postgres backup, restore, and verify scripts` (33 commits total in the
session working copy). Documentation commit to add on your side:
`docs: document final modular architecture, adrs, guides, and report`.

> Note on environment: the working folder could not host git and had no Postgres/Redis/Docker,
> so commits were produced in a session working copy and file changes synced into your folder.
> Run `git init` locally and apply the per-phase commit messages listed in `refactor-progress.md`.

## 32. Acceptance criteria

| Criterion | Status | Evidence / Notes |
|---|---|---|
| `architecture.md` matches code + module boundaries | Pass | `docs/architecture.md` |
| Dependency rules + adding-a-feature guide + ADRs | Pass | `docs/adding-a-feature.md`, `docs/decisions/` |
| CLAUDE.md + AGENTS.md present | Pass | repo root |
| PostgreSQL default (dev/tests/CI) | Pass | `settings`, `settings_test`, CI |
| Fresh migrations from empty DB | Pass | `migrate` verified |
| Existing-data path (additive migrations + backfill) | Pass | `0004` verified |
| SQLite migration path | N/A | no SQLite in project |
| Backend tests pass | Pass | 51 passed |
| API integration tests | Pass | endpoint tests in suite |
| Frontend tests pass | Pass | 5 Vitest + tsc + build |
| Migration consistency check | Pass | `makemigrations --check` clean |
| Production frontend build | Pass | `next build` success |
| Docker builds | Partial | Dockerfiles written + compose valid; `docker build` not run here (no Docker) |
| HTTP request never waits on PDF | Pass | 202 + Celery |
| Redis + Celery locally | Pass (config) | compose worker + redis; run locally |
| Report states + retries + dedupe + cleanup | Pass | state machine + task tests |
| Safe user errors + polling stop | Pass | error model + `useReportStatus` |
| Storage abstraction + protected downloads | Pass | `DocumentStorage`, tests |
| Missing files handled safely | Pass | 404 test |
| Template versioning + immutability | Pass | model guard + tests |
| Existing templates get initial versions + linked | Pass | `0004` |
| Invalid schema / DOCX / placeholder / zip-slip rejected | Pass | validation + scanner tests |
| Tokens not in localStorage; HttpOnly cookies | Pass | cookie auth + stubs |
| Refresh rotation; logout revokes | Pass | refresh/logout tests |
| CSRF protection | Pass | `CookieJWTAuthentication` + tests |
| No default creds in UI; no `.env` in git | Pass | login cleaned; `.gitignore` |
| Rate limiting (429) | Pass | throttle test |
| Permissions enforced server-side | Pass | ownership/admin tests |
| Audit log works | Pass | audit tests |
| Internal errors not exposed | Pass | unified handler |
| Frontend: routes thin, feature logic, unified client, polling, error model, typecheck | Pass | Phase 8 |
| Docker local stack + healthchecks | Pass (config) | compose + `/health/ready`; run locally |
| Backend readiness | Pass | `/health/ready` |
| Backup/restore scripts | Pass | `scripts/` |
| Restore tested locally | Not done | no Postgres in build env — run locally |
| Project run documented | Pass | `operations.md` |
