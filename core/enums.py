from django.db import models


class Role(models.TextChoices):
    STUDENT = "student", "Student"
    INSTRUCTOR = "instructor", "Instructor"
    ADMIN = "admin", "Admin"


class CourseState(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEW = "review", "In review"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class PricingModel(models.TextChoices):
    FREE = "free", "Free"
    ONE_TIME = "one_time", "One-time purchase"
    SUBSCRIPTION = "subscription", "Subscription only"


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class ProgressionMode(models.TextChoices):
    OPEN = "open", "Open — any lesson, any order"
    SEQUENTIAL = "sequential", "Sequential — unlock as you complete"


class ContentKind(models.TextChoices):
    TEXT = "text", "Rich text"
    VIDEO = "video", "Video"
    FILE = "file", "File / download"
    EMBED = "embed", "Embed"


class SubscriptionStatus(models.TextChoices):
    TRIALING = "trialing", "Trialing"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past due"
    CANCELED = "canceled", "Canceled"
    INCOMPLETE = "incomplete", "Incomplete"


class NotificationKind(models.TextChoices):
    ENROLLMENT = "enrollment", "Enrollment"
    PROGRESS = "progress", "Progress"
    CERTIFICATE = "certificate", "Certificate"
    FORUM_REPLY = "forum_reply", "Forum reply"
    CHAT_MENTION = "chat_mention", "Chat mention"
    PAYMENT = "payment", "Payment"
    SYSTEM = "system", "System"
