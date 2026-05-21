from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalog.models import Course
from apps.chat.services import can_participate
from shared.exceptions import DomainError

from . import selectors
from .services import discussions


def _course_for_member(request, slug) -> Course:
    course = get_object_or_404(Course, slug=slug)
    if not can_participate(user=request.user, course=course):
        raise Http404
    return course


@login_required
def forum_index(request, slug):
    course = _course_for_member(request, slug)
    return render(
        request,
        "forums/index.html",
        {"course": course, "threads": selectors.course_threads(course=course)},
    )


@login_required
def new_thread(request, slug):
    course = _course_for_member(request, slug)
    if request.method == "POST":
        try:
            thread = discussions.create_thread(
                course=course,
                author=request.user,
                title=request.POST.get("title", ""),
                body=request.POST.get("body", ""),
            )
            return redirect("forums:thread", slug=course.slug, thread_id=thread.id)
        except DomainError as exc:
            messages.error(request, exc.message)
    return render(request, "forums/new_thread.html", {"course": course})


@login_required
def thread_detail(request, slug, thread_id):
    course = _course_for_member(request, slug)
    thread = selectors.thread_with_posts(course=course, thread_id=thread_id)
    if thread is None:
        raise Http404
    if request.method == "POST":
        try:
            discussions.reply(
                thread=thread, author=request.user, body=request.POST.get("body", "")
            )
            return redirect("forums:thread", slug=course.slug, thread_id=thread.id)
        except DomainError as exc:
            messages.error(request, exc.message)
    return render(request, "forums/thread.html", {"course": course, "thread": thread})
