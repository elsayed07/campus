import pytest
from django.urls import reverse

from apps.content.services import structure
from core.enums import CourseState, EnrollmentStatus
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def _published_course_with_two_lessons():
    course = CourseFactory(state=CourseState.PUBLISHED)
    module = structure.add_module(course=course, title="M1")
    l0 = structure.add_lesson(module=module, title="L0")
    structure.add_content_item(
        lesson=l0, kind="text", title="Intro", body="# Hello\n\nSome **markdown**."
    )
    l1 = structure.add_lesson(module=module, title="L1")
    return course, [l0, l1]


def test_full_learning_flow(client, password):
    course, lessons = _published_course_with_two_lessons()
    student = UserFactory(password=password)
    client.force_login(student)

    # Enroll
    resp = client.post(reverse("enrollment:enroll", args=[course.slug]))
    assert resp.status_code == 302

    # Classroom reachable
    assert client.get(reverse("progress:classroom", args=[course.slug])).status_code == 200

    # Lesson page renders (exercises the markdown content renderer)
    lesson_resp = client.get(reverse("progress:lesson", args=[course.slug, lessons[0].id]))
    assert lesson_resp.status_code == 200
    assert b"markdown" in lesson_resp.content

    # Complete first lesson → redirected to the next
    resp = client.post(
        reverse("progress:complete_lesson", args=[course.slug, lessons[0].id])
    )
    assert resp.status_code == 302

    # Complete second lesson → enrollment completed
    client.post(reverse("progress:complete_lesson", args=[course.slug, lessons[1].id]))
    enrollment = course.enrollments.get(student=student)
    assert enrollment.status == EnrollmentStatus.COMPLETED


def test_cannot_enter_classroom_without_enrollment(client, password):
    course, _ = _published_course_with_two_lessons()
    client.force_login(UserFactory(password=password))
    assert client.get(reverse("progress:classroom", args=[course.slug])).status_code == 404


def test_cannot_complete_locked_lesson_directly(client, password):
    course = CourseFactory(state=CourseState.PUBLISHED)
    module = structure.add_module(course=course, title="M1")
    structure.add_lesson(module=module, title="L0")
    locked = structure.add_lesson(module=module, title="L1")
    student = UserFactory(password=password)
    client.force_login(student)
    client.post(reverse("enrollment:enroll", args=[course.slug]))

    resp = client.post(
        reverse("progress:complete_lesson", args=[course.slug, locked.id])
    )
    assert resp.status_code == 404
