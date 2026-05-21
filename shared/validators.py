from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

MAX_IMAGE_MB = 5
MAX_VIDEO_MB = 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


@deconstructible
class FileSizeValidator:
    def __init__(self, max_mb: int):
        self.max_bytes = max_mb * 1024 * 1024
        self.max_mb = max_mb

    def __call__(self, file) -> None:
        if file.size > self.max_bytes:
            raise ValidationError(f"File exceeds the {self.max_mb}MB limit.")

    def __eq__(self, other) -> bool:
        return isinstance(other, FileSizeValidator) and other.max_mb == self.max_mb


@deconstructible
class ContentTypeValidator:
    def __init__(self, allowed: set[str]):
        self.allowed = set(allowed)

    def __call__(self, file) -> None:
        content_type = getattr(file.file, "content_type", None)
        if content_type and content_type not in self.allowed:
            raise ValidationError(f"Unsupported file type: {content_type}.")

    def __eq__(self, other) -> bool:
        return isinstance(other, ContentTypeValidator) and other.allowed == self.allowed
