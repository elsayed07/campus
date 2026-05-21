from django.shortcuts import get_object_or_404
from ninja import Router

from apps.catalog.models import Course
from apps.chat.services import can_participate
from apps.forums import selectors
from apps.forums.models import Thread
from apps.forums.services import discussions
from shared.exceptions import NotFoundError, PermissionDeniedError

from ..schemas import PostIn, PostOut, ThreadDetailOut, ThreadIn, ThreadOut

router = Router(tags=["forums"])


def _member_course(request, slug: str) -> Course:
    course = get_object_or_404(Course, slug=slug)
    if not can_participate(user=request.user, course=course):
        raise PermissionDeniedError("Only enrolled members can access this forum.")
    return course


@router.get("/courses/{slug}/threads", response=list[ThreadOut])
def list_threads(request, slug: str):
    course = _member_course(request, slug)
    return selectors.course_threads(course=course)


@router.post("/courses/{slug}/threads", response=ThreadDetailOut)
def create_thread(request, slug: str, payload: ThreadIn):
    course = _member_course(request, slug)
    thread = discussions.create_thread(
        course=course, author=request.user, title=payload.title, body=payload.body
    )
    return selectors.thread_with_posts(course=course, thread_id=thread.id)


@router.get("/threads/{thread_id}", response=ThreadDetailOut)
def thread_detail(request, thread_id: str):
    thread = get_object_or_404(Thread.objects.select_related("course"), id=thread_id)
    _member_course(request, thread.course.slug)
    detail = selectors.thread_with_posts(course=thread.course, thread_id=thread_id)
    if detail is None:
        raise NotFoundError("Thread not found.")
    return detail


@router.post("/threads/{thread_id}/reply", response=PostOut)
def reply(request, thread_id: str, payload: PostIn):
    thread = get_object_or_404(Thread.objects.select_related("course"), id=thread_id)
    _member_course(request, thread.course.slug)
    return discussions.reply(thread=thread, author=request.user, body=payload.body)
