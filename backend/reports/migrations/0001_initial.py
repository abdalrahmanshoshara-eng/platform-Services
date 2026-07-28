# Generated manually for the MVP.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=180)),
                ('slug', models.SlugField(max_length=180, unique=True)),
                ('description', models.TextField(blank=True)),
                ('template_file', models.CharField(help_text='DOCX filename inside reports/templates/reports/', max_length=255)),
                ('fields_schema', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='GeneratedReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('input_data', models.JSONField(default=dict)),
                ('docx_file', models.FileField(blank=True, null=True, upload_to='generated_reports/docx/')),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='generated_reports/pdf/')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generated_reports', to=settings.AUTH_USER_MODEL)),
                ('report_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='generated_reports', to='reports.reporttype')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['created_by', '-created_at'], name='reports_gen_created_d775bf_idx'),
                    models.Index(fields=['status'], name='reports_gen_status_b3120a_idx'),
                ],
            },
        ),
    ]
