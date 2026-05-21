from django.db import transaction
from django.urls import reverse

from apps.enrollment.models import Enrollment
from apps.notifications.services import notify
from core.enums import NotificationKind

from .models import Certificate
from .tasks import generate_certificate_pdf


def issue_certificate(*, enrollment: Enrollment) -> Certificate:
    """Create a certificate for a completed enrollment and queue PDF rendering.

    Idempotent: re-running for the same enrollment returns the existing record.
    """
    certificate, created = Certificate.objects.get_or_create(enrollment=enrollment)
    if created or not certificate.is_ready:
        transaction.on_commit(
            lambda: generate_certificate_pdf.delay(str(certificate.id))
        )
    if created:
        notify(
            recipient=enrollment.student,
            kind=NotificationKind.CERTIFICATE,
            title=f"Your certificate for {enrollment.course.title} is ready",
            url=reverse("certificates:detail", args=[enrollment.course.slug]),
        )
    return certificate
