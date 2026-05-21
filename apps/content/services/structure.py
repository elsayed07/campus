from typing import Any

from django.db import transaction
from django.db.models import Max

from apps.catalog.models import Course
from apps.content.models import ContentItem, Lesson, Module
from core.enums import ContentKind
from shared.exceptions import NotFoundError


def _next_position(queryset) -> int:
    current = queryset.aggregate(m=Max("position"))["m"]
    return 0 if current is None else current + 1


# --- Modules ---------------------------------------------------------------

def add_module(*, course: Course, title: str, description: str = "") -> Module:
    return Module.objects.create(
        course=course,
        title=title,
        description=description,
        position=_next_position(course.modules),
    )


def add_lesson(*, module: Module, title: str, is_preview: bool = False) -> Lesson:
    return Lesson.objects.create(
        module=module,
        title=title,
        is_preview=is_preview,
        position=_next_position(module.lessons),
    )


def add_content_item(
    *, lesson: Lesson, kind: str, title: str = "", **payload: Any
) -> ContentItem:
    if kind not in ContentKind.values:
        raise NotFoundError(f"Unknown content kind: {kind}")
    return ContentItem.objects.create(
        lesson=lesson,
        kind=kind,
        title=title,
        position=_next_position(lesson.items),
        body=payload.get("body", ""),
        url=payload.get("url", ""),
        media=payload.get("media"),
    )


@transaction.atomic
def reorder(*, model: type, parent_field: str, parent, ordered_ids: list[str]) -> None:
    """Persist a new ordering for children of `parent` given their ids in order."""
    items = model.objects.filter(**{parent_field: parent}, id__in=ordered_ids)
    by_id = {str(obj.id): obj for obj in items}
    to_update = []
    for index, raw_id in enumerate(ordered_ids):
        obj = by_id.get(str(raw_id))
        if obj is not None and obj.position != index:
            obj.position = index
            to_update.append(obj)
    if to_update:
        model.objects.bulk_update(to_update, ["position"])


def reorder_modules(*, course: Course, ordered_ids: list[str]) -> None:
    reorder(model=Module, parent_field="course", parent=course, ordered_ids=ordered_ids)


def reorder_lessons(*, module: Module, ordered_ids: list[str]) -> None:
    reorder(model=Lesson, parent_field="module", parent=module, ordered_ids=ordered_ids)


def reorder_items(*, lesson: Lesson, ordered_ids: list[str]) -> None:
    reorder(
        model=ContentItem, parent_field="lesson", parent=lesson, ordered_ids=ordered_ids
    )
