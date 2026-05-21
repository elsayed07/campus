from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from apps.content.models import Lesson
from shared.models import BaseModel


class Thread(BaseModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="threads"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threads",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads"
    )
    title = models.CharField(max_length=255)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    last_activity_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-is_pinned", "-last_activity_at"]
        indexes = [models.Index(fields=["course", "-last_activity_at"])]

    def __str__(self) -> str:
        return self.title


class Post(BaseModel):
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="posts"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts"
    )
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["thread", "created_at"])]

    def __str__(self) -> str:
        return f"Post<{self.thread_id}>"
