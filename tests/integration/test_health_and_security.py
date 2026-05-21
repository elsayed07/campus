import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_healthz_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db"] is True


@override_settings(RATELIMIT_ENABLE=True)
def test_login_is_rate_limited(client, password):
    cache.clear()
    UserFactory(email="rl@campus.test", password=password)
    url = reverse("accounts:login")
    statuses = [
        client.post(url, {"username": "rl@campus.test", "password": "nope"}).status_code
        for _ in range(11)
    ]
    assert statuses[-1] == 403  # 11th request in the window is blocked
    cache.clear()
