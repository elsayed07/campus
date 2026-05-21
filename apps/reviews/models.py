from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import Course
from shared.models import BaseModel


class Review(BaseModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="reviews"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    body = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "student"], name="uniq_review_course_student"
            )
        ]

    def __str__(self) -> str:
        return f"{self.rating}★ {self.course_id}"
