from django.db.models import QuerySet

from .models import Notification


def unread_count(*, user=None, user_id=None) -> int:
    qs = Notification.objects.unread()
    if user is not None:
        qs = qs.filter(recipient=user)
    else:
        qs = qs.filter(recipient_id=user_id)
    return qs.count()


def recent(*, user, limit: int = 20) -> QuerySet[Notification]:
    return Notification.objects.for_user(user)[:limit]
