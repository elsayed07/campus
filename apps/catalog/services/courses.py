from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Course, Subject
from core.enums import CourseState
from shared.exceptions import ValidationError
from shared.text import unique_slug

EDITABLE_FIELDS = {
    "title",
    "subject",
    "headline",
    "overview",
    "thumbnail",
    "pricing_model",
    "price",
}


@transaction.atomic
def create_course(*, owner, subject: Subject, title: str, **fields: Any) -> Course:
    course = Course(
        owner=owner,
        subject=subject,
        title=title,
        slug=unique_slug(Course, title),
    )
    for key, value in fields.items():
        if key in EDITABLE_FIELDS:
            setattr(course, key, value)
    course.full_clean(exclude=["slug"])
    course.save()
    return course


@transaction.atomic
def update_course(*, course: Course, **fields: Any) -> Course:
    for key, value in fields.items():
        if key in EDITABLE_FIELDS:
            setattr(course, key, value)
    course.save()
    return course


def submit_for_review(*, course: Course) -> Course:
    course.state = CourseState.REVIEW
    course.save(update_fields=["state", "updated_at"])
    return course


@transaction.atomic
def publish_course(*, course: Course) -> Course:
    if not _has_publishable_content(course):
        raise ValidationError(
            "A course needs at least one module with a lesson before publishing."
        )
    course.state = CourseState.PUBLISHED
    course.published_at = course.published_at or timezone.now()
    course.save(update_fields=["state", "published_at", "updated_at"])
    return course


def archive_course(*, course: Course) -> Course:
    course.state = CourseState.ARCHIVED
    course.save(update_fields=["state", "updated_at"])
    return course


def _has_publishable_content(course: Course) -> bool:
    return course.modules.filter(lessons__isnull=False).exists()
