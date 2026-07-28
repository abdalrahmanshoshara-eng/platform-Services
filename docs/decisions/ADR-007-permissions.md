# ADR-007: Permission model

- Status: Accepted
- Date: 2026-07-14

## Context
Only `is_staff`-based checks existed. All authorization must live in the backend.

## Decision
Enforce object ownership (`IsOwnerOrAdmin`) and admin-only management (`IsAdminOrReadOnly`)
in DRF permissions. Users see/download only their own reports; staff see all. Downloads are
permission-checked server-side. See `permissions-matrix.md`. Roles map to Django groups
(`report_creator`, `template_manager`, `auditor`, `administrator`) — the current code enforces
ownership + staff; richer group mapping is a documented extension.

## Consequences
- Hiding a button is never a permission. All access is verified server-side and tested.
