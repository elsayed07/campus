from django.db import transaction

from apps.catalog.models import Course
from apps.enrollment.selectors import is_enrolled
from shared import realtime
from shared.exceptions import PermissionDeniedError, ValidationError

from .models import Message

MAX_BODY = 2000


def can_participate(*, user, course: Course) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if course.owner_id == user.id:
        return True
    return is_enrolled(student=user, course=course)


def post_message(*, course: Course, author, body: str) -> Message:
    body = (body or "").strip()
    if not body:
        raise ValidationError("Message cannot be empty.")
    if len(body) > MAX_BODY:
        raise ValidationError("Message is too long.")
    if not can_participate(user=author, course=course):
        raise PermissionDeniedError("You must be enrolled to chat in this course.")

    message = Message.objects.create(course=course, author=author, body=body)
    transaction.on_commit(lambda: _broadcast(message))
    return message


def _broadcast(message: Message) -> None:
    realtime.group_send(
        realtime.chat_group(message.course_id),
        {
            "type": "chat.message",
            "payload": {
                "id": str(message.id),
                "author": message.author.display_name,
                "body": message.body,
                "created_at": message.created_at.isoformat(),
            },
        },
    )
