from django.shortcuts import get_object_or_404
from ninja import Router

from apps.catalog.models import Course
from apps.enrollment.models import Enrollment
from apps.progress import selectors
from apps.progress.services import tracking
from shared.exceptions import NotFoundError

from ..schemas import ClassroomOut

router = Router(tags=["progress"])


def _enrollment(request, slug: str) -> Enrollment:
    course = get_object_or_404(Course, slug=slug)
    enrollment = Enrollment.objects.filter(
        student=request.user, course=course
    ).select_related("course").first()
    if enrollment is None:
        raise NotFoundError("You are not enrolled in this course.")
    return enrollment


def _classroom_payload(enrollment: Enrollment) -> dict:
    room = selectors.build_classroom(enrollment=enrollment)
    lessons = [
        {
            "id": node.lesson.id,
            "title": node.lesson.title,
            "completed": node.completed,
            "unlocked": node.unlocked,
        }
        for module in room.modules
        for node in module.lessons
    ]
    return {
        "course_slug": enrollment.course.slug,
        "progress_percent": enrollment.progress_percent,
        "completed": room.completed,
        "total": room.total,
        "next_lesson_id": room.next_lesson.id if room.next_lesson else None,
        "lessons": lessons,
    }


@router.get("/courses/{slug}/classroom", response=ClassroomOut)
def classroom(request, slug: str):
    return _classroom_payload(_enrollment(request, slug))


@router.post("/courses/{slug}/lessons/{lesson_id}/complete", response=ClassroomOut)
def complete_lesson(request, slug: str, lesson_id: str):
    enrollment = _enrollment(request, slug)
    lesson = selectors.accessible_lesson(enrollment=enrollment, lesson_id=lesson_id)
    if lesson is None:
        raise NotFoundError("Lesson is not available.")
    tracking.mark_lesson_complete(enrollment=enrollment, lesson=lesson)
    enrollment.refresh_from_db()
    return _classroom_payload(enrollment)
