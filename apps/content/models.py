from django.db import models
from django.utils.text import slugify

from apps.catalog.models import Course
from core.enums import ContentKind
from shared.models import BaseModel


class Module(BaseModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="modules"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at"]
        indexes = [models.Index(fields=["course", "position"])]

    def __str__(self) -> str:
        return f"{self.course.title} · {self.title}"


class Lesson(BaseModel):
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(
        default=False, help_text="Viewable without enrolling."
    )

    class Meta:
        ordering = ["position", "created_at"]
        indexes = [models.Index(fields=["module", "position"])]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ContentItem(BaseModel):
    """A single piece of lesson content. Single-table polymorphism keyed by `kind`
    avoids the generic-relation indirection of the original tutorial design."""

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="items"
    )
    kind = models.CharField(max_length=20, choices=ContentKind.choices)
    title = models.CharField(max_length=200, blank=True)
    position = models.PositiveIntegerField(default=0)

    body = models.TextField(blank=True, help_text="Markdown for text content.")
    media = models.FileField(upload_to="lesson_media/", blank=True, null=True)
    url = models.URLField(blank=True, help_text="Embed or external media URL.")

    class Meta:
        ordering = ["position", "created_at"]
        indexes = [models.Index(fields=["lesson", "position"])]

    def __str__(self) -> str:
        return self.title or f"{self.get_kind_display()} #{self.position}"
