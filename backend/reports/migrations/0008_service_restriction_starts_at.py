from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0007_admin_control_center"),
    ]

    operations = [
        migrations.AddField(
            model_name="userservicerestriction",
            name="starts_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
