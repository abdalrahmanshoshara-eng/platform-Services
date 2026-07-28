# ADR-008: Status polling (not WebSockets)

- Status: Accepted
- Date: 2026-07-14

## Context
Clients need to track async generation progress. WebSockets/Channels add infrastructure.

## Decision
Expose `GET /api/v1/reports/{id}/status/` and poll from the SPA (`useReportStatus`): ~2s interval,
stop on terminal states, clean up on unmount, bounded backoff on transient errors.

## Consequences
- Simple and robust for this scale. If real-time UX is needed later, revisit with SSE/WebSockets.
