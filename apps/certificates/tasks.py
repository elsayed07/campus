from celery import shared_task
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Certificate


@shared_task
def generate_certificate_pdf(certificate_id: str) -> None:
    from weasyprint import HTML

    certificate = (
        Certificate.objects.select_related(
            "enrollment__student", "enrollment__course"
        )
        .filter(id=certificate_id)
        .first()
    )
    if certificate is None or certificate.is_ready:
        return

    enrollment = certificate.enrollment
    html = render_to_string(
        "certificates/certificate.html",
        {
            "student": enrollment.student.display_name,
            "course": enrollment.course.title,
            "serial": certificate.serial,
            "date": timezone.now().date(),
        },
    )
    pdf_bytes = HTML(string=html).write_pdf()
    certificate.pdf.save(
        f"{certificate.serial}.pdf", ContentFile(pdf_bytes), save=False
    )
    certificate.issued_at = timezone.now()
    certificate.save(update_fields=["pdf", "issued_at", "updated_at"])
