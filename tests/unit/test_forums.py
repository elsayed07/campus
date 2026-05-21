import pytest

from apps.enrollment.services import enrolling
from apps.forums.models import Post, Thread
from apps.forums.services import discussions
from apps.notifications.models import Notification
from core.enums import CourseState, NotificationKind
from shared.exceptions import PermissionDeniedError, ValidationError
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def _enrolled(course):
    student = UserFactory()
    enrolling.enroll(student=student, course=course)
    return student


def test_create_thread_makes_first_post():
    course = CourseFactory(state=CourseState.PUBLISHED)
    student = _enrolled(course)
    thread = discussions.create_thread(
        course=course, author=student, title="How do migrations work?", body="Confused."
    )
    assert Thread.objects.filter(id=thread.id).exists()
    assert Post.objects.filter(thread=thread).count() == 1


def test_non_participant_cannot_create_thread():
    course = CourseFactory(state=CourseState.PUBLISHED)
    with pytest.raises(PermissionDeniedError):
        discussions.create_thread(
            course=course, author=UserFactory(), title="x", body="y"
        )


def test_reply_notifies_thread_author():
    course = CourseFactory(state=CourseState.PUBLISHED)
    thread = discussions.create_thread(
        course=course, author=course.owner, title="Welcome", body="Say hi"
    )
    student = _enrolled(course)
    discussions.reply(thread=thread, author=student, body="Hi!")
    assert Notification.objects.filter(
        recipient=course.owner, kind=NotificationKind.FORUM_REPLY
    ).exists()


def test_cannot_reply_to_locked_thread():
    course = CourseFactory(state=CourseState.PUBLISHED)
    thread = discussions.create_thread(
        course=course, author=course.owner, title="t", body="b"
    )
    thread.is_locked = True
    thread.save()
    with pytest.raises(ValidationError):
        discussions.reply(thread=thread, author=course.owner, body="late")
