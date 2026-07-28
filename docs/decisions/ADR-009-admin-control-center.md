# ADR-009: Independent Admin Control Center

## Status

Accepted.

## Decision

Provide a dedicated Next.js route tree under `/admin` and a dedicated DRF namespace
under `/api/v1/admin/`. Every endpoint uses one central `IsPlatformAdmin` permission.
Administrative writes are transactional and append an `AuditEvent`.

Keep account administration metadata in a one-to-one `UserAdministration` model instead
of replacing Django's user model. Keep service restrictions explicit, including creator,
optional reason, scheduled start, and optional expiry.

## Consequences

- User and admin navigation cannot leak into one another.
- The backend remains the source of truth even if a client bypasses the UI guard.
- Existing users and authentication tables remain migration-safe.
- New privileged operations must be added to the admin namespace and audit policy.
