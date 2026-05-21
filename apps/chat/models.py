from django.conf import settings
from django.db import models

from apps.catalog.models import Course
from shared.models import BaseModel


class Message(BaseModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="chat_messages"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages"
    )
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["course", "created_at"])]

    def __str__(self) -> str:
        return f"{self.author_id}@{self.course_id}"
