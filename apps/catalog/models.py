from django.conf import settings
from django.db import models
from django.utils.text import slugify

from core.enums import CourseState, PricingModel
from shared.models import BaseModel


class Subject(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CourseQuerySet(models.QuerySet):
    def published(self) -> "CourseQuerySet":
        return self.filter(state=CourseState.PUBLISHED)

    def for_instructor(self, user) -> "CourseQuerySet":
        return self.filter(owner=user)


class Course(BaseModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses_taught",
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="courses"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    headline = models.CharField(max_length=255, blank=True)
    overview = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="courses/", blank=True, null=True)

    pricing_model = models.CharField(
        max_length=20, choices=PricingModel.choices, default=PricingModel.FREE
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    state = models.CharField(
        max_length=20, choices=CourseState.choices, default=CourseState.DRAFT
    )
    published_at = models.DateTimeField(null=True, blank=True)

    # Denormalised aggregates kept current by services/signals.
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    enrolled_count = models.PositiveIntegerField(default=0)

    objects = CourseQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["state", "-published_at"]),
            models.Index(fields=["subject", "state"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def is_published(self) -> bool:
        return self.state == CourseState.PUBLISHED

    @property
    def is_free(self) -> bool:
        return self.pricing_model == PricingModel.FREE or self.price == 0
