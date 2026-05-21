from decimal import Decimal

from django.db import transaction
from django.db.models import Avg, Count

from apps.catalog.models import Course
from apps.enrollment.selectors import enrollment_for
from shared.exceptions import PermissionDeniedError, ValidationError

from .models import Review


def _recompute_course_rating(course: Course) -> None:
    stats = Review.objects.filter(course=course).aggregate(
        avg=Avg("rating"), count=Count("id")
    )
    course.rating_avg = Decimal(stats["avg"] or 0).quantize(Decimal("0.01"))
    course.rating_count = stats["count"]
    course.save(update_fields=["rating_avg", "rating_count", "updated_at"])


@transaction.atomic
def upsert_review(*, course: Course, student, rating: int, body: str = "") -> Review:
    if rating < 1 or rating > 5:
        raise ValidationError("Rating must be between 1 and 5.")
    enrollment = enrollment_for(student=student, course=course)
    if enrollment is None:
        raise PermissionDeniedError("Only enrolled students can review a course.")

    review, _ = Review.objects.update_or_create(
        course=course,
        student=student,
        defaults={"rating": rating, "body": body},
    )
    _recompute_course_rating(course)
    return review


@transaction.atomic
def delete_review(*, course: Course, student) -> None:
    Review.objects.filter(course=course, student=student).delete()
    _recompute_course_rating(course)
