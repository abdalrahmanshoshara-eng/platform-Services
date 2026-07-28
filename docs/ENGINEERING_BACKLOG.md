# Engineering Backlog

Evidence-based, prioritized. Audit date 2026-07-28. Repository is the source of truth.
Priorities: **P0** active security/data-loss/breakage · **P1** foundational correctness/
architecture blocking safe development · **P2** important maintainability/perf/test/UX ·
**P3** optional cleanup. Line numbers are from the audited revision; verify before editing.

| ID | Priority | Area | Finding | Evidence | Impact | Recommended direction | Dependencies |
| -- | -------- | ---- | ------- | -------- | ------ | --------------------- | ------------ |
| B1 | P0 | Security/Auth | Login/refresh throttling is not shared across workers — no `CACHES` backend, so DRF throttles use per-process `LocMemCache` while backend runs `gunicorn --workers 3`. Effective login limit ≈ `10/min × workers`. | `config/settings.py` has no `CACHES`; throttle scopes at `settings.py:149-156`; `docker-compose.yml` backend `--workers 3` | Brute-force protection (a stated requirement) is materially weakened in the shipped config | Configure a shared Redis cache backend for throttling; keep `LocMemCache` only for tests | Redis (already present) |
| B2 | P0 · **RESOLVED 2026-07-28** | Security/Admin | ✅ Fixed. Was: category-level user blocking is a silent no-op — `UserCategoryRestriction` is modeled but no policy, selector, or admin endpoint ever reads/writes it. Now enforced by the centralized policy and manageable via an audited admin endpoint. | `reports/models.py:240-258`; old `services_catalog/policy.py:15-29` only read `service.user_restrictions`; grep found no other refs | Admins believed a user was blocked from a category while access remained — an access-control that silently failed; failed an acceptance criterion | Done — see "B2 — Resolution" below | B7 |
| B3 | P1 | Security/Config | Insecure production defaults: hardcoded `SECRET_KEY` fallback, `DEBUG` defaults `True`, and `AUTH_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` derive from `DEBUG`; `.env.example` ships `DEBUG=True`. | `config/settings.py:19-24,173,180-181`; `.env.example` | A prod deploy that forgets to flip `DEBUG` serves non-Secure auth cookies + tracebacks | Fail fast if `SECRET_KEY` unset in non-debug; require explicit `DJANGO_DEBUG=False`; add a deploy checklist | — |
| B4 | P1 | Architecture/Admin | Audited enable/disable is bypassable: generic `PATCH` on admin Service/ReportType viewsets and `list_editable`/editable fields in Django `admin.py` flip `is_active`/`status` directly, skipping the `activate`/`deactivate` actions that set `disabled_by/at` and write audit. | `admin_api/views.py:180-227,282-309`; `admin_api/serializers.py:81-101`; `admin.py:29-34,54-60` | Services/templates disabled with no audit trail or metadata; audit integrity gap | Make `is_active`/`status` read-only on the generic serializers; route state changes only through audited actions; lock down Django admin editable fields | — |
| B5 | P1 | Architecture/Validation | `ReportType.fields_schema` is editable via `AdminReportTypeViewSet` with no schema validation; `validate_fields_schema` runs only inside a use case that has no HTTP entry point. | `admin_api/views.py:282-309`; `admin_api/serializers.py:148-157`; `catalog/validation.py`; `catalog/application.py:20-47` | Invalid schemas (dup names, `select` w/o options) persist and break the user form/generation | Call `validate_fields_schema` in the admin serializer `validate()`; add API-level test | B6 |
| B6 | P1 | Architecture/Dead code | Template-version lifecycle (`ReportTemplateVersion`, `ActivateTemplateVersionUseCase`) and DOCX security scanner (`catalog/security.py`) are unreachable via any API — only unit-tested. Admin "report templates" needs cannot be met. | No viewset/URL in `reports/urls.py` or `admin_api/urls.py`; callers only in tests/migrations | Documented template management + upload-security features effectively don't exist at runtime | Expose versioning + template upload through `admin_api` (draft→validate→activate) wired to the scanner, or explicitly descope | B5 |
| B7 | P1 | Security/Frontend | `POST /api/excel-contacts/process` (Next server route) processes uploaded Excel with **no auth check**; only the React page gates access client-side. Business logic also lives entirely in the frontend, bypassing the backend tool pipeline. | `app/api/excel-contacts/process/route.js:14-40` (no session check); page guard `app/tools/excel-contacts/page.tsx` | Unauthenticated compute/DoS vector; tool logic outside backend authz/audit | Add auth (call backend or verify cookie) + rate limit, or move processing to a backend tool endpoint | — |
| B8 | P1 | Security/Frontend | Admin route protection is client-side only (`AdminChrome` effect redirect); no `middleware.ts`. Child page effects can fire fetches before the redirect. | `components/admin/AdminChrome.tsx:14-22`; no `middleware.*` in repo | Real protection depends entirely on backend authz; brittle if any admin endpoint is under-guarded | Keep backend as the gate (it is), and add an edge `middleware.ts` guard for `/admin/*`; audit every `admin_api` endpoint's permission class | B4 |
| B9 | P1 | API/Consistency | API versioning is inconsistent: auth/reports/services under `/api/`, admin under `/api/v1/`. | `config/urls.py:13-19`; `reports/urls.py` | Two versioning contracts in one project; contract drift / client confusion | Version all public endpoints under `/api/v1/`; keep unversioned aliases temporarily for back-compat | — |
| B10 | P1 | Security/Auth | Registration does not run Django password validators (only `min_length=8`); no dedicated throttle scope. | `accounts/serializers.py:27-41` (no `validate_password`); `accounts/views.py:48-59` (no throttle) | Weak/common passwords accepted platform-wide; higher-volume account creation than login | Call `django.contrib.auth.password_validation.validate_password`; add a `register` throttle scope | B1 |
| B11 | P2 | Performance | N+1 in admin analytics: Python loop over every `Service` issuing 3 count queries each (`success`/`denied`/restrictions). | `admin_api/views.py:324-336` | `1+3N` queries; degrades as catalog/audit grow | Replace with grouped `values(...).annotate(Count(...))` aggregation | B12 |
| B12 | P2 | Performance/Data | Usage analytics derived from `AuditEvent` filtered by string `target_id`, but there is no index on `(action,target_type,target_id)`. | `admin_api/views.py:326-336`; indexes at `models.py:145-149` | Per-service analytics lookups scan/inefficient at volume | Add a composite index, or introduce a first-class usage-event table if analytics grows | — |
| B13 | P2 | Performance | Services list is effectively N+1 for restricted users: `prefetch_related("user_restrictions",...)` is set but `service_access_for` re-queries `.filter(...).first()` per service instead of using the prefetch. | `services_catalog/views.py:22`; `policy.py:21-27`; `serializers.py:34-38` | One extra query per service on the authenticated list endpoint | Compute restrictions from the prefetched set, or annotate access in the queryset | — |
| B14 | P2 | Security/Correctness | Dead `ReportGenerationService.generate()` stores raw exception text into `error_message`, which is serialized to clients; unused today but latent. | `services/report_generation.py:46-59`; serialized at `generation/serializers.py:17-32,71-82` | If ever wired to a sync path, leaks internal paths/stderr to users | Delete the dead method or sanitize like `tasks.py`; add a test asserting `error_message` never leaks internals | — |
| B15 | P2 | Frontend/Architecture | Two parallel API/auth stacks coexist: canonical `@/shared/api`+`@/shared/auth` vs deprecated `@/lib/{api,auth,useRequireAuth}` shims still imported by several report pages. | `lib/api.ts`, `lib/auth.ts` (marked deprecated) imported by `app/reports/page.tsx:8-9`, `app/reports/[id]/page.tsx:9-10`, `app/report-types/page.tsx:6-7` | Inconsistent boundaries; refactor hazard if stubs regain token storage | Finish migration to `@/shared`; delete the shims and orphaned hooks (`features/dashboard/useDashboard.ts`, `features/reports-history/useReports.ts`) | — |
| B16 | P2 | Frontend/UX | No App Router `error.tsx`/`loading.tsx`/`not-found.tsx` anywhere; every page hand-rolls loading/error state. Empty states are inconsistent (admin `<AdminEmpty>` vs bespoke markup in user pages). | grep: none under `app/`; `app/services/page.tsx:125`, `app/reports/page.tsx:61-63` | No route-level error boundaries; uncaught render errors are unhandled; inconsistent UX | Add route-segment `error/loading/not-found` files and a shared empty-state component | — |
| B17 | P2 | Frontend/Correctness | Hardcoded status displays that don't reflect real state: settings page shows permanent "connected/enabled" badges with no health API; profile shows a fixed "active" status ignoring `user.is_active`. | `app/admin/settings/page.tsx:12-14`; `app/profile/page.tsx:39` | Misleading operational/account status | Back badges with a health endpoint; render account status from API | — |
| B18 | P2 | Tests | Highest-value frontend flows are untested: admin route guard, login (`useLogin`), registration, restriction-assignment flow, and the core `apiFetch`/CSRF/error path (only `abortRequest` is tested). | `shared/api/__tests__/` (abort only); `features/report-generation/__tests__/validateInput.test.ts` | Regressions in auth/admin/restrictions would ship silently | Add tests for the guard, login/registration, restriction flow, and `client.ts` request/error path | B8,B15 |
| B19 | P2 | Tooling | No `lint` script and no ESLint config; `next build`'s default lint is the only gate. | `frontend/package.json` scripts; no eslint config in repo | Style/quality drift; no enforced FE lint in CI | Add ESLint + a `lint` script and wire into CI/Definition-of-Done | — |
| B20 | P2 | Security/Auth | Logout blacklists only the refresh token; a captured short-lived access token stays valid until expiry (15 min). | `accounts/views.py:90-104`; `SIMPLE_JWT` at `settings.py:161-167` | Small post-logout window of validity | Accept as documented trade-off, or shorten access lifetime / add a denylist check for high-risk actions | — |
| B21 | P2 | Architecture/Storage | `DocumentStorage` wraps `default_storage` (local `FileField`) but the docstring claims S3 swappability that isn't wired; requirements assume object storage + temporary signed URLs. | `shared/storage.py`; `docker-compose.yml` (no MinIO/S3) | Migration to object storage is unbudgeted; no signed-URL/retention layer | Either implement an S3 backend behind `DocumentStorage` or correct the docs to state local-only | — |
| B22 | P2 | Correctness/Domain | `recover_stuck_reports` sets `status=FAILED` directly instead of via `transition()`, circumventing the "domain is the only place transitions happen" invariant. | `management/commands/recover_stuck_reports.py:22-26` | Invariant erosion; future transition rules could be skipped by this path | Route the recovery transition through `domain.transition()` | — |
| B23 | P3 | Frontend/Types | excel-contacts is plain untyped JS in an otherwise strict-TS codebase; throws/consumes untyped `Error` objects. | `lib/excel-contacts/contacts.js:75-125,182-188`; `components/ContactProcessor.js` (298 lines) | Unchecked corner; no type safety for the most intricate FE logic | Port to TypeScript; add unit tests to Vitest (currently only an ad-hoc `test:excel` script) | B7 |
| B24 | P3 | Docs | Repo docs (`docs/architecture.md`, `docs/api-contracts.md`, ADRs) describe the generic multi-tool platform, not the report-generation implementation. | `docs/` vs verified `CODEBASE_MAP.md` | New contributors are misled about models/flows that don't exist | Reconcile docs with `CODEBASE_MAP.md`; note descoped features explicitly | — |
| B25 | P3 | Security/Headers | No security headers/CSP configured (`SecurityMiddleware` present but no HSTS/SSL-redirect/CSP settings), despite requirements asking for them. | `config/settings.py` (no `SECURE_*`/CSP) | Weaker defense-in-depth in production | Add `SECURE_HSTS_*`, `SECURE_SSL_REDIRECT`, referrer policy, and a CSP (env-gated for prod) | B3 |
| B26 | P3 | Verification | `Needs verification`: backend `manage.py check`/`pytest` and frontend Vitest could not be run in the audit sandbox (backend deps not installed / Windows `.venv`; frontend `node_modules` missing the Linux `@rollup/rollup-linux-x64-gnu` native binary). Only `npm run typecheck` was executed (passed). | See "Verification" note below | Backend test suite health unconfirmed by this audit | Run the full Definition-of-Done on a matched platform / CI | — |

## B2 — Resolution (2026-07-28)
**Status:** Resolved (verified re-trace + fix + tests).

**Root cause:** `service_access_for` in `services_catalog/policy.py` only queried
`UserServiceRestriction` (direct service restrictions). `UserCategoryRestriction` was never
read by the policy and had no create/remove admin endpoint, so category-level blocking was
inert. The service catalog even prefetched `category__user_restrictions` but the policy
never used it.

**Fix:**
- Rewrote the centralized policy into a single decision function plus a bulk
  `access_decisions_for(user, services)` that resolves in a constant number of user-scoped
  queries (avoids N+1 on the services list). Decisions now account for: account disabled,
  service/category disabled, staff-only, active direct service restriction, and active
  **category** restriction, returning a stable `code`
  (`ACCOUNT_DISABLED`/`SERVICE_DISABLED`/`STAFF_ONLY`/`SERVICE_RESTRICTION`/
  `CATEGORY_RESTRICTION`/`ALLOWED`). Expired restrictions are excluded by the active-window
  filter and are never deleted during evaluation; checks are timezone-aware.
- Serializer now computes all list decisions once via `access_decisions_for`; removed the
  now-unused `prefetch_related` on the catalog queryset (kept `select_related("category")`).
- Added an audited, atomic, admin-only endpoint mirroring the existing service-restriction
  action: `POST /api/v1/admin/users/{id}/category-restrictions/` (`mode` add|remove,
  `category_ids[]`, optional `reason`, optional `expires_at`). Duplicates are deterministic
  via `update_or_create` on the existing `unique_together(user, category)`; all category IDs
  are validated before the atomic block, and one `AuditEvent`
  (`admin.category_restrictions.{mode}`) summarizes each operation.

**Files changed:** `backend/reports/services_catalog/policy.py`,
`backend/reports/services_catalog/serializers.py`,
`backend/reports/services_catalog/views.py`, `backend/reports/admin_api/views.py`,
new `backend/reports/tests/test_category_restrictions.py`. No migration needed (model,
fields, and `unique_together` already existed). No frontend changes.

**Verification (SQLite test settings):**
- `python manage.py check` — 0 issues.
- `python manage.py makemigrations --check --dry-run` — No changes detected.
- `pytest test_category_restrictions.py test_admin_control_center.py test_service_catalog.py`
  — 26 passed (14 new B2 tests + 12 existing).
- Full suite: 73 passed, 4 failed — the 4 failures are pre-existing and environmental
  (`PermissionError: Operation not permitted` deleting files on the sandbox media mount, in
  `test_storage_downloads.py` / `test_report_generation_characterization.py`), unrelated to B2.

**Remaining limitation:** `AdminUserDetailSerializer.get_restrictions` still lists only
service restrictions, so category restrictions aren't surfaced in the user-detail payload
(enforcement and management work regardless); surfacing them is a small follow-up. The two
requirements docs still describe multi-user bulk endpoints — this fix follows the existing
per-user restriction pattern instead.

## Verification performed
- `npm run typecheck` (frontend, `tsc --noEmit`) — **passed** (exit 0).
- `npm run test` (Vitest) — **could not run**: missing `@rollup/rollup-linux-x64-gnu`
  (node_modules installed for another OS; reinstalling is out of audit scope).
- Backend `python manage.py check` / `pytest` — **could not run**: Django not installed in
  the sandbox and the project `.venv` is a Windows venv; installing dependencies was out of
  scope. No application code, migrations, tests, or config were modified.
