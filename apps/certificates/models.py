import uuid

from django.db import models

from apps.enrollment.models import Enrollment
from shared.models import BaseModel


def _make_serial() -> str:
    return f"CMP-{uuid.uuid4().hex[:12].upper()}"


class Certificate(BaseModel):
    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name="certificate"
    )
    serial = models.CharField(max_length=32, unique=True, default=_make_serial)
    issued_at = models.DateTimeField(null=True, blank=True)
    pdf = models.FileField(upload_to="certificates/", blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.serial

    @property
    def is_ready(self) -> bool:
        return self.issued_at is not None and bool(self.pdf)
