from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.catalog.models import Course
from apps.enrollment.models import Enrollment
from apps.payments.models import Order
from apps.progress.models import LessonProgress
from core.enums import CourseState, EnrollmentStatus, EventKind, OrderStatus
from shared import cache

from .models import CourseDailyStat, Event


def course_funnel(*, course: Course) -> dict:
    views = Event.objects.filter(course=course, kind=EventKind.COURSE_VIEW).count()
    enrollments = Enrollment.objects.filter(course=course).count()
    started = (
        LessonProgress.objects.filter(
            enrollment__course=course, completed_at__isnull=False
        )
        .values("enrollment_id")
        .distinct()
        .count()
    )
    completed = Enrollment.objects.filter(
        course=course, status=EnrollmentStatus.COMPLETED
    ).count()
    return {
        "views": views,
        "enrollments": enrollments,
        "started": started,
        "completed": completed,
        "completion_rate": round(completed * 100 / enrollments) if enrollments else 0,
    }


def instructor_overview(*, user) -> dict:
    cache_key = cache.key("analytics", "instructor", user.id)
    return cache.get_or_set(cache_key, lambda: _instructor_overview(user), timeout=120)


def _instructor_overview(user) -> dict:
    courses = Course.objects.filter(owner=user)
    enrollment_stats = Enrollment.objects.filter(course__owner=user).aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=EnrollmentStatus.COMPLETED)),
    )
    revenue = (
        Order.objects.filter(course__owner=user, status=OrderStatus.PAID).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )
    rating = courses.filter(rating_count__gt=0).aggregate(avg=Avg("rating_avg"))["avg"]
    since = timezone.now() - timedelta(days=7)
    active = (
        Event.objects.filter(course__owner=user, created_at__gte=since, actor__isnull=False)
        .values("actor_id")
        .distinct()
        .count()
    )
    return {
        "course_count": courses.count(),
        "published_count": courses.filter(state=CourseState.PUBLISHED).count(),
        "total_enrollments": enrollment_stats["total"] or 0,
        "total_completions": enrollment_stats["completed"] or 0,
        "active_learners_7d": active,
        "revenue": float(revenue),
        "avg_rating": round(float(rating), 2) if rating else None,
    }


def engagement_series(*, course: Course, days: int = 14) -> list[dict]:
    start = timezone.localdate() - timedelta(days=days - 1)
    rows = {
        s.date: s.event_count
        for s in CourseDailyStat.objects.filter(course=course, date__gte=start)
    }
    return [
        {
            "date": (start + timedelta(days=i)).isoformat(),
            "count": rows.get(start + timedelta(days=i), 0),
        }
        for i in range(days)
    ]


def learner_overview(*, user) -> dict:
    enrollments = Enrollment.objects.filter(student=user)
    since = timezone.now() - timedelta(days=7)
    lessons_7d = LessonProgress.objects.filter(
        enrollment__student=user, completed_at__gte=since
    ).count()
    return {
        "active": enrollments.filter(status=EnrollmentStatus.ACTIVE).count(),
        "completed": enrollments.filter(status=EnrollmentStatus.COMPLETED).count(),
        "lessons_completed_7d": lessons_7d,
    }
