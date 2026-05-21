from dataclasses import dataclass

from django.db.models import Prefetch

from apps.content.models import ContentItem, Lesson, Module
from apps.enrollment.models import Enrollment

from . import adaptive
from .models import LessonProgress


@dataclass
class LessonNode:
    lesson: Lesson
    completed: bool
    unlocked: bool


@dataclass
class ModuleNode:
    module: Module
    lessons: list[LessonNode]


@dataclass
class Classroom:
    enrollment: Enrollment
    modules: list[ModuleNode]
    completed_ids: set
    next_lesson: Lesson | None
    total: int
    completed: int


def _ordered_modules(course) -> list[Module]:
    lessons = Lesson.objects.order_by("position")
    return list(
        Module.objects.filter(course=course)
        .order_by("position")
        .prefetch_related(Prefetch("lessons", queryset=lessons))
    )


def build_classroom(*, enrollment: Enrollment) -> Classroom:
    course = enrollment.course
    modules = _ordered_modules(course)
    ordered_lessons = [lesson for m in modules for lesson in m.lessons.all()]

    completed_ids = set(
        LessonProgress.objects.filter(
            enrollment=enrollment, completed_at__isnull=False
        ).values_list("lesson_id", flat=True)
    )

    policy = adaptive.get_policy(course)
    unlocked = policy.unlocked_ids(ordered_lessons, completed_ids)

    module_nodes = [
        ModuleNode(
            module=m,
            lessons=[
                LessonNode(
                    lesson=lesson,
                    completed=lesson.id in completed_ids,
                    unlocked=lesson.id in unlocked,
                )
                for lesson in m.lessons.all()
            ],
        )
        for m in modules
    ]

    return Classroom(
        enrollment=enrollment,
        modules=module_nodes,
        completed_ids=completed_ids,
        next_lesson=policy.next_lesson(ordered_lessons, completed_ids),
        total=len(ordered_lessons),
        completed=len(completed_ids),
    )


def accessible_lesson(*, enrollment: Enrollment, lesson_id: str) -> Lesson | None:
    """Return the lesson only if it belongs to the course and is unlocked."""
    course = enrollment.course
    modules = _ordered_modules(course)
    ordered_lessons = [lesson for m in modules for lesson in m.lessons.all()]
    target = next((x for x in ordered_lessons if str(x.id) == str(lesson_id)), None)
    if target is None:
        return None

    completed_ids = set(
        LessonProgress.objects.filter(
            enrollment=enrollment, completed_at__isnull=False
        ).values_list("lesson_id", flat=True)
    )
    policy = adaptive.get_policy(course)
    if target.id not in policy.unlocked_ids(ordered_lessons, completed_ids):
        return None

    target_with_items = (
        Lesson.objects.prefetch_related(
            Prefetch("items", queryset=ContentItem.objects.order_by("position"))
        )
        .filter(id=target.id)
        .first()
    )
    return target_with_items
