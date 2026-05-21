import pytest
from django.urls import reverse

from apps.content.services import structure
from apps.enrollment.services import enrolling
from core.enums import CourseState
from tests.factories import CourseFactory, InstructorFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_instructor_dashboard_renders(client, password):
    instructor = InstructorFactory(password=password)
    course = CourseFactory(state=CourseState.PUBLISHED, owner=instructor)
    module = structure.add_module(course=course, title="M")
    structure.add_lesson(module=module, title="L")
    enrolling.enroll(student=UserFactory(), course=course)

    client.force_login(instructor)
    resp = client.get(reverse("analytics:dashboard"))
    assert resp.status_code == 200
    assert course.title.encode() in resp.content


def test_student_cannot_view_analytics(client, password):
    student = UserFactory(password=password)
    client.force_login(student)
    resp = client.get(reverse("analytics:dashboard"))
    assert resp.status_code in (403, 404)
