from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Course

from .models import Certificate


@login_required
def detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    certificate = (
        Certificate.objects.select_related("enrollment")
        .filter(enrollment__course=course, enrollment__student=request.user)
        .first()
    )
    if certificate is None:
        raise Http404
    return render(
        request, "certificates/detail.html", {"certificate": certificate, "course": course}
    )


@login_required
def download(request, slug):
    course = get_object_or_404(Course, slug=slug)
    certificate = Certificate.objects.filter(
        enrollment__course=course, enrollment__student=request.user
    ).first()
    if certificate is None or not certificate.is_ready:
        raise Http404
    return FileResponse(
        certificate.pdf.open("rb"),
        as_attachment=True,
        filename=f"{certificate.serial}.pdf",
    )


def verify(request, serial):
    certificate = (
        Certificate.objects.select_related("enrollment__course", "enrollment__student")
        .filter(serial=serial, issued_at__isnull=False)
        .first()
    )
    return render(
        request, "certificates/verify.html", {"certificate": certificate, "serial": serial}
    )
