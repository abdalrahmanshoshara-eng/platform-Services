"""Explicit development seed. Run on demand only: `python manage.py seed_dev_data`.

Never invoked automatically. Uses passwords from the environment.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed development accounts and report types (explicit, on-demand only)."

    def handle(self, *args, **options):
        # Reuse the existing seeding logic.
        call_command("seed_initial_data")
        self.stdout.write(self.style.SUCCESS("Development data seeded."))
