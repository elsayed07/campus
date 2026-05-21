import pytest
from django.urls import reverse

from core.enums import Role
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_home_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200


def test_signup_creates_user_and_logs_in(client):
    response = client.post(
        reverse("accounts:signup"),
        {
            "email": "newlearner@campus.test",
            "full_name": "New Learner",
            "password1": "Sup3r-Secret-Pw",
            "password2": "Sup3r-Secret-Pw",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert response.wsgi_request.user.is_authenticated


def test_signup_as_instructor_sets_role(client):
    client.post(
        reverse("accounts:signup"),
        {
            "email": "teacher@campus.test",
            "full_name": "Teacher",
            "as_instructor": "on",
            "password1": "Sup3r-Secret-Pw",
            "password2": "Sup3r-Secret-Pw",
        },
    )
    from apps.accounts.models import User

    user = User.objects.get(email="teacher@campus.test")
    assert user.role == Role.INSTRUCTOR
    assert user.is_instructor


def test_login_with_email(client, password):
    user = UserFactory(password=password)
    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": password},
        follow=True,
    )
    assert response.status_code == 200
    assert response.wsgi_request.user.is_authenticated
