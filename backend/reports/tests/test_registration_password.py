"""B10: registration must enforce Django's password validators."""

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()

REGISTER_URL = "/api/auth/register/"


def _payload(password, **over):
    data = {"username": "b10user", "email": "b10@example.com", "password": password}
    data.update(over)
    return data


def test_common_password_is_rejected(api):
    resp = api.post(REGISTER_URL, _payload("secret123"), format="json")
    assert resp.status_code == 400
    assert "password" in resp.data["details"]
    assert not User.objects.filter(username="b10user").exists()


def test_numeric_only_password_is_rejected(api):
    resp = api.post(REGISTER_URL, _payload("98765432"), format="json")
    assert resp.status_code == 400
    assert "password" in resp.data["details"]


def test_password_similar_to_username_is_rejected(api):
    resp = api.post(
        REGISTER_URL,
        _payload("b10user99", username="b10user", email="b10@example.com"),
        format="json",
    )
    assert resp.status_code == 400
    assert "password" in resp.data["details"]


def test_strong_password_is_accepted(api):
    resp = api.post(REGISTER_URL, _payload("strongPa55phrase"), format="json")
    assert resp.status_code == 201
    assert User.objects.filter(username="b10user").exists()
