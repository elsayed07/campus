from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.catalog.models import Course
from shared.exceptions import DomainError

from . import services


@login_required
@require_POST
def submit_review(request, slug):
    course = get_object_or_404(Course, slug=slug)
    try:
        services.upsert_review(
            course=course,
            student=request.user,
            rating=int(request.POST.get("rating", 0) or 0),
            body=request.POST.get("body", ""),
        )
        messages.success(request, "Thanks for your review.")
    except (DomainError, ValueError) as exc:
        messages.error(request, getattr(exc, "message", "Invalid review."))
    return redirect("catalog:course_detail", slug=course.slug)
