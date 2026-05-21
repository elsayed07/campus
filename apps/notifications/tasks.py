from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Notification


@shared_task
def send_notification_email(notification_id: str) -> None:
    notification = (
        Notification.objects.select_related("recipient")
        .filter(id=notification_id)
        .first()
    )
    if notification is None:
        return
    send_mail(
        subject=notification.title,
        message=notification.body or notification.title,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[notification.recipient.email],
        fail_silently=True,
    )
