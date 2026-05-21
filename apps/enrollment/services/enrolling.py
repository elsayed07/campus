from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Course
from apps.notifications.services import notify
from core.enums import CourseState, EnrollmentStatus, NotificationKind
from shared.exceptions import ConflictError, PaymentError, ValidationError

from ..models import Enrollment


@transaction.atomic
def enroll(*, student, course: Course, payment_verified: bool = False) -> Enrollment:
    """Enroll a student in a course.

    Free courses enroll immediately. Paid/subscription courses require the caller
    (the payment flow, Phase 4) to pass `payment_verified=True`.
    """
    if course.state != CourseState.PUBLISHED:
        raise ValidationError("This course is not open for enrollment.")
    if not course.is_free and not payment_verified:
        raise PaymentError("This course requires payment before enrolling.")

    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        course=course,
        defaults={"last_activity_at": timezone.now()},
    )
    if not created:
        if enrollment.status == EnrollmentStatus.CANCELLED:
            enrollment.status = EnrollmentStatus.ACTIVE
            enrollment.save(update_fields=["status", "updated_at"])
        else:
            raise ConflictError("You are already enrolled in this course.")

    Course.objects.filter(pk=course.pk).update(
        enrolled_count=F("enrolled_count") + 1
    )
    notify(
        recipient=student,
        kind=NotificationKind.ENROLLMENT,
        title=f"You're enrolled in {course.title}",
        url=reverse("progress:classroom", args=[course.slug]),
    )
    return enrollment


@transaction.atomic
def unenroll(*, enrollment: Enrollment) -> Enrollment:
    if enrollment.status == EnrollmentStatus.CANCELLED:
        return enrollment
    enrollment.status = EnrollmentStatus.CANCELLED
    enrollment.save(update_fields=["status", "updated_at"])
    Course.objects.filter(pk=enrollment.course_id, enrolled_count__gt=0).update(
        enrolled_count=F("enrolled_count") - 1
    )
    return enrollment
