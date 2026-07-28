# Engineering Backlog

Evidence-based, prioritized. Audit date 2026-07-28. Reconciled against `main` at
`1b972ce` after B6; the working tree was clean before this documentation-only update.
Repository is the source of truth.
Priorities: **P0** active security/data-loss/breakage · **P1** foundational correctness/
architecture blocking safe development · **P2** important maintainability/perf/test/UX ·
**P3** optional cleanup. Line numbers are from the audited revision; verify before editing.

## Next execution order

1. **B18 — Frontend regression tests:** cover auth, admin gating, restrictions, and `apiFetch`.
2. **B26 — Environment verification:** run the full stack against Docker/PostgreSQL/Redis/Celery.
3. **B23 — Optional cleanup:** migrate the remaining Excel Contacts UI component to TypeScript.

| ID | Priority | Area | Finding | Evidence | Impact | Recommended direction | Dependencies |
| -- | -------- | ---- | ------- | -------- | ------ | --------------------- | ------------ |
| B1 | P0 · **RESOLVED 2026-07-28** | Security/Auth | ✅ Fixed. Was: login/refresh throttling was not shared across workers — no `CACHES` backend, so DRF throttles used per-process `LocMemCache` under `gunicorn --workers 3` (effective login limit ≈ `10/min × workers`), and registration had no dedicated throttle scope. Now a shared Redis cache backs throttling and registration has its own `register` scope. | `config/settings.py` had no `CACHES`; throttle scopes at `settings.py:149-156`; `docker-compose.yml` backend `--workers 3` | Brute-force protection (a stated requirement) was materially weakened in the shipped config | Done — see "B1 — Resolution" below | Redis (already present) |
| B2 | P0 · **RESOLVED 2026-07-28** | Security/Admin | ✅ Fixed. Was: category-level user blocking is a silent no-op — `UserCategoryRestriction` is modeled but no policy, selector, or admin endpoint ever reads/writes it. Now enforced by the centralized policy and manageable via an audited admin endpoint. | `reports/models.py:240-258`; old `services_catalog/policy.py:15-29` only read `service.user_restrictions`; grep found no other refs | Admins believed a user was blocked from a category while access remained — an access-control that silently failed; failed an acceptance criterion | Done — see "B2 — Resolution" below | — |
| B3 | P1 · **RESOLVED 2026-07-28** | Security/Config | ✅ Fixed. `DEBUG` now defaults to `False` (fail-closed); a guard refuses to boot with the shared dev `SECRET_KEY` when `DEBUG` is off; and with `DEBUG` off, HTTPS redirect + HSTS + nosniff + referrer-policy + Secure cookies turn on automatically (all env-overridable). `.env.example` gained a production checklist. | `config/settings.py:19-24,182-195`; `.env.example` | A prod deploy that forgot to flip `DEBUG` served non-Secure cookies + tracebacks | Done — see "B3 — Resolution" below | — |
| B4 | P1 · **RESOLVED 2026-07-28** | Architecture/Admin | ✅ Fixed for Service (the real gap). Was: generic `PATCH` on the admin Service viewset and `list_editable`/editable fields in Django `admin.py` flipped `is_active`/`status` directly, skipping the audited `activate`/`deactivate` actions. `Service.is_active` is now read-only on the API serializer and locked in Django admin; template `status` is locked in Django admin. ReportType toggling was already audited via `perform_update` (no metadata loss) — left as-is. | `admin_api/serializers.py:81-101`; `admin.py:29-34,54-60`; ReportType path `admin_api/views.py:300-308` already audits | Services/templates could be disabled with no audit trail or `disabled_by/at` metadata | Done — see "B4 — Resolution" below | — |
| B5 | P1 · **RESOLVED 2026-07-28** | Architecture/Validation | ✅ Fixed. `AdminReportTypeSerializer.validate()` now runs `validate_fields_schema` on create/PATCH, so malformed schemas (dup names, `select` without `options`, bad type, non-list) are rejected with `400 INVALID_FIELDS_SCHEMA` instead of being persisted. | `admin_api/serializers.py` `AdminReportTypeSerializer`; `catalog/validation.py` | Invalid schemas used to persist and break the user form/generation | Done — see "B5 — Resolution" below | — |
| B6 | P1 · **RESOLVED 2026-07-28** | Architecture/Security | ✅ Fixed. Template versions now have admin-only upload/list/detail and audited validate/activate/deactivate/archive actions. Uploads use randomized storage keys and bounded DOCX scanning; activation is transactional and DB-constrained to one active version; generation requires and preserves the active validated snapshot. | `catalog/{application,security}.py`; `services/template_storage.py`; `admin_api/{views,serializers,urls}.py`; migration `0010`; Admin UI | Runtime template management and upload security are now enforced end-to-end. | Done — see "B6 — Resolution" below | — |
| B7 | P1 · **RESOLVED 2026-07-28** | Security/Frontend | ✅ Confirmed and fixed. The unauthenticated Next route was the processing/security boundary. Processing now flows through authenticated `POST /api/tools/excel-contacts/process/` → input serializer → focused use case → centralized `service_access_for` → bounded workbook processor → audited in-memory response. | Added `backend/reports/excel_contacts/*` + focused tests; updated URL/settings/audit/dependencies/docs; Frontend now calls the canonical shared API from `features/excel-contacts/api.ts`; deleted the Next route and duplicate JS processor. | Authentication, active account/service/category, direct/category restrictions, file signature/size/dimension limits, safe errors, formula-safe exports, and `service.execute` audit are enforced server-side. | Done — synchronous mode preserves the immediate UI contract (10 MiB/10k-row bounds); old `/api/excel-contacts/process` Next route intentionally removed with no repository callers; 16 Backend B7 tests + policy tests and 4 Frontend tests pass. No Job/Asset migration because neither generic model exists; results are not retained. | — |
| B8 | P1 · **ACCEPTED TRADE-OFF** | Security/Frontend | The `/admin` route gate remains client-side, while authorization is deliberately enforced at the API boundary. | `AdminChrome.tsx`; every class in `admin_api/views.py` declares `IsPlatformAdmin`; ADR-009 states the backend remains authoritative. | An unauthorized client can briefly render the loading/redirect state and issue requests that the backend rejects; there is no demonstrated privilege bypass. | Keep backend authorization as the security boundary. Edge middleware is optional UX/defense-in-depth, not required remediation. | — |
| B9 | P1 · **RESOLVED 2026-07-28** | API/Consistency | ✅ Fixed. Public auth/report/service/tool routes were under `/api/` while admin used `/api/v1/admin/`; all application APIs are now canonical under `/api/v1/`. Existing `/api/...` routes remain deprecated aliases to the same URLConf/views, isolated in a legacy namespace so normal reverse lookups and schema inventory stay canonical. | `config/{urls,api_urls}.py`; Frontend `shared/api/{client,endpoints}.ts`; API docs and focused route tests. | New clients have one evolvable contract without breaking existing callers; health remains unversioned. | Done — see "B9 — Resolution" below. Remove aliases only after consumers migrate; no removal date is scheduled. | — |
| B10 | P1 · **RESOLVED 2026-07-28** | Security/Auth | ✅ Fixed. Registration now runs Django's configured password validators (length, common-password, numeric-only, similarity to username/email) via `RegisterSerializer.validate()`, not just `min_length=8`. Throttle half was already resolved under B1 (`register` scope + shared cache). | `accounts/serializers.py` `RegisterSerializer` | Weak/common passwords were accepted platform-wide | Done — see "B10 — Resolution" below | — |
| B11 | P2 · **RESOLVED 2026-07-28** | Performance | ✅ Fixed. The per-service loop that issued 3 count queries each is replaced by two grouped aggregations (launch counts by `target_id`+`outcome`, restriction counts by `service_id`), then a single service pass reads from in-memory maps — query count is now flat regardless of service count. | `admin_api/views.py` `AdminAnalyticsView` | `1+3N` queries degraded as catalog/audit grew | Done — see "B11/B12 — Resolution" below | — |
| B12 | P2 · **RESOLVED 2026-07-28** | Performance/Data | ✅ Fixed. Added a composite index `AuditEvent(action, target_type, target_id)` backing the service.launch analytics lookups (migration `0009`). | `models.py` `AuditEvent.Meta.indexes`; migration `0009_auditevent_reports_aud_action_11faf8_idx` | Per-service analytics lookups were unindexed at volume | Done — see "B11/B12 — Resolution" below | — |
| B13 | P2 · **RESOLVED 2026-07-28** | Performance | ✅ Fixed as part of B2: the serializer now calls `access_decisions_for(user, services)` once (two user-scoped queries) and the unused `prefetch_related` was removed, so the list endpoint's query count is flat regardless of service count. | `services_catalog/serializers.py`, `policy.py` (B2); regression test `test_services_list_perf.py` | Was one extra query per service on the authenticated list | Done (via B2) — confirmed with a query-count test | — |
| B14 | P2 · **RESOLVED 2026-07-28** | Security/Correctness | ✅ Fixed. The dead, unsafe `ReportGenerationService.generate()` (and its `_set_status` helper) that stored `str(exc)` into the client-visible `error_message` were removed; only the raising `produce()` remains, and the Celery task keeps ownership of sanitized status. | `services/report_generation.py`; regression test `test_recover_and_cleanup.py` | If ever wired to a sync path it would have leaked internal paths/stderr | Done — dead method removed; guarded by a test | — |
| B15 | P2 · **RESOLVED 2026-07-28** | Frontend/Architecture | ✅ Fixed. Runtime imports now use the canonical `@/shared/api` and `@/shared/auth` modules; the deprecated `@/lib/{api,auth,useRequireAuth}` shims and two confirmed-orphan hooks were removed. | Search confirms no runtime, test, dynamic, or alias-based imports remain; TypeScript typecheck passes. | A single cookie-aware API/auth stack remains, preserving CSRF, refresh/retry, and normalized error handling. | Done — deprecated compatibility paths removed without changing public API contracts. | — |
| B16 | P2 · **RESOLVED 2026-07-28** | Frontend/UX | ✅ Fixed (route boundaries). Added `app/error.tsx` (client error boundary with retry), `app/loading.tsx` (Suspense fallback), and `app/not-found.tsx` (404), so uncaught render errors and navigations now have App Router boundaries. | new `frontend/src/app/{error,loading,not-found}.tsx` | No route-level error boundaries; uncaught render errors were unhandled | Done — boundaries added; a shared empty-state component remains a minor follow-up | — |
| B17 | P2 · **RESOLVED 2026-07-28** | Frontend/Correctness | ✅ Fixed. Profile "account status" is now data-driven from `user.is_active` (newly exposed by `UserSummarySerializer`); the admin settings page checks `/health/ready` live for the PostgreSQL badge and relabels the components it cannot verify honestly ("مُهيّأ"/configured) instead of asserting a fake "connected". | `app/admin/settings/page.tsx`; `app/profile/page.tsx`; `accounts/serializers.py`; `shared/api/types.ts` | Misleading operational/account status | Done | — |
| B18 | P2 · **OPEN** | Tests | Highest-value frontend flows remain untested: admin gate behavior, login, registration, restriction assignment, and `apiFetch` cookie/CSRF/error behavior. | Current Vitest suite has 11 tests across five files, covering errors/abort/types/report input/Excel API but not these flows. | Regressions in auth/admin/restrictions can still ship without focused coverage. | Add tests for `AdminChrome`, auth flows, restriction UI, and canonical `apiFetch`; no dependency on B8 or B15 remains. | — |
| B19 | P2 · **RESOLVED 2026-07-28** | Tooling | ✅ Fixed. Added an ESLint 9 flat config using Next.js core-web-vitals and TypeScript rules, plus a clear `npm run lint` script and generated-output ignores. | `frontend/eslint.config.mjs`; `frontend/package.json`; lint and typecheck pass. | Frontend correctness checks now run independently of `next build`. | Done — one effect-state rule is disabled for the existing async loading/form-reset pattern; no broad auto-fix or framework upgrade was performed. | — |
| B20 | P2 · **ACCEPTED TRADE-OFF** | Security/Auth | Logout clears cookies and blacklists the refresh token; an already captured access token remains valid for its configured 15-minute lifetime. | `accounts/views.py:91-104`; `SIMPLE_JWT` access/refresh lifetimes in `config/settings.py`. | A bounded post-logout token-validity window remains, consistent with stateless short-lived JWT access tokens. | Accept the current 15-minute window; revisit only if product security policy requires immediate access-token revocation. | — |
| B21 | P2 · **ACCEPTED TRADE-OFF** | Architecture/Storage | Production currently uses Django storage backed by the local `backend_media` volume; no S3 adapter or signed-URL layer is implemented. | `shared/storage.py`, `docker-compose.yml`, CODEBASE_MAP, and accepted ADR-004 explicitly document local storage and the abstraction boundary. | Horizontal storage/retention concerns remain if deployment requirements expand. | Keep local storage for the current deployment. Reopen only with a concrete object-storage or retention requirement. | — |
| B22 | P2 · **RESOLVED 2026-07-28** | Correctness/Domain | ✅ Fixed. `recover_stuck_reports` now moves PROCESSING→FAILED via `domain.transition()` before retrying, upholding the "domain is the only place transitions happen" invariant. | `management/commands/recover_stuck_reports.py`; regression test `test_recover_and_cleanup.py` | Invariant erosion; future transition rules could be skipped | Done | — |
| B23 | P3 · **PARTIALLY RESOLVED** | Frontend/Types | B7 removed the untyped browser-side Excel processor and replaced its boundary with typed `features/excel-contacts/api.ts`, but the remaining UI is still `ContactProcessor.js`. | Deleted `lib/excel-contacts/contacts.js`; typed API contract plus four Vitest API tests; current `components/ContactProcessor.js` remains JavaScript. | Processing/security logic is now typed and server-side; residual risk is limited to UI state, preview, and download handling. | Optional: migrate `ContactProcessor.js` to TSX and add component interaction tests. | — |
| B24 | P3 · **RESOLVED BY OTHER WORK** | Docs | Core documentation now describes the actual report-generation platform and explicitly separates absent generic-platform capabilities. | Current `architecture.md`, `api-contracts.md`, CODEBASE_MAP, ADRs, and B6 documentation cover real models, flows, template lifecycle, and deviations. | The original contributor-misdirection finding is closed. | No backlog action; keep these files synchronized with future contract/architecture changes. | — |
| B25 | P3 · **RESOLVED 2026-07-28** | Security/Headers | ✅ Fixed on both deployment surfaces. Django transport/HSTS/referrer/nosniff settings have secure production defaults and explicit env controls; proxy scheme trust is opt-in. Next.js sends CSP, referrer, nosniff, permissions, and frame-protection headers with separate development HMR allowances. | `config/settings.py`; `.env.example`; `frontend/next.config.js`; focused Django and frontend header tests pass. | Production responses now have defense-in-depth without breaking local HTTP development. | Done — production CSP excludes `unsafe-eval`; `unsafe-inline` remains documented for Next bootstrap scripts and existing JSX inline styles. | — |
| B26 | P3 · **NEEDS ENVIRONMENT VERIFICATION** | Verification | Application and test checks now pass locally, but the real Docker/PostgreSQL/Redis/Celery stack has not been exercised. | Latest run: Django check and migration drift check pass; 148 backend SQLite tests pass; frontend typecheck, 11 Vitest tests, lint, and production build pass. Docker daemon was unavailable, so `TEST_USE_POSTGRES=true` was not run. | PostgreSQL-specific locking/constraints, migrations, worker/broker behavior, and volume integration remain unverified end-to-end. | Run the complete Docker stack and full backend suite against PostgreSQL in CI or a host with Docker available. | — |

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

## B4 — Resolution (2026-07-28)
**Status:** Resolved (Service enable/disable audit gap closed; Django admin locked).

**Root cause:** `Service` enable/disable had dedicated audited actions
(`activate`/`deactivate` set `disabled_reason/at/by` and write an `AuditEvent`), but
`AdminServiceSerializer` left `is_active` writable, so `PATCH /api/v1/admin/services/{id}/
{"is_active": false}` flipped the flag with no audit and no metadata. Django admin also
allowed inline toggling (`ServiceAdmin.list_editable` included `is_active`) and editing a
template version's `status` directly (bypassing the activation use case). Re-trace note:
`ReportType.is_active` toggles via `PATCH` but `AdminReportTypeViewSet.perform_update`
already writes an audit event and ReportType has no disabled-* metadata, so it was **not**
a real bypass and was left unchanged.

**Fix:**
- `AdminServiceSerializer`: added `is_active` to `read_only_fields`, so state changes are
  only possible through the audited `activate`/`deactivate` actions. Other properties
  (name, sort_order, …) remain editable via `PATCH`.
- `admin.py`: `ServiceAdmin` — removed `is_active` from `list_editable` and made
  `is_active`, `disabled_reason`, `disabled_at`, `disabled_by` read-only;
  `ReportTemplateVersionAdmin` — made `status` read-only.

**Files changed:** `backend/reports/admin_api/serializers.py`, `backend/reports/admin.py`,
new `backend/reports/tests/test_service_toggle_audit.py`. No migration (no schema change).
No frontend changes.

**Verification (SQLite test settings):**
- `python manage.py check` — 0 issues; `makemigrations --check --dry-run` — No changes.
- Targeted: `test_service_toggle_audit.py` + admin/service-catalog/category suites — 30 passed
  (4 new B4 tests + 26 existing). Full suite: 77 passed, 4 failed (the same pre-existing
  environmental media-mount `PermissionError`s, unrelated to B4).

**Remaining limitation:** Non-state property edits via the generic Service `PATCH`
(e.g. `launch_target`, `settings`) are validated by `Service.clean()` but are still not
themselves audited; adding a `perform_update` audit for Service edits is a small follow-up
outside B4's enable/disable scope.

## B1 — Resolution (2026-07-28)
**Status:** Resolved (shared throttle cache + dedicated registration scope).

**Root cause:** No `CACHES` was configured, so DRF's rate throttles fell back to Django's
default per-process `LocMemCache`. With `gunicorn --workers 3` each worker counted
independently, so the "10/min" login limit was really ~"10/min per worker". Registration
had no throttle scope at all and fell back to the generic anon limit (100/min).

**Fix:**
- Added a Redis-backed `CACHES["default"]` (`django.core.cache.backends.redis.RedisCache`,
  `LOCATION=DJANGO_CACHE_URL or REDIS_URL`, `KEY_PREFIX="reports"`) so throttle counters are
  shared across all worker processes. `redis` is already a dependency and a running service.
- `settings_test.py` overrides the cache to in-process `LocMemCache` so tests need no Redis.
- Added a `register` throttle scope (`THROTTLE_REGISTER`, default `10/min`), a
  `RegisterRateThrottle`, and wired it onto `RegisterView`.

**Files changed:** `backend/config/settings.py`, `backend/config/settings_test.py`,
`backend/reports/accounts/throttling.py`, `backend/reports/accounts/views.py`,
new `backend/reports/tests/test_throttling_cache.py`. No migration (no schema change). No
frontend changes.

**Verification (SQLite test settings):**
- `python manage.py check` — 0 issues; `makemigrations --check --dry-run` — No changes.
- `pytest test_throttling_cache.py` — 3 passed (shared-cache config guard; register throttle
  wired; registration returns 429 past the limit via the real throttle+cache path). Full
  suite: 80 passed, 4 failed (the same pre-existing environmental media-mount
  `PermissionError`s, unrelated to B1).

**Operational note:** to keep throttle keys off the Celery broker DB, set
`DJANGO_CACHE_URL` to a dedicated Redis database (e.g. `redis://redis:6379/2`).

**Remaining:** the register password-strength gap (B10) is still open — throttling alone
does not reject weak passwords.

## B10 — Resolution (2026-07-28)
**Status:** Resolved (both halves now closed: B1 added the throttle scope; this adds
password-strength enforcement).

**Root cause:** `RegisterSerializer` enforced only a bare `min_length=8` and never called
`django.contrib.auth.password_validation.validate_password`, so common/weak passwords
(e.g. `secret123`) were accepted even though `AUTH_PASSWORD_VALIDATORS` was configured.

**Fix:** `RegisterSerializer.validate()` now builds a transient `User(username, email)` and
runs `validate_password(password, user=candidate)`, mapping Django's `ValidationError` to a
DRF `{"password": [...]}` error. This activates all four configured validators including
similarity to username/email.

**Files changed:** `backend/reports/accounts/serializers.py`, new
`backend/reports/tests/test_registration_password.py`. Two existing tests that registered via
the API with the now-rejected `secret123` were updated to a compliant password
(`test_service_catalog.py`, `test_throttling_cache.py`) — a required consequence of the
behavior change, not a rewrite. `create_user` fixtures are unaffected (they bypass the
serializer). No migration. No frontend changes.

**Verification (SQLite test settings):**
- `python manage.py check` — 0 issues.
- `pytest test_registration_password.py` — 4 passed (common, numeric-only, and
  username-similar passwords rejected with 400; strong password accepted with 201). Full
  suite: 84 passed, 4 failed (the same pre-existing environmental media-mount
  `PermissionError`s, unrelated to B10).

## B3 — Resolution (2026-07-28)
**Status:** Resolved (fail-closed defaults + production transport hardening).

**Root cause:** `DEBUG` defaulted to `True` and `SECRET_KEY` fell back to a hardcoded
development value, while `AUTH_COOKIE_SECURE`/`CSRF_COOKIE_SECURE`/`SESSION_COOKIE_SECURE`
were derived from `DEBUG`. A deploy that forgot to set `DJANGO_DEBUG=False` therefore
served debug tracebacks and non-Secure auth cookies, and could run on the shared dev secret.

**Fix (config/settings.py):**
- `DEBUG` now defaults to `False` (fail-closed); dev/compose set `DJANGO_DEBUG=True`
  explicitly.
- `require_secure_secret(DEBUG, SECRET_KEY)` raises `ImproperlyConfigured` at boot if the
  shared `INSECURE_SECRET_KEY` is used while `DEBUG` is off.
- Added transport hardening that auto-enables when `DEBUG` is off (all env-overridable):
  `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS=31536000` (+ subdomains/preload),
  `SECURE_PROXY_SSL_HEADER`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`.
  Existing Secure-cookie flags remain tied to the (now fail-closed) `DEBUG`.
- `settings_test.py` pins `DJANGO_DEBUG=True` and a real secret *before* importing base
  settings (so the guard never trips in a clean CI without `.env`), and force-disables
  SSL redirect/HSTS so the plain-HTTP test client is never redirected.
- `.env.example` gained a production checklist.

**Files changed:** `backend/config/settings.py`, `backend/config/settings_test.py`,
`.env.example`, new `backend/reports/tests/test_production_settings.py`. No migration. No
frontend changes.

**Verification (SQLite test settings):**
- `python manage.py check` — 0 issues.
- `pytest test_production_settings.py` — 6 passed. Full suite: 90 passed, 4 failed (the same
  pre-existing environmental media-mount `PermissionError`s, unrelated to B3).
- Manual boot checks: `DJANGO_DEBUG=False` + fallback secret → raises `ImproperlyConfigured`;
  `DJANGO_DEBUG=False` + real secret → loads with `SECURE_SSL_REDIRECT=True`,
  `SECURE_HSTS_SECONDS=31536000`, `AUTH_COOKIE_SECURE=True`.

**Remaining:** a Content-Security-Policy header (tracked under B25) is still not set — it
needs a CSP middleware/dependency and is out of B3's scope.

## B5 — Resolution (2026-07-28)
**Status:** Resolved (admin ReportType schema is now validated server-side).

**Root cause:** `AdminReportTypeViewSet` is a full `ModelViewSet` whose serializer had no
`validate()`, so `fields_schema` was persisted verbatim. `validate_fields_schema` existed
but was only called from `ActivateTemplateVersionUseCase`, which has no HTTP entry point —
so admin edits bypassed validation entirely.

**Fix:** `AdminReportTypeSerializer.validate()` calls
`reports.catalog.validation.validate_fields_schema(attrs["fields_schema"])` when the field is
present (create or PATCH). Its `SchemaError` is a `DomainError`, so the existing unified
exception handler renders a `400` with the stable code `INVALID_FIELDS_SCHEMA` — no bespoke
error shaping needed.

**Files changed:** `backend/reports/admin_api/serializers.py`, new
`backend/reports/tests/test_admin_report_type_schema.py`. No migration. No frontend changes.

**Verification (SQLite test settings):**
- `python manage.py check` — 0 issues.
- `pytest test_admin_report_type_schema.py` — 5 passed (rejects missing name, `select`
  without options, and duplicate names; accepts a valid schema; create with a bad schema
  returns 400 and persists nothing). Full suite: 95 passed, 4 failed (the same pre-existing
  environmental media-mount `PermissionError`s, unrelated to B5).

**Remaining:** B6 (exposing the template-version draft→active lifecycle and the DOCX
upload-security scanner via the admin API) is still open and is a larger, feature-sized change.

## B6 — Resolution (2026-07-28)
**Status:** Resolved (admin template lifecycle and secure upload are reachable end-to-end).

**Fix:**
- Added nested admin-only list/upload/detail and validate/activate/deactivate/archive
  endpoints. Lifecycle transitions run through focused application use cases and every
  successful action records actor, timestamp, target, and optional reason in `AuditEvent`.
- Uploaded DOCX files are structurally scanned with bounded compressed/uncompressed size,
  entry count and compression ratio; traversal, malformed packages, macros/executables,
  OLE/embedded packages, external relationships, XML entities, encryption, and wrong
  extension/signature are rejected with safe errors. Managed files use randomized storage
  keys behind `DocumentStorage`; a failed DB write removes the blob.
- Added the archived state and a conditional unique DB constraint for one active version per
  report type (migration `0010`). Activation locks the report type and all versions,
  rechecks the file/checksum, retires the previous active version, and supports deterministic
  idempotent reactivation.
- Report creation now returns stable `409 NO_ACTIVE_TEMPLATE` unless an active checksummed
  version exists. Each report stores the selected version, so later deactivation/archive
  cannot rewrite history or break retries.
- Replaced the Admin UI's editable template filename with real DOCX upload, lifecycle status,
  and confirmed validate/activate/deactivate/archive controls.

**Verification:** focused API/security/version tests cover permissions, unsafe/oversized
uploads, lifecycle and repeated activation, the DB uniqueness invariant, history, state
bypass prevention, audit, cleanup, and safe errors. Full Definition-of-Done results are
recorded in the implementation handoff.

## B11/B12 — Resolution (2026-07-28)
**Status:** Resolved (analytics N+1 removed; supporting index added).

**Root cause:** `AdminAnalyticsView` looped over every `Service` and issued three `COUNT`
queries per service (successful launches, denied launches, active restrictions) — `1+3N`
queries. Those launch counts filtered `AuditEvent` by `(action, target_type, target_id)`,
which had no covering index.

**Fix:**
- `admin_api/views.py`: replaced the loop with two grouped aggregations —
  `AuditEvent … .values("target_id","outcome").annotate(Count("id"))` and
  `UserServiceRestriction … .values("service_id").annotate(Count("id"))` — then a single
  `Service.objects.select_related("category")` pass reads counts from in-memory maps.
  Query count is now independent of the number of services. Response shape/semantics
  unchanged (restriction window still keyed on `expires_at` as before).
- `models.py`: added `Index(action, target_type, target_id)` on `AuditEvent`; additive,
  reversible migration `0009`.

**Files changed:** `backend/reports/admin_api/views.py`, `backend/reports/models.py`,
new `backend/reports/migrations/0009_auditevent_reports_aud_action_11faf8_idx.py`,
new `backend/reports/tests/test_analytics_performance.py`. No frontend changes.

**Verification (SQLite test settings):**
- `python manage.py check` — 0 issues; `makemigrations --check --dry-run` — No changes
  (0009 accounts for the only model change).
- `pytest test_analytics_performance.py` — 2 passed: counts are correct, and the request
  query count is identical with 2 vs 7 services (proving no per-service growth). Full suite:
  97 passed, 4 failed (the same pre-existing environmental media-mount `PermissionError`s,
  unrelated to B11/B12).

## B13 / B14 / B22 — Resolution (2026-07-28)
**B13 (services-list N+1):** already fixed by the B2 refactor (`access_decisions_for` does two
bulk, user-scoped queries; the unused `prefetch_related` was removed). Locked with
`test_services_list_perf.py`, which asserts the query count is identical for 2 vs 8 services.

**B14 (dead unsafe generate()):** removed `ReportGenerationService.generate()` and
`_set_status()` — the only path that wrote `str(exc)` into the client-visible `error_message`.
`produce()` (raises on failure) is the sole entry point; `generation/tasks.py` remains the
owner of sanitized status. `CLAUDE.md`'s guidance was updated accordingly. Guarded by
`test_recover_and_cleanup.py::test_unsafe_generate_wrapper_is_removed`.

**B22 (recovery bypassed the state machine):** `recover_stuck_reports` now calls
`domain.transition(report, FAILED)` before `RetryReportUseCase`, so every transition flows
through the single source of truth. Verified by `test_recover_and_cleanup.py` (stuck report
ends up `QUEUED`; a recent PROCESSING report is left untouched).

**Files changed:** `backend/reports/services/report_generation.py`,
`backend/reports/management/commands/recover_stuck_reports.py`, `CLAUDE.md`, new
`backend/reports/tests/test_recover_and_cleanup.py`,
`backend/reports/tests/test_services_list_perf.py`. No migration. No frontend changes.

**Verification:** `python manage.py check` — 0 issues. Targeted new tests — 4 passed. Full
suite: 101 passed, 4 failed (the same pre-existing environmental media-mount
`PermissionError`s, unrelated to these changes).

## B16 / B17 — Resolution (2026-07-28)
**B16 (route boundaries):** added `frontend/src/app/error.tsx` (a `'use client'` error
boundary that logs the error and offers a retry via `reset()`), `app/loading.tsx` (Suspense
fallback), and `app/not-found.tsx` (styled 404 with a link home). Uncaught render errors and
missing routes now resolve to proper App Router boundaries instead of failing silently.

**B17 (data-driven status):**
- Backend: `UserSummarySerializer` now exposes `is_active`; the `UserSummary` TS type mirrors it.
- Profile: "account status" renders from `user.is_active` (`نشط`/`موقوف`) instead of a hardcoded value.
- Admin settings: converted to a client component that calls `/health/ready` and shows the
  PostgreSQL badge from the live `checks.database` result; the components it cannot verify
  (Celery+Redis, JWT mode) are labelled honestly ("مُهيّأ"/"مُفعّل") rather than a fake
  "connected".

**Files changed:** `frontend/src/app/{error,loading,not-found}.tsx` (new),
`frontend/src/app/admin/settings/page.tsx`, `frontend/src/app/profile/page.tsx`,
`frontend/src/shared/api/types.ts`, `backend/reports/accounts/serializers.py`.

**Verification:** `npm run typecheck` — passed (exit 0). Backend full suite — 101 passed,
4 failed (the same pre-existing environmental media-mount `PermissionError`s). Note: Vitest
could not be run in this environment (missing native rollup binary), so the new `.tsx` files
were validated by `tsc` type-checking and review only.

## B9 — Resolution (2026-07-28)

**Status:** Resolved. The previous split (`/api/...` for user APIs and
`/api/v1/admin/...` for admin) is replaced by canonical `/api/v1/...` routes. Temporary
deprecated `/api/...` aliases include the same URLConf under `legacy_api`; they therefore
share views, serializers, permissions, and business logic. Ordinary route names/reverses
produce v1 URLs, and `canonical_api_urlpatterns` excludes aliases from schema enumeration
to prevent duplicate paths/operation IDs. Health checks remain `/health/live` and
`/health/ready`.

**Files changed:** `backend/config/{api_urls,urls}.py`, focused B9 Backend tests,
Frontend `shared/api/{client,endpoints}.ts` and active call sites/config, focused Frontend
tests, `.env.example`, `docker-compose.yml`, `README.md`, and current API/architecture/
operations/security docs. No model, migration, payload, authentication, or authorization
change.

**Verification:** Django check and migration-drift check passed; 51 focused Backend tests
and the full 157-test SQLite suite passed; B9 Ruff/Black checks passed. Frontend typecheck,
12 Vitest tests, production build, and lint passed (zero errors; four existing warnings).
No OpenAPI endpoint was configured before B9; the canonical-only DRF schema input now
confirms `/api/v1/` paths with unique generated callback/action operation IDs. Alias removal
remains future work after consumer migration; no date is scheduled.

## Latest verification status
- Backend: `manage.py check` passed; `makemigrations --check --dry-run` reported no drift;
  **157 SQLite tests passed**.
- Frontend: typecheck passed; **12 Vitest tests passed**; lint completed with zero errors
  (four existing warnings); production build passed.
- Quality gates: B6-scoped Ruff/Black checks passed. Repository-wide Ruff/Black still report
  one existing B904 lint finding and formatting drift in five pre-existing files.
- Environment: Docker daemon was unavailable, so PostgreSQL migrations/tests and the
  PostgreSQL/Redis/Celery/media-volume integration remain unverified.
