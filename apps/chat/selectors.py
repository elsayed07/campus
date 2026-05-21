from apps.catalog.models import Course

from .models import Message


def recent_messages(*, course: Course, limit: int = 50) -> list[Message]:
    qs = (
        Message.objects.filter(course=course)
        .select_related("author")
        .order_by("-created_at")[:limit]
    )
    return list(reversed(qs))
