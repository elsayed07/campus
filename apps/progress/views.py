from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import Course
from apps.enrollment.models import Enrollment

from . import selectors
from .services import tracking


def _enrollment_or_404(request, slug) -> Enrollment:
    course = get_object_or_404(Course, slug=slug)
    enrollment = Enrollment.objects.filter(
        student=request.user, course=course
    ).select_related("course").first()
    if enrollment is None or not (enrollment.is_active or enrollment.is_completed):
        raise Http404
    return enrollment


@login_required
def classroom(request, slug):
    enrollment = _enrollment_or_404(request, slug)
    room = selectors.build_classroom(enrollment=enrollment)
    return render(request, "progress/classroom.html", {"room": room})


@login_required
def lesson_view(request, slug, lesson_id):
    enrollment = _enrollment_or_404(request, slug)
    lesson = selectors.accessible_lesson(enrollment=enrollment, lesson_id=lesson_id)
    if lesson is None:
        raise Http404
    room = selectors.build_classroom(enrollment=enrollment)
    is_done = lesson.id in room.completed_ids
    return render(
        request,
        "progress/lesson.html",
        {"room": room, "lesson": lesson, "is_done": is_done},
    )


@login_required
@require_POST
def complete_lesson(request, slug, lesson_id):
    enrollment = _enrollment_or_404(request, slug)
    lesson = selectors.accessible_lesson(enrollment=enrollment, lesson_id=lesson_id)
    if lesson is None:
        raise Http404
    tracking.mark_lesson_complete(enrollment=enrollment, lesson=lesson)

    room = selectors.build_classroom(enrollment=enrollment)
    if room.next_lesson is not None:
        return redirect(
            "progress:lesson", slug=slug, lesson_id=room.next_lesson.id
        )
    return redirect("progress:classroom", slug=slug)
