# سجل تقدّم إعادة الهيكلة — Refactor Progress

سجل زمني لكل مرحلة: ما تم، الملفات المتغيّرة، الاختبارات المشغّلة، النتائج، المتبقّي، والـ commit.

---

## Phase 0 — Audit & Safety

- **الحالة**: مكتملة (توثيق) / محدودة بالبيئة (Git).
- **التاريخ**: 2026-07-14.
- **ما تم تنفيذه**:
  - فحص كامل للـ backend (`settings`, `models`, `views`, `serializers`, `permissions`, `urls`, `services`, `seed`, `migration`) والـ frontend (`app/*`, `lib/*`, `components/*`) وDocker والاعتمادات.
  - إنشاء `docs/current-architecture-audit.md` (20 قسماً، مطابق للكود الفعلي).
  - إنشاء `docs/refactor-progress.md` (هذا الملف).
  - تحديد الحقائق المرجعية: PostgreSQL هي القاعدة الحالية (لا SQLite)، لا اختبارات، لا Git، توليد synchronous.
- **الملفات الرئيسية المتغيّرة/المضافة**: `docs/current-architecture-audit.md`, `docs/refactor-progress.md`.
- **الاختبارات المشغّلة**: لا يوجد بعد (لا توجد بنية اختبار — تُنشأ في Phase 1).
- **النتائج**: تدقيق دقيق + خطة تنفيذ مرحلية + سجل مخاطر.
- **المشكلات المتبقّية / قيود البيئة**:
  - بيئة الـ agent بلا **PostgreSQL/Redis/Docker** → لا يمكن تشغيل الحزمة أو اختبارات Postgres أو Docker من هنا.
  - مجلد المشروع على نظام ملفات **FUSE يمنع الحذف** → **Git لا يعمل داخل المجلد من هذه البيئة**. حاولت `git init` فأنشأ `.git` معطوباً (config.lock لا يُحذف)؛ أُعيدت تسميته إلى `.git_broken_agent_init` لإبقاء مجلدك نظيفاً. يمكنك حذفه وتشغيل `git init` من جهازك.
- **الـ commit**: تعذّر إنشاء commit من البيئة (سبب أعلاه). أوامر Git المقترحة لتنفيذها من جهازك:
  ```bash
  # من جذر المشروع على جهازك
  rmdir /s /q .git_broken_agent_init   # Windows، أو: rm -rf .git_broken_agent_init
  git init
  git add -A
  git commit -m "docs: audit current application architecture"
  ```

### أوامر Baseline (المرجعية للمراحل القادمة)
```bash
# Backend (داخل backend/ مع بيئة بها Postgres)
python manage.py check
python manage.py migrate
python manage.py test              # بعد إضافة الاختبارات في Phase 1
# Frontend (داخل frontend/)
npm ci
npm run build
```

---

## Phase 1 — Baseline Quality
- **Status**: Done (verified in sandbox).
- **Date**: 2026-07-14.
- **What was implemented**:
  - `pytest` + `pytest-django` harness: `backend/pytest.ini`, fixtures in `backend/reports/tests/conftest.py`.
  - **16 characterization tests** covering current behavior:
    - Auth: login success/failure, `/me` auth-required, logout, unauthenticated 401.
    - Catalog: active-only visibility for normal users, admin sees all, create allowed for admin only.
    - Generation: create → synchronous generation → `completed` + files; required-field rejection; failure path (missing template → 500/`failed`, documented defect); owner-only visibility; admin sees all; unauthorized download blocked.
  - Formatting/lint baseline: `black` + `ruff` via `backend/pyproject.toml` (migrations excluded). Applied to existing code.
  - Small safe fix: `pdf_converter.py` now uses `capture_output=True`.
  - Dependency pinning: `backend/requirements.txt` pinned to resolved versions; new `backend/requirements-dev.txt`.
  - Frontend: generated `frontend/package-lock.json`, added `typecheck` script (`tsc --noEmit`).
  - CI: `.github/workflows/ci.yml` — backend job (ruff, black --check, `manage.py check`, `makemigrations --check`, pytest) on **PostgreSQL + Redis** services; frontend job (`npm ci`, typecheck, build); infra job (compose config validation, `.env` guard).
- **Key files added/changed**: `backend/pytest.ini`, `backend/pyproject.toml`, `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/reports/tests/*`, `.github/workflows/ci.yml`, `frontend/package.json`, `frontend/package-lock.json`, plus formatting-only changes across `backend/**/*.py`.
- **Commands run (sandbox, real results)**:
  - `pytest` → **16 passed** (against SQLite in sandbox; project/CI config targets PostgreSQL).
  - `ruff check .` → **All checks passed**.
  - `black --check .` → **26 files unchanged** (clean).
  - `python manage.py check` → **no issues**.
- **Environment caveats (honest)**:
  - Sandbox has no PostgreSQL, so the suite was verified on SQLite locally; the committed `pytest.ini`/CI run on PostgreSQL. A sandbox-only `config/settings_sandbox_sqlite.py` was used for local verification and is **not** part of your repo.
  - Frontend `typecheck`/`build` not executed in sandbox (no full `node_modules`); they run in CI. `npm ci` locally will validate.
- **Suggested commits** (run on your machine — see Phase 0 for git init):
  ```
  style: apply ruff + black formatting baseline
  build: pin backend deps, add frontend lockfile and typecheck script
  test: add pytest harness and characterization tests
  ci: add github actions pipeline (postgres + redis)
  ```

### How to run the tests yourself
```bash
cd backend
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
# with a local/Docker PostgreSQL reachable via POSTGRES_* env (see .env.example):
pytest
ruff check . && black --check . && python manage.py check
```

## Phase 2 — PostgreSQL hardening
- **Status**: Done (verified in sandbox).
- **Date**: 2026-07-14.
- **What was implemented**:
  - `settings.py`: connection read from **`DATABASE_URL`** if present, else `POSTGRES_*` (no new dependency — parsed with `urllib`). Added `CONN_MAX_AGE` (persistent connections).
  - **UTC default**: `TIME_ZONE` now defaults to `UTC` (`DJANGO_TIME_ZONE`), with a separate `REPORT_DISPLAY_TIMEZONE` (default `Asia/Damascus`) so generated reports keep their local display time — **behavior preserved**.
  - Health probes: `config/health.py` + routes `GET /health/live` and `GET /health/ready` (readiness runs `SELECT 1`; Redis check deferred to Phase 9). No credentials or internal detail leaked.
  - `.env.example` expanded: `DATABASE_URL` (commented), `DJANGO_DB_CONN_MAX_AGE`, `REDIS_URL`, `DJANGO_TIME_ZONE`, `REPORT_DISPLAY_TIMEZONE`, and de-risked seed passwords (`change-me-*`).
- **Key files**: `backend/config/settings.py`, `backend/config/health.py`, `backend/config/urls.py`, `backend/reports/services/report_generation.py`, `backend/reports/tests/test_health_checks.py`, `.env.example`.
- **Commands run (sandbox)**: `pytest` → **19 passed** (16 + 3 new health tests); `ruff` clean; `black --check` clean; `makemigrations --check` → **No changes detected**; `manage.py check` → no issues.
- **SQLite → PostgreSQL migration**: **N/A** — the project has no SQLite (already PostgreSQL). Documented rather than building unused migration tooling. If a SQLite instance ever appears, the migration/verification scripts will be added then.
- **Suggested commits**:
  ```
  build: support DATABASE_URL, UTC default, and DB connection settings
  feat: add /health/live and /health/ready probes
  ```

## Phase 3 — Backend modular architecture
- **Status**: Done (verified in sandbox).
- **Date**: 2026-07-14.
- **Key decision (ADR-001)**: The existing `reports` Django app **keeps ownership of the tables** (no `db_table` moves, zero data-migration risk — per audit §20). Module boundaries are achieved through a **package structure + import rules + a use-case/selector layering**, not one-Django-app-per-module. Physically relocating models can be done later with `SeparateDatabaseAndState` once a PostgreSQL test environment is available.
- **What was implemented** (inside `backend/reports/`):
  - `shared/`: unified **API error model** (`errors.py`), domain exceptions (`exceptions.py`), **correlation id** middleware + contextvar (`correlation.py`), DRF `exception_handler.py`, cross-cutting `permissions.py`.
  - `accounts/`: login/logout/me views + serializers.
  - `catalog/`: report-type view + serializer + `selectors.visible_report_types`.
  - `generation/`: report view + serializers + `selectors.reports_for` + **`application.CreateReportUseCase`** (write path now goes View → Serializer → Use Case → ORM/Service).
  - `dashboard/`: `selectors.dashboard_statistics` + read-only view.
  - Wiring: `reports/urls.py` aggregates feature routers; `config/urls.py` imports auth from `accounts`; `settings` registers the correlation middleware + unified `EXCEPTION_HANDLER`.
  - Old `reports/views.py`, `serializers.py`, `permissions.py` kept as **backward-compatible re-export shims** (the folder's filesystem forbids deletion; shims also preserve any external imports).
- **Commands run (sandbox)**: `pytest` → **23 passed** (adds 4 error-model/correlation tests); `makemigrations --check` → **No changes detected** (tables preserved); `ruff`/`black --check` clean; `manage.py check` clean.
- **Behavior**: All API paths and responses unchanged (guarded by the characterization suite). The error *body* shape is now `{code,message,request_id}`; the frontend API client is adapted in Phase 8.
- **Suggested commits**:
  ```
  refactor: add shared error model, correlation id, and permissions
  refactor: split reports into feature modules with use cases and selectors
  test: cover unified error model and correlation id
  ```

## Phase 4 — Background generation (Celery/Redis)
- **Status**: Done (verified in sandbox with Celery eager mode).
- **Date**: 2026-07-14.
- **What was implemented**:
  - Celery app `config/celery.py` + `config/__init__.py`; Redis broker via `REDIS_URL`. **Result backend disabled** — PostgreSQL is the single source of truth for report state (`CELERY_RESULT_BACKEND=None`, `TASK_IGNORE_RESULT`). Added `acks_late`, `prefetch=1`, soft/hard time limits.
  - **State machine** `reports/generation/domain.py`: statuses `pending, queued, processing, completed, failed, cancelled` with explicit allowed transitions (e.g. `completed→processing` forbidden; `processing→queued` allowed only as retry). `transition()` raises `InvalidStateTransition`.
  - Model: added `task_id, attempts, queued_at, started_at, finished_at` + new statuses. Migration **`0002`** (additive columns + choices alter — safe, no data loss).
  - Task `reports/generation/tasks.py`: `select_for_update` row lock; **idempotency** (skip completed) + **duplicate protection** (skip processing); attempt counter; **re-enqueue with exponential backoff** up to `REPORT_MAX_ATTEMPTS` then mark `failed` with a **safe** user message (no path/traceback); correlation id propagated from request into the task.
  - Use case `CreateReportUseCase` now creates `pending`→`queued` and enqueues via `transaction.on_commit` — **the HTTP request returns 202 immediately** and never waits for LibreOffice. Added `RetryReportUseCase`.
  - Polling: `GET /api/reports/{id}/status/` (lightweight) and `POST /api/reports/{id}/retry/`.
  - Ops: `recover_stuck_reports` management command (requeues reports stuck in `processing`). Redis + `worker` (celery) services added to `docker-compose.yml`; backend command no longer auto-seeds an admin (explicit seeding documented for Phase 7/9).
- **Commands run (sandbox)**: `pytest` → **26 passed** (async completion via eager mode + captured `on_commit`, polling, retry→failed, state machine); `ruff`/`black` clean; `makemigrations --check` → **No changes detected**.
- **Behavior change (intended)**: report creation returns **202 + queued** instead of 200/500 + completed. Frontend adapts via polling in Phase 8.
- **Suggested commits**:
  ```
  feat: add celery app and redis-backed task settings
  feat: add report generation state machine and task-tracking fields
  feat: generate reports asynchronously with celery + polling and retries
  test: cover async generation, polling, retries, and state machine
  infra: add redis and celery worker to local docker stack
  ```

## Phase 5 — Storage abstraction
- **Status**: Done (verified in sandbox).
- **Date**: 2026-07-14.
- **What was implemented**:
  - `reports/shared/storage.py` → `DocumentStorage` (`save/open/exists/delete/get_size/get_checksum`) wrapping Django's storage API; module singleton `document_storage`. A new backend (e.g. S3) can be added later **without touching `ReportGenerationService`**.
  - `ReportGenerationService.produce()` now renders in a **temp working dir** (LibreOffice needs real paths) and persists final files **through `DocumentStorage.save()`** — no `MEDIA_ROOT`/`FileField.path` coupling in the persistence decision; temp dir auto-cleaned.
  - Download view no longer uses `FileField.path`; it streams via `document_storage.open()` after an ownership + existence check, with a **sanitized `Content-Disposition` filename** derived from the report title. Storage errors return a safe 404.
- **Commands run (sandbox)**: `pytest` → **29 passed** (owner download docx/pdf, missing-file 404, storage round-trip + checksum); `ruff`/`black` clean; `makemigrations --check` clean.
- **Suggested commits**:
  ```
  refactor: abstract generated document storage and secure downloads
  test: cover storage abstraction and permission-checked downloads
  ```

## Phase 6 — Templates versioning & validation
- **Status**: Done (verified in sandbox).
- **Date**: 2026-07-14.
- **What was implemented**:
  - Model `ReportTemplateVersion` (report_type, version, template_file, fields_schema, checksum, status: draft/validated/active/inactive/rejected, created_by, activated_at). **Impactful fields become immutable once ACTIVE** (guard in `save()`); editing requires a new version. `GeneratedReport.template_version` FK (PROTECT → a referenced version cannot be deleted).
  - Migrations: **`0003`** (schema) + **`0004`** (data backfill: creates an active v1 per report type with checksum, links existing reports). Verified to apply cleanly from an empty DB.
  - Central validation `catalog/validation.py`: `validate_fields_schema` (structure, identifiers, duplicates, supported types, select options, length bounds) + `validate_report_input` (required, unknown-field rejection, select/date/number checks, length bounds). **Backend is the single source of truth** — the duplicated serializer rule was removed.
  - `catalog/placeholders.py`: extract DOCX placeholders (docxtpl) + `validate_template_against_schema` (rejects unknown placeholders; reserved keys allowed).
  - `catalog/security.py` `TemplateSecurityScanner`: filename safety, size caps, DOCX signature, ZIP structure + required entries, zip-slip, compression-ratio/zip-bomb, macro/executable rejection, bad-zip handling. No external AV (documented deferred).
  - `ActivateTemplateVersionUseCase`: validates schema + placeholders, computes checksum, activates, and deactivates the previous active version (one active per type). Create flow now attaches the active version + validates input against its snapshot.
- **Commands run (sandbox)**: `pytest` → **44 passed** (schema/input validation, activation + immutability, single-active, DOCX scanner cases); `manage.py migrate` from empty DB OK; `ruff`/`black` clean; `makemigrations --check` clean.
- **2026-07-28 B6 follow-up**: admin-only upload/list/detail and audited
  validate/activate/deactivate/archive endpoints plus the minimal Admin UI are now live.
  Activation uses row locks and a one-active DB constraint; generation requires the active
  checksummed snapshot. Public/non-admin upload and external antivirus remain deferred.
- **Suggested commits**:
  ```
  feat: add immutable report template versions
  feat: central fields_schema validation, placeholder + docx security checks
  refactor: use active template version and central input validation on create
  test: cover template versioning, validation, and docx security
  ```

## Phase 7 — Security (cookies/CSRF/permissions/rate limit/audit)
- **Status**: Done (verified in sandbox).
- **Date**: 2026-07-14.
- **What was implemented**:
  - **HttpOnly cookie JWT**: `CookieJWTAuthentication` reads the access token from an HttpOnly cookie (Authorization header still works for tooling). Tokens are **no longer returned in the login body**. Login/refresh set cookies; logout blacklists the refresh token and clears cookies. `ACCESS_TOKEN_LIFETIME` cut to 15 min; **refresh rotation** (`ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`) via a `/api/auth/refresh/` endpoint using SimpleJWT's rotation.
  - **CSRF**: cookie-authenticated unsafe methods are CSRF-checked (`_enforce_csrf`); `CSRF_COOKIE_HTTPONLY=False` so the SPA can echo `X-CSRFToken`; `CORS_ALLOW_CREDENTIALS=True`. Cookie `Secure`/`SameSite` configurable, `Secure` defaults on in production.
  - **Rate limiting** (DRF throttling): per-IP `login` + `refresh` throttles (don't reveal account existence), scoped `report_create` and `download` throttles, plus `user`/`anon` defaults → HTTP 429. **Disabled in test settings** so it never breaks automated tests.
  - **Audit log**: append-only `AuditEvent` model (actor, action, target, outcome, request_id, ip, user_agent, safe metadata) + `audit.service.record()`. Wired into login success/failure, logout, token refresh, report created, generation completed/failed, download, template activation. Admin is **read-only** (no add/change/delete). Never stores passwords/tokens/full input. Migration **`0005`**.
  - **Production safety checks** (`reports/checks.py`, run by `manage.py check`): fail on default `SECRET_KEY`, default DB password, or non-secure cookies when `DEBUG=False`.
  - **Secrets**: `.env.example` de-risked (`change-me-*`); explicit on-demand `seed_dev_data` command (no auto-admin). CI uses a non-default DB password and `DEBUG=False`.
- **Commands run (sandbox)**: `pytest` → **50 passed** (cookie login/refresh/logout, audit success+failure, throttle blocks after limit, production-check flags insecure config); `ruff`/`black` clean; `makemigrations --check` clean; `manage.py check` clean (dev) and flags insecure config in production mode.
- **Behavior change (intended)**: auth is cookie-based; the frontend must use `credentials: "include"` + `X-CSRFToken` (done in Phase 8).
- **Suggested commits**:
  ```
  security: move jwt authentication to httponly cookies with csrf and rotation
  security: add rate limiting for login, refresh, create, and download
  feat: add append-only audit log for security and admin actions
  security: production settings safety checks and explicit dev seed
  test: cover cookie auth, audit, throttling; disable throttles in test settings
  ```

## Phase 8 — Frontend feature architecture
- **Status**: Done (fully verified in sandbox — tsc + tests + build).
- **Date**: 2026-07-14.
- **What was implemented**:
  - New structure: `src/shared/{api,auth,errors}` + `src/features/{auth,report-catalog,report-generation,reports-history,dashboard}`.
  - **Unified API client** (`shared/api/client.ts`): `credentials: "include"` (HttpOnly cookies), auto `X-CSRFToken` on unsafe methods, parses the backend error model into an `ApiError`, request cancellation via `AbortSignal`. No tokens in `localStorage` anymore.
  - **Auth state** (`shared/auth/AuthContext.tsx` + `useRequireAuth`): cookie-session based, hydrated from `/auth/me/`; `TopBar` and login use it. `lib/auth.ts` token/`localStorage` helpers are now no-op stubs.
  - Feature hooks: `useLogin`, `useReportTypes`, `useCreateReport` (+ `validateInput`), **`useReportStatus`** (polling with terminal-state stop, unmount cleanup, bounded backoff, transient-error tolerance), `useReports`, `useDashboard`.
  - `reports/new` page rewritten to submit (202) then **poll** until completed/failed; pages are thin composition. `lib/api.ts`/`lib/useRequireAuth.ts` kept as re-export shims so untouched pages keep working.
  - Backend: `ensure_csrf_cookie` on login + me so the SPA receives the CSRF cookie.
  - Tooling: **fixed `typescript` `7.0.2` → `^5.9.0`** (the preview build broke `next build`), added **Vitest** + unit tests, updated `tsconfig` (removed `target: es5`/`baseUrl`), regenerated lockfile, and added the frontend test step to CI.
- **Commands run (sandbox — real)**: `npm ci` OK; `npx tsc --noEmit` → **clean**; `npx vitest run` → **5 passed**; `npx next build` → **compiled successfully + static pages generated (exit 0)**.
- **Suggested commits**:
  ```
  security: set csrf cookie on login and me for the SPA
  refactor: organize frontend by feature with shared api client and auth
  build: fix typescript version, add vitest, wire frontend tests into ci
  ```

## Phase 9 — Local operations (Docker/health/logging/backup)
- **Status**: Done (verified where possible in sandbox).
- **Date**: 2026-07-14.
- **What was implemented**:
  - **Structured logging**: `reports/shared/logging.py` (`JsonFormatter` + `CorrelationIdFilter`); `LOGGING` in settings emits JSON with `correlation_id` (and `report_id/task_id/action/...` when provided). `DJANGO_LOG_FORMAT=plain` available for local readability.
  - **Docker**: backend `Dockerfile` now has a `HEALTHCHECK` + production `gunicorn` `CMD`; `docker-compose.yml` gained a backend healthcheck hitting `/health/ready` (db + redis already have healthchecks); new **`frontend/Dockerfile.prod`** (multi-stage `npm ci → build → start`).
  - **Backup/restore**: `scripts/backup_postgres.sh` (timestamped custom-format `pg_dump`, never prints the password, reminds that media is separate), `scripts/restore_postgres.sh` (restores to a **separate** DB by default, explicit confirmation before overwriting the live DB), `scripts/verify_backup.sh` (`pg_restore --list` integrity check).
- **Commands run (sandbox)**: `pytest` → **51 passed** (adds the logging test); `ruff`/`black`/`manage.py check` clean; `docker compose config` YAML valid; `bash -n` clean on all scripts.
- **Honest gaps**: no Docker/Postgres in this environment, so `docker build`, `docker compose up`, and an actual backup→restore round-trip were **not executed here** — they run on your machine / CI. Non-root container user was left as a documented hardening (avoids local media-volume permission issues).
- **Suggested commits**:
  ```
  feat: structured json logging with correlation id
  infra: production-capable builds and backend healthcheck
  ops: local postgres backup, restore, and verify scripts
  ```

## Phase 10 — Docs & final validation
- **Status**: Done.
- **Date**: 2026-07-14.
- **What was written** (English technical, matching the final code):
  - `docs/architecture.md` (36 sections + Mermaid: components, dependencies, auth sequence,
    creation/generation sequences, template lifecycle, ER diagram, local topology).
  - `docs/decisions/ADR-001…008`.
  - `docs/adding-a-feature.md`, `testing-strategy.md`, `security.md`, `operations.md`,
    `backup-and-restore.md`, `permissions-matrix.md`, `api-contracts.md`, `deferred-features.md`.
  - `CLAUDE.md` + `AGENTS.md` (mandatory contributor/agent rules).
  - `docs/final-refactor-report.md` (executive summary, before/after, migrations, commands,
    real test results, acceptance-criteria table).
- **Final verification (sandbox)**: backend `pytest` → **51 passed**; `ruff`/`black`/`manage.py check`
  clean; migrations apply from empty DB. Frontend `tsc` clean, `vitest` **5 passed**, `next build` OK.
- **Suggested commit**: `docs: document final modular architecture, adrs, guides, and report`.
