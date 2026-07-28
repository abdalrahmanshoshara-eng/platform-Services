from datetime import timedelta

import pytest
from django.utils import timezone

from reports.models import (
    AuditEvent,
    Service,
    ServiceCategory,
    UserCategoryRestriction,
    UserServiceRestriction,
)
from reports.services_catalog.policy import service_access_for

pytestmark = pytest.mark.django_db


@pytest.fixture
def category_a():
    return ServiceCategory.objects.create(name="Images", slug="images")


@pytest.fixture
def category_b():
    return ServiceCategory.objects.create(name="Documents", slug="documents")


def _service(category, slug):
    return Service.objects.create(
        category=category,
        name=slug,
        slug=slug,
        description=slug,
        kind=Service.Kind.INTERNAL,
        launch_target=f"/tools/{slug}",
    )


@pytest.fixture
def service_a1(category_a):
    return _service(category_a, "compress")


@pytest.fixture
def service_a2(category_a):
    return _service(category_a, "resize")


@pytest.fixture
def service_b(category_b):
    return _service(category_b, "word")


# --- Policy behaviour -------------------------------------------------------

def test_user_without_restrictions_is_allowed(normal_user, service_a1):
    decision = service_access_for(normal_user, service_a1)
    assert decision.allowed
    assert decision.code == "ALLOWED"


def test_active_direct_service_restriction_denies(normal_user, service_a1):
    UserServiceRestriction.objects.create(user=normal_user, service=service_a1, reason="direct")
    decision = service_access_for(normal_user, service_a1)
    assert not decision.allowed
    assert decision.code == "SERVICE_RESTRICTION"


def test_active_category_restriction_denies_every_service_in_category(
    normal_user, category_a, service_a1, service_a2
):
    UserCategoryRestriction.objects.create(user=normal_user, category=category_a, reason="whole category")
    for service in (service_a1, service_a2):
        decision = service_access_for(normal_user, service)
        assert not decision.allowed
        assert decision.code == "CATEGORY_RESTRICTION"
        assert decision.reason == "whole category"


def test_category_restriction_does_not_affect_other_category(
    normal_user, category_a, service_a1, service_b
):
    UserCategoryRestriction.objects.create(user=normal_user, category=category_a)
    assert not service_access_for(normal_user, service_a1).allowed
    assert service_access_for(normal_user, service_b).allowed


def test_expired_category_restriction_does_not_deny(normal_user, category_a, service_a1):
    UserCategoryRestriction.objects.create(
        user=normal_user,
        category=category_a,
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    assert service_access_for(normal_user, service_a1).allowed
    # Access evaluation must not delete the historical (expired) row.
    assert UserCategoryRestriction.objects.filter(user=normal_user, category=category_a).exists()


def test_disabled_user_is_denied(normal_user, service_a1):
    normal_user.is_active = False
    normal_user.save(update_fields=["is_active"])
    decision = service_access_for(normal_user, service_a1)
    assert not decision.allowed
    assert decision.code == "ACCOUNT_DISABLED"


def test_disabled_service_is_denied(normal_user, service_a1):
    service_a1.is_active = False
    service_a1.save(update_fields=["is_active"])
    decision = service_access_for(normal_user, service_a1)
    assert not decision.allowed
    assert decision.code == "SERVICE_DISABLED"


# --- Admin API --------------------------------------------------------------

def test_regular_user_cannot_call_category_restriction_endpoint(
    api, normal_user, login, category_a
):
    login(normal_user)
    response = api.post(
        f"/api/v1/admin/users/{normal_user.id}/category-restrictions/",
        {"mode": "add", "category_ids": [category_a.id]},
        format="json",
    )
    assert response.status_code == 403
    assert not UserCategoryRestriction.objects.exists()


def test_admin_can_bulk_create_category_restrictions(
    api, admin_user, normal_user, login, category_a, category_b, service_a1, service_b
):
    login(admin_user)
    response = api.post(
        f"/api/v1/admin/users/{normal_user.id}/category-restrictions/",
        {"mode": "add", "category_ids": [category_a.id, category_b.id], "reason": "policy"},
        format="json",
    )
    assert response.status_code == 200
    assert UserCategoryRestriction.objects.filter(user=normal_user).count() == 2
    assert not service_access_for(normal_user, service_a1).allowed
    assert not service_access_for(normal_user, service_b).allowed


def test_admin_can_bulk_remove_category_restrictions(
    api, admin_user, normal_user, login, category_a, service_a1
):
    UserCategoryRestriction.objects.create(user=normal_user, category=category_a)
    login(admin_user)
    response = api.post(
        f"/api/v1/admin/users/{normal_user.id}/category-restrictions/",
        {"mode": "remove", "category_ids": [category_a.id]},
        format="json",
    )
    assert response.status_code == 200
    assert not UserCategoryRestriction.objects.filter(user=normal_user).exists()
    assert service_access_for(normal_user, service_a1).allowed


def test_duplicate_creation_is_deterministic(
    api, admin_user, normal_user, login, category_a
):
    login(admin_user)
    url = f"/api/v1/admin/users/{normal_user.id}/category-restrictions/"
    api.post(url, {"mode": "add", "category_ids": [category_a.id], "reason": "first"}, format="json")
    api.post(url, {"mode": "add", "category_ids": [category_a.id], "reason": "second"}, format="json")
    rows = UserCategoryRestriction.objects.filter(user=normal_user, category=category_a)
    assert rows.count() == 1
    assert rows.first().reason == "second"


def test_bulk_operation_is_atomic_when_one_input_is_invalid(
    api, admin_user, normal_user, login, category_a
):
    UserCategoryRestriction.objects.create(user=normal_user, category=category_a, reason="original")
    login(admin_user)
    response = api.post(
        f"/api/v1/admin/users/{normal_user.id}/category-restrictions/",
        {"mode": "add", "category_ids": [category_a.id, 999999], "reason": "should rollback"},
        format="json",
    )
    assert response.status_code == 400
    row = UserCategoryRestriction.objects.get(user=normal_user, category=category_a)
    assert row.reason == "original"


def test_audit_event_written_for_successful_bulk_change(
    api, admin_user, normal_user, login, category_a
):
    login(admin_user)
    api.post(
        f"/api/v1/admin/users/{normal_user.id}/category-restrictions/",
        {"mode": "add", "category_ids": [category_a.id], "reason": "audited"},
        format="json",
    )
    assert AuditEvent.objects.filter(
        action="admin.category_restrictions.add", target_id=str(normal_user.id)
    ).exists()


def test_direct_launch_request_cannot_bypass_category_restriction(
    api, normal_user, login, category_a, service_a1
):
    UserCategoryRestriction.objects.create(user=normal_user, category=category_a)
    login(normal_user)
    response = api.post(f"/api/services/{service_a1.slug}/launch/")
    assert response.status_code == 403
    assert response.data["code"] == "SERVICE_ACCESS_DENIED"
