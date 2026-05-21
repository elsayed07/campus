from django.db.models import QuerySet

from apps.catalog.models import Course

from .models import Review


def course_reviews(*, course: Course) -> QuerySet[Review]:
    return Review.objects.filter(course=course).select_related("student")


def user_review(*, course: Course, student) -> Review | None:
    if not getattr(student, "is_authenticated", False):
        return None
    return Review.objects.filter(course=course, student=student).first()
