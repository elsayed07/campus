import pytest

from apps.content.services import structure
from core.enums import CourseState
from tests.factories import CourseFactory, InstructorFactory, UserFactory

pytestmark = pytest.mark.django_db

BASE = "/api/v1"


def _token(client, user, password):
    user.set_password(password)
    user.save()
    resp = client.post(
        f"{BASE}/auth/token",
        data={"email": user.email, "password": password},
        content_type="application/json",
    )
    assert resp.status_code == 200, resp.content
    return resp.json()["access"]


def _published_course_with_lessons():
    course = CourseFactory(state=CourseState.PUBLISHED, owner=InstructorFactory())
    module = structure.add_module(course=course, title="M1")
    l0 = structure.add_lesson(module=module, title="L0")
    l1 = structure.add_lesson(module=module, title="L1")
    return course, [l0, l1]


def test_public_course_list_and_detail(client):
    course, _ = _published_course_with_lessons()
    assert client.get(f"{BASE}/courses/").status_code == 200

    detail = client.get(f"{BASE}/courses/{course.slug}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["slug"] == course.slug
    assert len(data["modules"]) == 1


def test_protected_endpoint_requires_token(client):
    assert client.get(f"{BASE}/enrollments").status_code == 401


def test_token_auth_and_enroll_flow(client, password):
    course, lessons = _published_course_with_lessons()
    student = UserFactory()
    token = _token(client, student, password)
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    enroll = client.post(f"{BASE}/courses/{course.slug}/enroll", **headers)
    assert enroll.status_code == 200
    assert enroll.json()["status"] == "active"

    room = client.get(f"{BASE}/courses/{course.slug}/classroom", **headers)
    assert room.status_code == 200
    body = room.json()
    assert body["total"] == 2
    assert body["progress_percent"] == 0

    complete = client.post(
        f"{BASE}/courses/{course.slug}/lessons/{lessons[0].id}/complete", **headers
    )
    assert complete.status_code == 200
    assert complete.json()["progress_percent"] == 50


def test_invalid_credentials_rejected(client):
    UserFactory(email="known@campus.test")
    resp = client.post(
        f"{BASE}/auth/token",
        data={"email": "known@campus.test", "password": "wrong"},
        content_type="application/json",
    )
    assert resp.status_code == 403


def test_forum_thread_via_api(client, password):
    course, _ = _published_course_with_lessons()
    student = UserFactory()
    token = _token(client, student, password)
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    client.post(f"{BASE}/courses/{course.slug}/enroll", **headers)

    resp = client.post(
        f"{BASE}/courses/{course.slug}/threads",
        data={"title": "Question", "body": "How?"},
        content_type="application/json",
        **headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Question"
    assert len(resp.json()["posts"]) == 1
