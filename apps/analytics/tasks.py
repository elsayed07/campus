from datetime import date as date_cls

from celery import shared_task
from django.db.models import Count
from django.utils import timezone

from apps.catalog.models import Course
from apps.enrollment.models import Enrollment
from core.enums import EnrollmentStatus

from .models import CourseDailyStat, Event


@shared_task
def rollup_daily_stats(for_date: str | None = None) -> int:
    """Aggregate per-course metrics for a single day into CourseDailyStat.

    Returns the number of course rows written. Idempotent: re-running for the
    same date overwrites that day's row.
    """
    day = date_cls.fromisoformat(for_date) if for_date else timezone.localdate()
    written = 0

    for course in Course.objects.all().only("id"):
        enrollments = Enrollment.objects.filter(course=course)
        new_enrollments = enrollments.filter(created_at__date=day).count()
        completions = enrollments.filter(
            status=EnrollmentStatus.COMPLETED, completed_at__date=day
        ).count()
        events = Event.objects.filter(course=course, created_at__date=day)
        active = (
            events.filter(actor__isnull=False)
            .aggregate(n=Count("actor", distinct=True))["n"]
            or 0
        )
        event_count = events.count()

        if new_enrollments or completions or active or event_count:
            CourseDailyStat.objects.update_or_create(
                course=course,
                date=day,
                defaults={
                    "new_enrollments": new_enrollments,
                    "completions": completions,
                    "active_learners": active,
                    "event_count": event_count,
                },
            )
            written += 1
    return written
