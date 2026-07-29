import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from reports.models import Service, ServiceCategory, UserServiceRestriction


@pytest.fixture
def public_service():
    category = ServiceCategory.objects.create(
        name="خدمات المستندات",
        slug="documents",
        description="أدوات إعداد المستندات.",
    )
    return Service.objects.create(
        category=category,
        name="منشئ التقارير",
        slug="report-builder",
        description="أنشئ تقريراً احترافياً.",
        kind=Service.Kind.INTERNAL,
        launch_target="/reports/new",
    )


@pytest.mark.django_db
def test_service_catalog_is_public_but_marks_usage_as_requiring_login(public_service):
    client = APIClient()
    response = client.get("/api/v1/services/")
    legacy_response = client.get("/api/services/")

    assert response.status_code == legacy_response.status_code == 200
    assert response.data == legacy_response.data
    assert response.data[0]["slug"] == public_service.slug
    assert response.data[0]["is_available"] is False
    assert response.data[0]["restriction_reason"] == "سجّل الدخول لاستخدام هذه الخدمة."


@pytest.mark.django_db
def test_anonymous_user_cannot_launch_publicly_listed_service(public_service):
    response = APIClient().post(f"/api/v1/services/{public_service.slug}/launch/")

    assert response.status_code == 401
    assert response.data["code"] == "NOT_AUTHENTICATED"


@pytest.mark.django_db
def test_service_catalog_marks_user_restrictions():
    user = get_user_model().objects.create_user(username="catalog-user", password="secret123")
    category = ServiceCategory.objects.create(name="Tools", slug="tools")
    service = Service.objects.create(
        category=category,
        name="External",
        slug="external",
        description="External tool",
        kind=Service.Kind.EXTERNAL,
        launch_target="https://example.com/login",
    )
    UserServiceRestriction.objects.create(user=user, service=service, reason="موقوفة لهذا الحساب.")
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/services/")

    assert response.status_code == 200
    assert response.data[0]["is_available"] is False
    assert response.data[0]["restriction_reason"] == "موقوفة لهذا الحساب."


@pytest.mark.django_db
def test_service_launch_returns_server_owned_target():
    user = get_user_model().objects.create_user(username="launcher", password="secret123")
    category = ServiceCategory.objects.create(name="Tools", slug="tools")
    Service.objects.create(
        category=category,
        name="Internal",
        slug="internal",
        description="Internal tool",
        kind=Service.Kind.INTERNAL,
        launch_target="/tools/example",
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.post("/api/services/internal/launch/")

    assert response.status_code == 200
    assert response.data == {"target": "/tools/example", "kind": "internal"}


@pytest.mark.django_db
def test_register_and_login_with_email():
    client = APIClient()
    registered = client.post(
        "/api/auth/register/",
        {"username": "new-user", "email": "new@example.com", "password": "strongPa55phrase"},
        format="json",
    )
    assert registered.status_code == 201

    client.cookies.clear()
    logged_in = client.post(
        "/api/auth/login/",
        {"username": "new@example.com", "password": "strongPa55phrase"},
        format="json",
    )
    assert logged_in.status_code == 200
    assert logged_in.data["user"]["username"] == "new-user"
