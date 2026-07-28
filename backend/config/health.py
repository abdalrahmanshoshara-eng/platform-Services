"""Liveness and readiness probes.

- /health/live  : process is up (no dependency checks).
- /health/ready : dependencies required to serve traffic are reachable.

Responses never expose credentials, hostnames, or internal error detail.
"""

from django.db import connection
from django.http import JsonResponse


def liveness(_request):
    return JsonResponse({"status": "ok"})


def readiness(_request):
    checks = {}
    healthy = True

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
        healthy = False

    # NOTE: Redis/broker readiness is added in Phase 9 alongside Celery.

    return JsonResponse(
        {"status": "ready" if healthy else "not_ready", "checks": checks},
        status=200 if healthy else 503,
    )
