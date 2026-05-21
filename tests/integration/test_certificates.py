import pytest

from apps.certificates.models import Certificate
from apps.content.services import structure
from apps.enrollment.services import enrolling
from apps.progress.services import tracking
from core.enums import CourseState
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_certificate_is_issued_and_rendered_on_completion(
    django_capture_on_commit_callbacks,
):
    course = CourseFactory(state=CourseState.PUBLISHED)
    module = structure.add_module(course=course, title="M")
    lesson = structure.add_lesson(module=module, title="Only lesson")
    student = UserFactory()
    enrollment = enrolling.enroll(student=student, course=course)

    with django_capture_on_commit_callbacks(execute=True):
        tracking.mark_lesson_complete(enrollment=enrollment, lesson=lesson)

    certificate = Certificate.objects.get(enrollment=enrollment)
    assert certificate.serial.startswith("CMP-")
    # Celery runs eagerly in tests, so the PDF is rendered synchronously.
    certificate.refresh_from_db()
    assert certificate.is_ready
    assert certificate.pdf.name.endswith(".pdf")


def test_certificate_issuance_is_idempotent(django_capture_on_commit_callbacks):
    from apps.certificates.services import issue_certificate

    course = CourseFactory(state=CourseState.PUBLISHED)
    student = UserFactory()
    enrollment = enrolling.enroll(student=student, course=course)

    with django_capture_on_commit_callbacks(execute=True):
        issue_certificate(enrollment=enrollment)
        issue_certificate(enrollment=enrollment)

    assert Certificate.objects.filter(enrollment=enrollment).count() == 1
