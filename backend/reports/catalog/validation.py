"""Central validation for field schemas and report input.

The backend is the single source of truth for validation. Do NOT duplicate these
rules in serializers or the frontend (the frontend may mirror them for UX only).
"""

from datetime import datetime

from reports.shared.exceptions import DomainError

SUPPORTED_TYPES = {"text", "textarea", "date", "select", "number"}


class SchemaError(DomainError):
    code = "INVALID_FIELDS_SCHEMA"
    status_code = 400
    message = "مخطط الحقول غير صالح."


class InputError(DomainError):
    code = "INVALID_REPORT_INPUT"
    status_code = 400
    message = "بيانات التقرير غير صالحة."


def validate_fields_schema(schema) -> list:
    if not isinstance(schema, list):
        raise SchemaError("fields_schema يجب أن يكون قائمة.")
    seen = set()
    for index, field in enumerate(schema):
        if not isinstance(field, dict):
            raise SchemaError(f"الحقل رقم {index} يجب أن يكون كائناً.")
        name = field.get("name")
        if not name or not isinstance(name, str):
            raise SchemaError(f"الحقل رقم {index} يفتقد معرفاً صالحاً (name).")
        if name in seen:
            raise SchemaError(f"معرّف حقل مكرر: {name}")
        seen.add(name)
        ftype = field.get("type", "text")
        if ftype not in SUPPORTED_TYPES:
            raise SchemaError(f"نوع حقل غير مدعوم: {ftype}")
        if ftype == "select":
            options = field.get("options")
            if not isinstance(options, list) or not options:
                raise SchemaError(f"الحقل '{name}' من نوع select ويجب أن يملك options.")
        for bound in ("min_length", "max_length"):
            if bound in field and not isinstance(field[bound], int):
                raise SchemaError(f"{bound} للحقل '{name}' يجب أن يكون عدداً صحيحاً.")
        if "min_length" in field and "max_length" in field and field["min_length"] > field["max_length"]:
            raise SchemaError(f"min_length أكبر من max_length للحقل '{name}'.")
    return schema


def validate_report_input(schema, data) -> dict:
    if not isinstance(data, dict):
        raise InputError("input_data يجب أن يكون كائناً JSON.")

    known = {f["name"] for f in schema if isinstance(f, dict) and f.get("name")}
    unknown = set(data) - known
    if unknown:
        raise InputError(f"حقول غير معروفة: {', '.join(sorted(unknown))}")

    errors = {}
    for field in schema:
        name = field.get("name")
        if not name:
            continue
        raw = data.get(name)
        is_empty = raw is None or str(raw).strip() == ""
        if field.get("required") and is_empty:
            errors[name] = "هذا الحقل مطلوب."
            continue
        if is_empty:
            continue
        ftype = field.get("type", "text")
        value = str(raw)
        if ftype == "select" and value not in (field.get("options") or []):
            errors[name] = "قيمة غير مسموحة."
        elif ftype == "date" and not _is_iso_date(value):
            errors[name] = "صيغة التاريخ يجب أن تكون YYYY-MM-DD."
        elif ftype == "number" and not _is_number(value):
            errors[name] = "يجب أن تكون قيمة رقمية."
        else:
            mn, mx = field.get("min_length"), field.get("max_length")
            if isinstance(mn, int) and len(value) < mn:
                errors[name] = f"الحد الأدنى للطول {mn}."
            elif isinstance(mx, int) and len(value) > mx:
                errors[name] = f"الحد الأقصى للطول {mx}."
    if errors:
        raise InputError("بيانات غير صالحة.", details=errors)
    return data


def _is_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False
