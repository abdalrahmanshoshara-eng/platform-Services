# ADR-001: Modular Monolith with in-app feature packages

- Status: Accepted
- Date: 2026-07-14

## Context
The MVP was a single Django app with mixed responsibilities. We need clear boundaries but
must not rewrite, must not add microservices, and must not risk existing data. Moving models
to new Django apps renames tables (e.g. `reports_reporttype` → `catalog_reporttype`), which
risks data loss and could not be verified against PostgreSQL in the working environment.

## Decision
Keep one deployable Django project. Achieve module boundaries via **feature packages inside
the `reports` app** (`accounts`, `catalog`, `generation`, `dashboard`, `audit`, `shared`)
with a use-case/selector layering and import rules. The `reports` app keeps ownership of all
tables; table names are unchanged.

## Consequences
- Zero data-migration risk (`makemigrations --check` reports no schema change for the split).
- Boundaries enforced by convention + review rather than Python package installation.
- If physical app separation is ever needed, use `SeparateDatabaseAndState` with preserved
  `db_table`, staged migrations, and row-count comparison — once a PostgreSQL test env exists.
