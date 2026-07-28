# Testing strategy

- **Framework**: `pytest` + `pytest-django`. Config in `backend/pytest.ini`
  (`DJANGO_SETTINGS_MODULE=config.settings_test`, PostgreSQL, throttling disabled).
- **Characterization tests** protect existing behavior before refactors.
- **Async**: enable Celery eager mode via the `eager` fixture and run enqueued tasks with
  `django_capture_on_commit_callbacks(execute=True)`.
- **Layers covered**: auth (cookies/refresh/logout), catalog (visibility + admin create),
  generation (async create → poll → download, retries, ownership), template versioning +
  validation + DOCX security, storage + secure downloads, audit, throttling, error model,
  health checks, logging.
- **Frontend**: Vitest unit tests for pure logic (`validateInput`, error mapping, status
  helpers) + `tsc --noEmit` + `next build`.
- Snapshots are not the primary source of confidence.

## Run
```bash
cd backend && pytest                      # PostgreSQL via POSTGRES_* / DATABASE_URL
ruff check . && black --check . && python manage.py check
python manage.py makemigrations --check --dry-run
cd ../frontend && npm run typecheck && npm run test && npm run build
```
