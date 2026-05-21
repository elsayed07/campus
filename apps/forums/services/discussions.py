from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Course
from apps.chat.services import can_participate
from apps.content.models import Lesson
from apps.notifications.services import notify
from core.enums import NotificationKind
from shared.exceptions import PermissionDeniedError, ValidationError

from ..models import Post, Thread


def _require_participant(user, course: Course) -> None:
    if not can_participate(user=user, course=course):
        raise PermissionDeniedError("Only enrolled members can post in this forum.")


@transaction.atomic
def create_thread(
    *, course: Course, author, title: str, body: str, lesson: Lesson | None = None
) -> Thread:
    title = (title or "").strip()
    body = (body or "").strip()
    if not title or not body:
        raise ValidationError("A title and message are required.")
    _require_participant(author, course)

    thread = Thread.objects.create(
        course=course, author=author, title=title, lesson=lesson
    )
    Post.objects.create(thread=thread, author=author, body=body)
    return thread


@transaction.atomic
def reply(*, thread: Thread, author, body: str) -> Post:
    body = (body or "").strip()
    if not body:
        raise ValidationError("Reply cannot be empty.")
    if thread.is_locked:
        raise ValidationError("This thread is locked.")
    _require_participant(author, thread.course)

    post = Post.objects.create(thread=thread, author=author, body=body)
    Thread.objects.filter(pk=thread.pk).update(last_activity_at=timezone.now())

    if thread.author_id != author.id:
        notify(
            recipient=thread.author,
            kind=NotificationKind.FORUM_REPLY,
            title=f"New reply in “{thread.title}”",
            url=reverse(
                "forums:thread", args=[thread.course.slug, thread.id]
            ),
        )
    return post
