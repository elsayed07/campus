import pytest

from apps.chat.models import Message
from apps.chat.services import can_participate, post_message
from apps.enrollment.services import enrolling
from core.enums import CourseState
from shared.exceptions import PermissionDeniedError, ValidationError
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_owner_and_enrolled_can_participate():
    course = CourseFactory(state=CourseState.PUBLISHED)
    assert can_participate(user=course.owner, course=course) is True

    outsider = UserFactory()
    assert can_participate(user=outsider, course=course) is False

    enrolling.enroll(student=outsider, course=course)
    assert can_participate(user=outsider, course=course) is True


def test_post_message_persists_for_participant():
    course = CourseFactory(state=CourseState.PUBLISHED)
    student = UserFactory()
    enrolling.enroll(student=student, course=course)
    msg = post_message(course=course, author=student, body="Hi all")
    assert Message.objects.filter(id=msg.id, body="Hi all").exists()


def test_non_participant_cannot_post():
    course = CourseFactory(state=CourseState.PUBLISHED)
    with pytest.raises(PermissionDeniedError):
        post_message(course=course, author=UserFactory(), body="hello")


def test_empty_message_rejected():
    course = CourseFactory(state=CourseState.PUBLISHED)
    with pytest.raises(ValidationError):
        post_message(course=course, author=course.owner, body="   ")
