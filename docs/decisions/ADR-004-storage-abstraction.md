# ADR-004: Storage abstraction for generated documents

- Status: Accepted
- Date: 2026-07-14

## Context
Business logic used `FileField.path`/`MEDIA_ROOT` directly, coupling it to local disk.

## Decision
Introduce `DocumentStorage` (`save/open/exists/delete/get_size/get_checksum`) over Django's
storage API. Generation renders in a temp dir (LibreOffice needs real paths) and persists via
the abstraction; downloads stream through it after a permission check.

## Consequences
- A new backend (e.g. S3) can be added later without touching `ReportGenerationUseCase`.
- No S3 adapter is implemented now (deferred).
