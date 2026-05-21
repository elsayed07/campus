from django.db.models import Prefetch, QuerySet

from apps.catalog.models import Course
from apps.content.models import Lesson, Module


def published_courses(*, subject_slug: str | None = None, search: str | None = None) -> QuerySet[Course]:
    qs = Course.objects.published().select_related("subject", "owner")
    if subject_slug:
        qs = qs.filter(subject__slug=subject_slug)
    if search:
        qs = qs.filter(title__icontains=search)
    return qs


def instructor_courses(*, user) -> QuerySet[Course]:
    return Course.objects.for_instructor(user).select_related("subject")


def course_with_outline(*, slug: str) -> Course | None:
    """Course detail with modules/lessons prefetched (no N+1)."""
    lessons = Lesson.objects.order_by("position")
    modules = Module.objects.order_by("position").prefetch_related(
        Prefetch("lessons", queryset=lessons)
    )
    return (
        Course.objects.select_related("subject", "owner")
        .prefetch_related(Prefetch("modules", queryset=modules))
        .filter(slug=slug)
        .first()
    )
