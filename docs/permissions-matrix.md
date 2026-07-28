# Permissions matrix

Roles map to Django groups; the code enforces ownership + staff today, with group names
reserved for richer mapping (see ADR-007).

| Capability | report_creator | template_manager | auditor | administrator |
|---|---|---|---|---|
| Login / view own profile | ✅ | ✅ | ✅ | ✅ |
| Create a report | ✅ | ✅ | ➖ | ✅ |
| View / download **own** reports | ✅ | ✅ | ➖ | ✅ |
| View / download **all** reports | ➖ | ➖ | ➖ | ✅ (staff) |
| List active report types | ✅ | ✅ | ✅ | ✅ |
| Create / edit report types & templates | ➖ | ✅ (staff) | ➖ | ✅ |
| Activate a template version | ➖ | ✅ (staff) | ➖ | ✅ |
| Read audit log (admin) | ➖ | ➖ | ✅ | ✅ |
| Django admin | ➖ | ➖ | ➖ | ✅ |

- All protections are server-side; hiding a UI control is not a permission.
- Object ownership: a report is visible/downloadable only by its creator or staff.
