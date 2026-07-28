# ADR-002: PostgreSQL everywhere

- Status: Accepted
- Date: 2026-07-14

## Context
The project already used PostgreSQL; there is no SQLite. Tests/CI must match production.

## Decision
PostgreSQL is the default DB in development, tests, and CI. Connection via `DATABASE_URL`
or `POSTGRES_*` (parsed without extra dependencies). `USE_TZ=True`, `TIME_ZONE=UTC`.

## Consequences
- No SQLite-specific behavior leaks into tests. A SQLite→Postgres migration path is N/A.
- A sandbox-only SQLite settings file is used solely for local agent smoke checks and is not
  part of the repo.
