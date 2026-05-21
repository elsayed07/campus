import pytest
from django.urls import reverse

from apps.catalog.models import Course
from apps.content.models import Module
from core.enums import CourseState
from tests.factories import (
    CourseFactory,
    InstructorFactory,
    SubjectFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def test_instructor_creates_course_then_builds_and_publishes(client, password):
    instructor = InstructorFactory(password=password)
    subject = SubjectFactory()
    client.force_login(instructor)

    resp = client.post(
        reverse("catalog:course_create"),
        {
            "title": "Production Django",
            "subject": subject.id,
            "headline": "Ship real systems",
            "overview": "Deep dive.",
            "pricing_model": "free",
            "price": "0",
        },
    )
    assert resp.status_code == 302
    course = Course.objects.get(title="Production Django")

    add_module_url = reverse("content:add_module", args=[course.slug])
    resp = client.post(add_module_url, {"title": "Module 1"})
    assert resp.status_code == 200
    module = Module.objects.get(course=course)

    resp = client.post(reverse("content:add_lesson", args=[module.id]), {"title": "Lesson 1"})
    assert resp.status_code == 200

    resp = client.post(reverse("catalog:course_publish", args=[course.slug]))
    course.refresh_from_db()
    assert course.state == CourseState.PUBLISHED


def test_student_cannot_access_builder(client, password):
    student = UserFactory(password=password)
    course = CourseFactory()
    client.force_login(student)
    resp = client.get(reverse("content:course_builder", args=[course.slug]))
    assert resp.status_code in (403, 404)


def test_non_owner_instructor_cannot_build(client):
    course = CourseFactory()
    other = InstructorFactory()
    client.force_login(other)
    resp = client.get(reverse("content:course_builder", args=[course.slug]))
    assert resp.status_code == 404
