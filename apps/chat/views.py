from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from apps.catalog.models import Course

from . import selectors, services


@login_required
def chat_room(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if not services.can_participate(user=request.user, course=course):
        raise Http404
    return render(
        request,
        "chat/room.html",
        {"course": course, "messages": selectors.recent_messages(course=course)},
    )
