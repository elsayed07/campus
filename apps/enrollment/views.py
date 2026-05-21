from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import Course
from shared.exceptions import DomainError

from . import selectors
from .services import enrolling


@login_required
@require_POST
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug)
    try:
        enrolling.enroll(student=request.user, course=course)
        messages.success(request, f"You're enrolled in {course.title}.")
        return redirect("progress:classroom", slug=course.slug)
    except DomainError as exc:
        messages.error(request, exc.message)
        return redirect("catalog:course_detail", slug=course.slug)


@login_required
def my_courses(request):
    from apps.analytics import selectors as analytics_selectors

    enrollments = selectors.active_enrollments(student=request.user)
    return render(
        request,
        "enrollment/my_courses.html",
        {
            "enrollments": enrollments,
            "stats": analytics_selectors.learner_overview(user=request.user),
        },
    )
