"""B9: canonical v1 routes and temporary legacy aliases."""

import pytest
from django.urls import resolve, reverse
from rest_framework.schemas.generators import EndpointEnumerator

from config.urls import canonical_api_urlpatterns
from reports.models import Service, ServiceCategory, UserServiceRestriction

pytestmark = pytest.mark.django_db


def login(api, path, user):
    return api.post(
        path,
        {"username": user.username, "password": "pass12345"},
        format="json",
    )


def test_canonical_and_legacy_login_use_the_same_view(api, normal_user):
    canonical = login(api, "/api/v1/auth/login/", normal_user)
    api.cookies.clear()
    legacy = login(api, "/api/auth/login/", normal_user)

    assert canonical.status_code == legacy.status_code == 200
    assert canonical.data.keys() == legacy.data.keys()
    assert resolve("/api/v1/auth/login/").func.view_class is resolve("/api/auth/login/").func.view_class


def test_canonical_refresh_me_and_logout(api, normal_user):
    assert login(api, "/api/v1/auth/login/", normal_user).status_code == 200
    assert api.get("/api/v1/auth/me/").status_code == 200
    assert api.post("/api/v1/auth/refresh/").status_code == 200
    assert api.post("/api/v1/auth/logout/").status_code == 200
    assert api.get("/api/v1/auth/me/").status_code == 401


def test_canonical_reports_route_and_reverse_names(api, normal_user, report_type):
    api.force_authenticate(normal_user)
    response = api.get("/api/v1/reports/")

    assert response.status_code == 200
    assert reverse("generatedreport-list") == "/api/v1/reports/"
    assert reverse("auth-login") == "/api/v1/auth/login/"
    assert reverse("legacy_api:generatedreport-list") == "/api/reports/"


def test_canonical_and_legacy_services_have_equivalent_shapes(api, normal_user):
    category = ServiceCategory.objects.create(name="Tools", slug="tools")
    Service.objects.create(
        category=category,
        name="Example",
        slug="example",
        description="Example",
        kind=Service.Kind.INTERNAL,
        launch_target="/tools/example",
    )
    api.force_authenticate(normal_user)

    canonical = api.get("/api/v1/services/")
    legacy = api.get("/api/services/")

    assert canonical.status_code == legacy.status_code == 200
    assert canonical.data == legacy.data


def test_legacy_alias_preserves_permissions(api):
    assert api.get("/api/v1/reports/").status_code == 401
    assert api.get("/api/reports/").status_code == 401


def test_restriction_cannot_be_bypassed_through_legacy_alias(api, normal_user):
    category = ServiceCategory.objects.create(name="Tools", slug="restricted-tools")
    service = Service.objects.create(
        category=category,
        name="Restricted",
        slug="restricted",
        description="Restricted",
        kind=Service.Kind.INTERNAL,
        launch_target="/tools/restricted",
    )
    UserServiceRestriction.objects.create(user=normal_user, service=service)
    api.force_authenticate(normal_user)

    canonical = api.post("/api/v1/services/restricted/launch/")
    legacy = api.post("/api/services/restricted/launch/")

    assert canonical.status_code == legacy.status_code == 403
    assert canonical.data["code"] == legacy.data["code"] == "SERVICE_ACCESS_DENIED"


def test_canonical_excel_contacts_route_is_active(api, normal_user):
    category = ServiceCategory.objects.create(name="Productivity", slug="productivity")
    Service.objects.create(
        category=category,
        name="Excel Contacts",
        slug="whatsapp-contacts",
        description="Prepare contacts",
        kind=Service.Kind.INTERNAL,
        launch_target="/tools/excel-contacts",
    )
    api.force_authenticate(normal_user)

    response = api.post(
        "/api/v1/tools/excel-contacts/process/",
        {"countryCode": "963"},
        format="multipart",
    )

    assert response.status_code == 400
    assert response.data["code"] == "VALIDATION_ERROR"


def test_canonical_admin_route_remains_unchanged(api, admin_user):
    api.force_authenticate(admin_user)
    assert api.get("/api/v1/admin/dashboard/").status_code == 200


def test_schema_inventory_is_canonical_and_has_unique_operations():
    endpoints = EndpointEnumerator(
        patterns=canonical_api_urlpatterns,
    ).get_api_endpoints()
    paths = [path for path, _method, _callback in endpoints]
    operations = [(path, method) for path, method, _callback in endpoints]
    operation_ids = []
    for _path, method, callback in endpoints:
        action = getattr(callback, "actions", {}).get(method.lower(), method.lower())
        operation_ids.append(f"{callback.cls.__name__}_{action}")

    assert endpoints
    assert all(path.startswith("/api/v1/") for path in paths)
    assert not any(path.startswith("/api/") and not path.startswith("/api/v1/") for path in paths)
    assert len(operations) == len(set(operations))
    assert len(operation_ids) == len(set(operation_ids))
