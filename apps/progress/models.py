from django.db import models

from apps.content.models import Lesson
from apps.enrollment.models import Enrollment
from shared.models import BaseModel


class LessonProgress(BaseModel):
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="progress_records"
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "lesson"], name="uniq_lessonprogress"
            )
        ]
        indexes = [models.Index(fields=["enrollment", "completed_at"])]

    def __str__(self) -> str:
        return f"{self.enrollment_id}:{self.lesson_id}"

    @property
    def is_complete(self) -> bool:
        return self.completed_at is not None
