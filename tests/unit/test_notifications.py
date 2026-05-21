import pytest

from apps.content.services import structure
from apps.enrollment.services import enrolling
from apps.notifications import selectors, services
from apps.notifications.models import Notification
from apps.progress.services import tracking
from core.enums import CourseState, NotificationKind
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_notify_creates_unread_notification():
    user = UserFactory()
    services.notify(recipient=user, kind=NotificationKind.SYSTEM, title="Welcome")
    assert selectors.unread_count(user=user) == 1


def test_mark_all_read():
    user = UserFactory()
    for _ in range(3):
        services.notify(recipient=user, kind=NotificationKind.SYSTEM, title="x")
    services.mark_all_read(user=user)
    assert selectors.unread_count(user=user) == 0


def test_enrolling_notifies_student():
    course = CourseFactory(state=CourseState.PUBLISHED)
    student = UserFactory()
    enrolling.enroll(student=student, course=course)
    assert Notification.objects.filter(
        recipient=student, kind=NotificationKind.ENROLLMENT
    ).exists()


def test_course_completion_notifies(django_capture_on_commit_callbacks):
    course = CourseFactory(state=CourseState.PUBLISHED)
    module = structure.add_module(course=course, title="M")
    lesson = structure.add_lesson(module=module, title="L")
    student = UserFactory()
    enrollment = enrolling.enroll(student=student, course=course)

    with django_capture_on_commit_callbacks(execute=True):
        tracking.mark_lesson_complete(enrollment=enrollment, lesson=lesson)

    assert Notification.objects.filter(
        recipient=student, kind=NotificationKind.PROGRESS
    ).exists()
