"""B11/B12: admin analytics must aggregate without per-service N+1 queries."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from reports.models import AuditEvent, Service, ServiceCategory, UserServiceRestriction

pytestmark = pytest.mark.django_db

URL = "/api/v1/admin/analytics/"


def _service(category, slug):
    return Service.objects.create(
        category=category,
        name=slug,
        slug=slug,
        description=slug,
        kind=Service.Kind.INTERNAL,
        launch_target=f"/tools/{slug}",
    )


def _launch(service, outcome):
    AuditEvent.objects.create(
        action="service.launch", target_type="Service", target_id=str(service.id), outcome=outcome
    )


def test_analytics_counts_are_correct(api, admin_user, normal_user, login):
    category = ServiceCategory.objects.create(name="Cat", slug="cat")
    s1 = _service(category, "one")
    s2 = _service(category, "two")
    _launch(s1, "success")
    _launch(s1, "success")
    _launch(s1, "denied")
    UserServiceRestriction.objects.create(user=normal_user, service=s1)

    login(admin_user)
    resp = api.get(URL)
    assert resp.status_code == 200
    by_id = {row["id"]: row for row in resp.data["services"]}
    assert by_id[s1.id]["launches"] == 2
    assert by_id[s1.id]["denied"] == 1
    assert by_id[s1.id]["restricted_users"] == 1
    assert by_id[s2.id]["launches"] == 0
    assert by_id[s2.id]["denied"] == 0
    assert by_id[s2.id]["restricted_users"] == 0


def test_analytics_query_count_does_not_grow_with_services(api, admin_user, login):
    category = ServiceCategory.objects.create(name="Cat", slug="cat")
    for i in range(2):
        _service(category, f"svc{i}")

    login(admin_user)
    api.get(URL)  # warm any first-request auth caching

    with CaptureQueriesContext(connection) as small:
        api.get(URL)

    for i in range(2, 7):  # add 5 more services
        _service(category, f"svc{i}")

    with CaptureQueriesContext(connection) as large:
        api.get(URL)

    # A per-service N+1 would add ~3 queries per new service; aggregation keeps it flat.
    assert len(large) == len(small)
