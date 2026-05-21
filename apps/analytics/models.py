from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from apps.content.models import Lesson
from core.enums import EventKind
from shared.models import TimestampedModel, UUIDModel


class Event(UUIDModel, TimestampedModel):
    """An append-only analytics event. Not soft-deletable: events are immutable
    facts, so this skips BaseModel's soft-delete mixin."""

    kind = models.CharField(max_length=30, choices=EventKind.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True, related_name="events"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="events"
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["course", "kind", "created_at"]),
            models.Index(fields=["kind", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind}@{self.created_at:%Y-%m-%d}"


class CourseDailyStat(UUIDModel, TimestampedModel):
    """Pre-aggregated per-course daily metrics, refreshed by a beat task."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="daily_stats"
    )
    date = models.DateField(db_index=True)
    new_enrollments = models.PositiveIntegerField(default=0)
    completions = models.PositiveIntegerField(default=0)
    active_learners = models.PositiveIntegerField(default=0)
    event_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "date"], name="uniq_course_daily_stat"
            )
        ]

    def __str__(self) -> str:
        return f"{self.course_id} {self.date}"
