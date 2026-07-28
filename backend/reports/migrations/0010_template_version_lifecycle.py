from django.db import migrations, models


def normalize_active_versions(apps, schema_editor):
    Version = apps.get_model("reports", "ReportTemplateVersion")
    active_report_types = Version.objects.filter(status="active").values_list("report_type_id", flat=True).distinct()
    for report_type_id in active_report_types:
        active_ids = list(
            Version.objects.filter(
                report_type_id=report_type_id,
                status="active",
            )
            .order_by("-version", "-id")
            .values_list("id", flat=True)
        )
        if len(active_ids) > 1:
            Version.objects.filter(id__in=active_ids[1:]).update(status="inactive")


class Migration(migrations.Migration):
    dependencies = [("reports", "0009_auditevent_reports_aud_action_11faf8_idx")]

    operations = [
        migrations.RunPython(normalize_active_versions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="reporttemplateversion",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("validated", "Validated"),
                    ("active", "Active"),
                    ("inactive", "Inactive"),
                    ("archived", "Archived"),
                    ("rejected", "Rejected"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name="reporttemplateversion",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "active")),
                fields=("report_type",),
                name="one_active_template_per_report_type",
            ),
        ),
    ]
