"""B4: enable/disable state must change only through audited actions."""

import pytest

from reports.admin import ReportTemplateVersionAdmin, ServiceAdmin
from reports.models import AuditEvent, Service, ServiceCategory

pytestmark = pytest.mark.django_db


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


def test_patch_cannot_disable_service(api, admin_user, login, service):
    login(admin_user)
    response = api.patch(
        f"/api/v1/admin/services/{service.id}/",
        {"is_active": False},
        format="json",
    )
    # The field is read-only: the request succeeds but the flag is ignored.
    assert response.status_code == 200
    service.refresh_from_db()
    assert service.is_active is True
    assert not AuditEvent.objects.filter(action="admin.service.deactivated").exists()


def test_patch_can_still_edit_non_state_fields(api, admin_user, login, service):
    login(admin_user)
    response = api.patch(
        f"/api/v1/admin/services/{service.id}/",
        {"sort_order": 7},
        format="json",
    )
    assert response.status_code == 200
    service.refresh_from_db()
    assert service.sort_order == 7
    assert service.is_active is True


def test_audited_deactivate_action_still_works(api, admin_user, login, service):
    login(admin_user)
    response = api.post(
        f"/api/v1/admin/services/{service.id}/deactivate/",
        {"reason": "Maintenance"},
        format="json",
    )
    assert response.status_code == 200
    service.refresh_from_db()
    assert service.is_active is False
    assert service.disabled_reason == "Maintenance"
    assert service.disabled_by_id == admin_user.id
    assert service.disabled_at is not None
    assert AuditEvent.objects.filter(
        action="admin.service.deactivated", target_id=str(service.id)
    ).exists()


def test_django_admin_state_fields_are_locked():
    assert "is_active" not in ServiceAdmin.list_editable
    assert "is_active" in ServiceAdmin.readonly_fields
    assert "status" in ReportTemplateVersionAdmin.readonly_fields
