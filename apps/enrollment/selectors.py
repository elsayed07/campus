from django.db.models import QuerySet

from apps.catalog.models import Course
from core.enums import EnrollmentStatus

from .models import Enrollment


def enrollment_for(*, student, course: Course) -> Enrollment | None:
    return Enrollment.objects.filter(student=student, course=course).first()


def is_enrolled(*, student, course: Course) -> bool:
    return Enrollment.objects.filter(
        student=student, course=course, status=EnrollmentStatus.ACTIVE
    ).exists()


def active_enrollments(*, student) -> QuerySet[Enrollment]:
    return (
        Enrollment.objects.for_user(student)
        .active()
        .select_related("course", "course__subject")
    )
