# ADR-005: Immutable template versions

- Status: Accepted
- Date: 2026-07-14

## Context
Editing a template changed the meaning of previously generated reports.

## Decision
`ReportTemplateVersion` snapshots `template_file` + `fields_schema` + `checksum` + `status`.
Activated versions are immutable in impactful fields; changes require a new version. One active
version per report type. `GeneratedReport.template_version` (PROTECT) records which version was
used; a referenced version cannot be deleted. Existing data backfilled to an active v1.

## Consequences
- Reproducible, auditable reports. Slightly more moving parts in the catalog module.
