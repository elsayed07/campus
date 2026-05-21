"""Pluggable course progression engine.

A policy decides which lessons are unlocked for a learner given the lessons they
have completed. New strategies (prerequisite graphs, mastery thresholds, spaced
repetition) can be added by implementing `ProgressionPolicy` without touching the
progress service or views.
"""

from typing import Protocol

from apps.catalog.models import Course
from apps.content.models import Lesson
from core.enums import ProgressionMode


class ProgressionPolicy(Protocol):
    def unlocked_ids(
        self, ordered_lessons: list[Lesson], completed_ids: set
    ) -> set: ...

    def next_lesson(
        self, ordered_lessons: list[Lesson], completed_ids: set
    ) -> Lesson | None: ...


class OpenPolicy:
    """Every lesson is always available."""

    def unlocked_ids(self, ordered_lessons, completed_ids):
        return {lesson.id for lesson in ordered_lessons}

    def next_lesson(self, ordered_lessons, completed_ids):
        for lesson in ordered_lessons:
            if lesson.id not in completed_ids:
                return lesson
        return None


class SequentialPolicy:
    """A lesson unlocks once every lesson before it is complete.

    Preview lessons and the first lesson are always unlocked.
    """

    def unlocked_ids(self, ordered_lessons, completed_ids):
        unlocked: set = set()
        all_previous_done = True
        for index, lesson in enumerate(ordered_lessons):
            if index == 0 or lesson.is_preview or all_previous_done:
                unlocked.add(lesson.id)
            if lesson.id not in completed_ids:
                all_previous_done = False
        return unlocked

    def next_lesson(self, ordered_lessons, completed_ids):
        for lesson in ordered_lessons:
            if lesson.id not in completed_ids:
                return lesson
        return None


_POLICIES = {
    ProgressionMode.OPEN: OpenPolicy(),
    ProgressionMode.SEQUENTIAL: SequentialPolicy(),
}


def get_policy(course: Course) -> ProgressionPolicy:
    return _POLICIES.get(course.progression_mode, SequentialPolicy())
