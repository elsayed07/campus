from django.db.models import Count, Prefetch, QuerySet

from apps.catalog.models import Course

from .models import Post, Thread


def course_threads(*, course: Course) -> QuerySet[Thread]:
    return (
        Thread.objects.filter(course=course)
        .select_related("author")
        .annotate(post_count=Count("posts"))
    )


def thread_with_posts(*, course: Course, thread_id: str) -> Thread | None:
    posts = Post.objects.select_related("author").order_by("created_at")
    return (
        Thread.objects.filter(course=course, id=thread_id)
        .select_related("author", "course")
        .prefetch_related(Prefetch("posts", queryset=posts))
        .first()
    )
