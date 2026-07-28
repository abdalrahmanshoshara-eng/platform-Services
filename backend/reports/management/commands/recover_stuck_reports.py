"""Requeue reports stuck in 'processing' beyond a threshold (worker crash recovery)."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from reports.generation.application import RetryReportUseCase
from reports.generation.domain import transition
from reports.models import GeneratedReport


class Command(BaseCommand):
    help = "Requeue reports stuck in processing longer than --minutes (default 30)."

    def add_arguments(self, parser):
        parser.add_argument("--minutes", type=int, default=30)

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(minutes=options["minutes"])
        stuck = GeneratedReport.objects.filter(status=GeneratedReport.Status.PROCESSING, started_at__lt=threshold)
        count = 0
        for report in stuck:
            # Move processing -> failed through the state machine (the single source of
            # truth for transitions) so the subsequent retry is allowed to requeue it.
            transition(report, GeneratedReport.Status.FAILED)
            RetryReportUseCase().execute(report=report)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Requeued {count} stuck report(s)."))
