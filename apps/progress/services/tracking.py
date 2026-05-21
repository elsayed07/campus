from django.db import transaction
from django.utils import timezone

from apps.content.models import Lesson
from apps.enrollment.models import Enrollment
from core.enums import EnrollmentStatus
from shared.exceptions import ValidationError

from ..models import LessonProgress


def _course_lesson_count(course) -> int:
    return Lesson.objects.filter(module__course=course).count()


def _completed_count(enrollment: Enrollment) -> int:
    return enrollment.lesson_progress.filter(completed_at__isnull=False).count()


def recompute_progress(enrollment: Enrollment) -> int:
    total = _course_lesson_count(enrollment.course)
    if total == 0:
        return 0
    completed = _completed_count(enrollment)
    return min(100, round(completed * 100 / total))


@transaction.atomic
def mark_lesson_complete(*, enrollment: Enrollment, lesson: Lesson) -> LessonProgress:
    if lesson.module.course_id != enrollment.course_id:
        raise ValidationError("Lesson does not belong to this course.")

    record, _ = LessonProgress.objects.get_or_create(
        enrollment=enrollment, lesson=lesson
    )
    newly_completed = record.completed_at is None
    if newly_completed:
        record.completed_at = timezone.now()
        record.save(update_fields=["completed_at", "updated_at"])

    _refresh_enrollment(enrollment)

    if newly_completed:
        from apps.analytics.events import record_event
        from core.enums import EventKind

        record_event(
            kind=EventKind.LESSON_COMPLETE,
            actor=enrollment.student,
            course=enrollment.course,
            lesson=lesson,
        )
    return record


@transaction.atomic
def mark_lesson_incomplete(*, enrollment: Enrollment, lesson: Lesson) -> None:
    LessonProgress.objects.filter(enrollment=enrollment, lesson=lesson).update(
        completed_at=None
    )
    _refresh_enrollment(enrollment)


def _refresh_enrollment(enrollment: Enrollment) -> None:
    percent = recompute_progress(enrollment)
    fields = ["progress_percent", "last_activity_at"]
    enrollment.progress_percent = percent
    enrollment.last_activity_at = timezone.now()

    if percent >= 100 and enrollment.status != EnrollmentStatus.COMPLETED:
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_at = timezone.now()
        fields += ["status", "completed_at"]
        transaction.on_commit(lambda: _on_course_completed(enrollment.pk))
    elif percent < 100 and enrollment.status == EnrollmentStatus.COMPLETED:
        enrollment.status = EnrollmentStatus.ACTIVE
        enrollment.completed_at = None
        fields += ["status", "completed_at"]

    enrollment.save(update_fields=[*fields, "updated_at"])


def _on_course_completed(enrollment_id) -> None:
    """Course-completion side-effects: notify the learner and issue a certificate."""
    from django.urls import reverse

    from apps.certificates.services import issue_certificate
    from apps.notifications.services import notify
    from core.enums import NotificationKind

    enrollment = (
        Enrollment.objects.select_related("course", "student")
        .filter(pk=enrollment_id)
        .first()
    )
    if enrollment is None:
        return
    notify(
        recipient=enrollment.student,
        kind=NotificationKind.PROGRESS,
        title=f"You completed {enrollment.course.title}",
        url=reverse("progress:classroom", args=[enrollment.course.slug]),
    )
    issue_certificate(enrollment=enrollment)

    from apps.analytics.events import record_event
    from core.enums import EventKind

    record_event(
        kind=EventKind.COURSE_COMPLETE,
        actor=enrollment.student,
        course=enrollment.course,
    )
