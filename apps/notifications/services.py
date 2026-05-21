from django.db import transaction

from core.enums import NotificationKind
from shared import realtime

from .models import Notification
from .selectors import unread_count

# Kinds that also send an email (in addition to the in-app + WebSocket push).
EMAIL_KINDS = {
    NotificationKind.CERTIFICATE,
    NotificationKind.PAYMENT,
}


def notify(
    *,
    recipient,
    kind: str,
    title: str,
    body: str = "",
    url: str = "",
) -> Notification:
    notification = Notification.objects.create(
        recipient=recipient, kind=kind, title=title, body=body, url=url
    )
    transaction.on_commit(lambda: _dispatch(notification))
    return notification


def _dispatch(notification: Notification) -> None:
    realtime.group_send(
        realtime.user_group(notification.recipient_id),
        {
            "type": "notify",
            "payload": {
                "id": str(notification.id),
                "kind": notification.kind,
                "title": notification.title,
                "body": notification.body,
                "url": notification.url,
                "unread": unread_count(user_id=notification.recipient_id),
            },
        },
    )
    if notification.kind in EMAIL_KINDS:
        from .tasks import send_notification_email

        send_notification_email.delay(str(notification.id))


def mark_read(*, notification: Notification) -> None:
    notification.mark_read()


def mark_all_read(*, user) -> int:
    from django.utils import timezone

    return Notification.objects.for_user(user).unread().update(
        read_at=timezone.now()
    )
