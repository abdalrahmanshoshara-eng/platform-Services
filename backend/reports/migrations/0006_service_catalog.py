from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("reports", "0005_audit_event"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("description", models.CharField(blank=True, max_length=240)),
                ("icon", models.CharField(blank=True, max_length=40)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["sort_order", "name"], "verbose_name_plural": "service categories"},
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=140)),
                ("slug", models.SlugField(max_length=140, unique=True)),
                ("description", models.CharField(max_length=320)),
                ("kind", models.CharField(choices=[("internal", "Internal"), ("external", "External")], max_length=16)),
                ("launch_target", models.CharField(help_text="Internal route beginning with / or an HTTPS external URL.", max_length=500)),
                ("icon", models.CharField(blank=True, max_length=40)),
                ("accent", models.CharField(default="green", max_length=20)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("requires_staff", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="services", to="reports.servicecategory")),
            ],
            options={"ordering": ["category__sort_order", "sort_order", "name"]},
        ),
        migrations.CreateModel(
            name="UserCategoryRestriction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(blank=True, max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_restrictions", to="reports.servicecategory")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="category_restrictions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("user", "category")}},
        ),
        migrations.CreateModel(
            name="UserServiceRestriction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(blank=True, max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("service", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_restrictions", to="reports.service")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="service_restrictions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("user", "service")}},
        ),
    ]
