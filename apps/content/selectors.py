from django.db.models import Prefetch

from apps.catalog.models import Course
from apps.content.models import ContentItem, Lesson, Module


def course_builder_outline(*, course: Course) -> Course:
    """Course with modules → lessons → items fully prefetched for the CMS builder."""
    items = ContentItem.objects.order_by("position")
    lessons = Lesson.objects.order_by("position").prefetch_related(
        Prefetch("items", queryset=items)
    )
    modules = Module.objects.order_by("position").prefetch_related(
        Prefetch("lessons", queryset=lessons)
    )
    return (
        Course.objects.prefetch_related(Prefetch("modules", queryset=modules)).get(
            id=course.id
        )
    )


def lesson_for_viewing(*, lesson_id: str) -> Lesson | None:
    return (
        Lesson.objects.select_related("module__course")
        .prefetch_related(Prefetch("items", queryset=ContentItem.objects.order_by("position")))
        .filter(id=lesson_id)
        .first()
    )
