from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Course
from apps.catalog.selectors import instructor_courses
from core.enums import Role
from core.permissions import role_required

from . import selectors


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
def instructor_dashboard(request):
    overview = selectors.instructor_overview(user=request.user)
    courses = [
        {"course": c, "funnel": selectors.course_funnel(course=c)}
        for c in instructor_courses(user=request.user)
    ]
    return render(
        request,
        "analytics/dashboard.html",
        {"overview": overview, "courses": courses},
    )


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
def course_analytics(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.owner_id != request.user.id and request.user.role != Role.ADMIN:
        raise Http404
    return render(
        request,
        "analytics/course.html",
        {
            "course": course,
            "funnel": selectors.course_funnel(course=course),
            "series": selectors.engagement_series(course=course),
        },
    )
