from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from reports.models import (
    AuditEvent,
    Service,
    ServiceCategory,
    UserServiceRestriction,
)
from reports.services_catalog.policy import service_access_for

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def service():
    category = ServiceCategory.objects.create(name="Office", slug="office")
    return Service.objects.create(
        category=category,
        name="Reports",
        slug="reports",
        description="Reports",
        kind=Service.Kind.INTERNAL,
        launch_target="/reports/new",
    )


def test_admin_api_rejects_regular_user(api, normal_user, login):
    login(normal_user)
    response = api.get("/api/v1/admin/dashboard/")
    assert response.status_code == 403


def test_admin_dashboard_returns_real_counts(api, admin_user, normal_user, login, service):
    login(admin_user)
    response = api.get("/api/v1/admin/dashboard/")
    assert response.status_code == 200
    assert response.data["summary"]["users"] == 2
    assert response.data["summary"]["services"] == 1


def test_admin_cannot_deactivate_current_account(api, admin_user, login):
    login(admin_user)
    response = api.post(
        f"/api/v1/admin/users/{admin_user.id}/deactivate/",
        {"reason": "Current session"},
        format="json",
    )
    assert response.status_code == 409
    admin_user.refresh_from_db()
    assert admin_user.is_active


def test_admin_deactivate_and_reactivate_user_is_audited(api, admin_user, normal_user, login):
    login(admin_user)
    disabled = api.post(
        f"/api/v1/admin/users/{normal_user.id}/deactivate/",
        {"reason": "Security review"},
        format="json",
    )
    assert disabled.status_code == 200
    normal_user.refresh_from_db()
    assert not normal_user.is_active
    assert normal_user.administration.disabled_reason == "Security review"

    enabled = api.post(f"/api/v1/admin/users/{normal_user.id}/activate/", {}, format="json")
    assert enabled.status_code == 200
    normal_user.refresh_from_db()
    assert normal_user.is_active
    assert AuditEvent.objects.filter(action="admin.user.deactivated", target_id=str(normal_user.id)).exists()


def test_deactivation_reason_is_optional(api, admin_user, normal_user, login):
    login(admin_user)
    response = api.post(f"/api/v1/admin/users/{normal_user.id}/deactivate/", {}, format="json")
    assert response.status_code == 200
    normal_user.refresh_from_db()
    assert not normal_user.is_active
    assert normal_user.administration.disabled_reason == ""


def test_bulk_restrictions_are_atomic_and_expired_rules_do_not_block(
    api, admin_user, normal_user, login, service
):
    login(admin_user)
    response = api.post(
        f"/api/v1/admin/users/{normal_user.id}/restrictions/",
        {"mode": "add", "service_ids": [service.id], "reason": "Temporary review"},
        format="json",
    )
    assert response.status_code == 200
    assert not service_access_for(normal_user, service).allowed

    restriction = UserServiceRestriction.objects.get(user=normal_user, service=service)
    restriction.expires_at = timezone.now() - timedelta(minutes=1)
    restriction.save(update_fields=["expires_at"])
    assert service_access_for(normal_user, service).allowed

    invalid = api.post(
        f"/api/v1/admin/users/{normal_user.id}/restrictions/",
        {"mode": "add", "service_ids": [service.id, 999999], "reason": "Should rollback"},
        format="json",
    )
    assert invalid.status_code == 400
    restriction.refresh_from_db()
    assert restriction.reason == "Temporary review"


def test_future_restriction_with_optional_reason_starts_on_schedule(
    api, admin_user, normal_user, login, service
):
    login(admin_user)
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(days=5)
    response = api.post(
        f"/api/v1/admin/users/{normal_user.id}/restrictions/",
        {
            "mode": "add",
            "service_ids": [service.id],
            "starts_at": start.isoformat(),
            "expires_at": end.isoformat(),
        },
        format="json",
    )
    assert response.status_code == 200
    assert service_access_for(normal_user, service).allowed

    restriction = UserServiceRestriction.objects.get(user=normal_user, service=service)
    assert restriction.reason == ""
    restriction.starts_at = timezone.now() - timedelta(minutes=1)
    restriction.save(update_fields=["starts_at"])
    assert not service_access_for(normal_user, service).allowed


def test_categories_are_not_exposed_in_admin_api(api, admin_user, login):
    login(admin_user)
    assert api.get("/api/v1/admin/categories/").status_code == 404


def test_service_deactivation_changes_catalog_access(api, admin_user, normal_user, login, service):
    login(admin_user)
    response = api.post(
        f"/api/v1/admin/services/{service.id}/deactivate/",
        {"reason": "Maintenance"},
        format="json",
    )
    assert response.status_code == 200
    service.refresh_from_db()
    assert not service.is_active
    assert not service_access_for(normal_user, service).allowed
