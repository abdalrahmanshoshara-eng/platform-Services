# ADR-003: Background report generation with Celery

- Status: Accepted
- Date: 2026-07-14

## Context
Generation was synchronous; the HTTP request blocked on LibreOffice, failing under load and
on large files, and returned internal errors to users.

## Decision
Generate asynchronously with Celery + Redis. Creation returns `202` with status `queued`.
A row-locked task enforces idempotency + duplicate protection, increments an attempt counter,
retries with exponential backoff, then marks `failed` with a safe message. Enqueue via
`transaction.on_commit`. Result backend disabled — PostgreSQL is the source of truth.

## Consequences
- Responsive API; resilient generation. Requires a running worker + Redis locally.
- Clients poll for status (see ADR-008).
