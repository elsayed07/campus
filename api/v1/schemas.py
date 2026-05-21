from datetime import datetime
from uuid import UUID

from ninja import Schema


# --- Auth ---
class TokenIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    access: str
    refresh: str


class RefreshIn(Schema):
    refresh: str


class AccessOut(Schema):
    access: str


# --- Catalog ---
class SubjectOut(Schema):
    id: UUID
    name: str
    slug: str


class CourseOut(Schema):
    id: UUID
    title: str
    slug: str
    headline: str
    pricing_model: str
    price: float
    rating_avg: float
    rating_count: int
    enrolled_count: int
    subject: SubjectOut


class LessonOut(Schema):
    id: UUID
    title: str
    position: int
    is_preview: bool


class ModuleOut(Schema):
    id: UUID
    title: str
    position: int
    lessons: list[LessonOut]

    @staticmethod
    def resolve_lessons(obj):
        return obj.lessons.all()


class CourseDetailOut(CourseOut):
    overview: str
    modules: list[ModuleOut]

    @staticmethod
    def resolve_modules(obj):
        return obj.modules.all()


# --- Enrollment / progress ---
class EnrollmentOut(Schema):
    id: UUID
    course: CourseOut
    status: str
    progress_percent: int
    completed_at: datetime | None


class LessonStateOut(Schema):
    id: UUID
    title: str
    completed: bool
    unlocked: bool


class ClassroomOut(Schema):
    course_slug: str
    progress_percent: int
    completed: int
    total: int
    next_lesson_id: UUID | None
    lessons: list[LessonStateOut]


# --- Forums ---
class ThreadIn(Schema):
    title: str
    body: str


class PostIn(Schema):
    body: str


class PostOut(Schema):
    id: UUID
    author: str
    body: str
    created_at: datetime

    @staticmethod
    def resolve_author(obj):
        return obj.author.display_name


class ThreadOut(Schema):
    id: UUID
    title: str
    author: str
    is_locked: bool
    created_at: datetime

    @staticmethod
    def resolve_author(obj):
        return obj.author.display_name


class ThreadDetailOut(ThreadOut):
    posts: list[PostOut]

    @staticmethod
    def resolve_posts(obj):
        return obj.posts.all()


class DetailOut(Schema):
    detail: str
