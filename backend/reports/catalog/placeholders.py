"""Extract DOCX placeholders and check them against a field schema."""

from docxtpl import DocxTemplate

# Context keys the generator always injects (allowed even if not in the schema).
RESERVED_PLACEHOLDERS = {
    "report_title",
    "report_type_name",
    "created_by",
    "generated_at",
}


def extract_template_placeholders(docx_path) -> set[str]:
    template = DocxTemplate(str(docx_path))
    return set(template.get_undeclared_template_variables())


def validate_template_against_schema(placeholders, schema) -> None:
    from reports.shared.exceptions import DomainError

    schema_names = {f["name"] for f in schema if isinstance(f, dict) and f.get("name")}
    allowed = schema_names | RESERVED_PLACEHOLDERS
    unknown = set(placeholders) - allowed
    if unknown:
        raise DomainError(
            f"القالب يحتوي متغيرات غير معرّفة في المخطط: {', '.join(sorted(unknown))}",
            code="TEMPLATE_PLACEHOLDER_MISMATCH",
            status_code=400,
        )
