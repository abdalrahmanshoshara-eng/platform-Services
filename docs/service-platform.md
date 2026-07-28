# Service Platform Integration

## Service catalog

`ServiceCategory` and `Service` are the source of truth for the portal. The
frontend renders the catalog returned by the API and never owns launch targets.

Access is evaluated on the server in this order:

1. Service activation.
2. Staff-only requirement.
3. Scheduled or permanent user service restriction.

The launch endpoint repeats this policy check and records both successful and
denied attempts in `AuditEvent`.

## Integrated services

| Service | Type | Launch target |
|---|---|---|
| Professional reports | Internal | `/reports/new` |
| Excel contacts | Internal | `/tools/excel-contacts` |
| Business cards | External | `CARDNEST_URL` |

## Excel data handling

The uploaded workbook is processed by the Next.js Node route in memory. The
route validates file extension, size, required columns, phone numbers and email
addresses. It returns a generated ZIP containing VCF, cleaned rows, duplicates,
invalid rows and a summary. Uploaded contact data is not persisted.
