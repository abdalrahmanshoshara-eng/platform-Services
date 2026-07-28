# Contributor & AI-Agent Guide

Read `docs/architecture.md` before changing code. These rules are mandatory.

## Where things go
- Identify the module first: `accounts`, `catalog`, `generation`, `dashboard`, `audit`, `shared`.
- Business logic lives in `application/` use cases and `domain/`; reads in `selectors.py`.
- API endpoints in each module`s `views.py`; input/output shape in `serializers.py`.
- External boundaries (LibreOffice, storage) behind interfaces in `services/`/`shared`.

## Hard rules
- No business logic in Views, Serializers, or React components.
- No DB schema change without a migration; never delete an existing migration.
- Never change a public API without updating `docs/api-contracts.md`.
- Every bug fix needs a regression test; every feature needs tests.
- No new dependency without a clear reason; no abstraction without a real use.
- No direct filesystem paths (`FileField.path`, `MEDIA_ROOT`) in business logic — use `DocumentStorage`.
- Never store JWTs in `localStorage`; auth is HttpOnly cookies + CSRF.
- An HTTP request must never wait for PDF generation (enqueue Celery, return 202).
- Do not cross module boundaries via private imports; use public selectors/use cases.
- Never disable CSRF to "fix" auth. Never return internal errors/tracebacks to users.
- No secrets in Git (`.env` is ignored; use `.env.example`).
- Keep backward compatibility where possible.

## Definition of done (run these)
- Backend: `ruff check .` · `black --check .` · `python manage.py check` ·
  `python manage.py makemigrations --check --dry-run` · `pytest` (PostgreSQL).
- Frontend: `npm run typecheck` · `npm run test` · `npm run build`.
- Update `docs/architecture.md` when the architecture changes; add an ADR for significant decisions.

## Layering
- Writes: View → Input Serializer → Use Case → Domain → ORM/Infra → Output Serializer.
- Reads: View → Selector → Output Serializer.
