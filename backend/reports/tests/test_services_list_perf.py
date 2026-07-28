"""B13: the services list computes access decisions in a bounded number of queries
(no per-service N+1), confirming the B2 policy refactor holds."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from reports.models import Service, ServiceCategory, UserServiceRestriction

pytestmark = pytest.mark.django_db


def _service(category, slug):
    return Service.objects.create(
        category=category,
        name=slug,
        slug=slug,
        description=slug,
        kind=Service.Kind.INTERNAL,
        launch_target=f"/tools/{slug}",
    )


def test_services_list_query_count_is_flat(normal_user):
    category = ServiceCategory.objects.create(name="Cat", slug="cat")
    for i in range(2):
        _service(category, f"svc{i}")
    # A restriction ensures the policy's restriction lookups are exercised.
    UserServiceRestriction.objects.create(user=normal_user, service=Service.objects.first())

    client = APIClient()
    client.force_authenticate(normal_user)
    client.get("/api/services/")  # warm

    with CaptureQueriesContext(connection) as small:
        client.get("/api/services/")

    for i in range(2, 8):
        _service(category, f"svc{i}")

    with CaptureQueriesContext(connection) as large:
        client.get("/api/services/")

    assert len(large) == len(small)
