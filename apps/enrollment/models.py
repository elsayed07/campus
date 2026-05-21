from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from core.enums import EnrollmentStatus
from shared.models import BaseModel


class EnrollmentQuerySet(models.QuerySet):
    def active(self) -> "EnrollmentQuerySet":
        return self.filter(status=EnrollmentStatus.ACTIVE)

    def for_user(self, user) -> "EnrollmentQuerySet":
        return self.filter(student=user)


class Enrollment(BaseModel):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
    )
    progress_percent = models.PositiveSmallIntegerField(default=0)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    objects = EnrollmentQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="uniq_enrollment_student_course"
            )
        ]
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} → {self.course}"

    @property
    def is_active(self) -> bool:
        return self.status == EnrollmentStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        return self.status == EnrollmentStatus.COMPLETED
