from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.catalog.models import Course
from core.enums import Role
from core.permissions import role_required

from . import selectors
from .models import ContentItem, Lesson, Module
from .services import structure


def _owned_course(request, slug) -> Course:
    course = get_object_or_404(Course, slug=slug)
    if course.owner_id != request.user.id and request.user.role != Role.ADMIN:
        raise Http404
    return course


def _assert_owns(request, course: Course) -> None:
    if course.owner_id != request.user.id and request.user.role != Role.ADMIN:
        raise Http404


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
def course_builder(request, slug):
    course = _owned_course(request, slug)
    outline = selectors.course_builder_outline(course=course)
    return render(request, "content/builder.html", {"course": outline})


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
@require_POST
def add_module(request, slug):
    course = _owned_course(request, slug)
    title = (request.POST.get("title") or "").strip()
    if not title:
        return HttpResponseBadRequest("Title is required.")
    module = structure.add_module(course=course, title=title)
    return render(request, "content/partials/module.html", {"module": module})


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
@require_POST
def add_lesson(request, module_id):
    module = get_object_or_404(Module.objects.select_related("course"), id=module_id)
    _assert_owns(request, module.course)
    title = (request.POST.get("title") or "").strip()
    if not title:
        return HttpResponseBadRequest("Title is required.")
    lesson = structure.add_lesson(
        module=module, title=title, is_preview=bool(request.POST.get("is_preview"))
    )
    return render(request, "content/partials/lesson.html", {"lesson": lesson})


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
@require_POST
def add_item(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("module__course"), id=lesson_id
    )
    _assert_owns(request, lesson.module.course)
    kind = request.POST.get("kind", "")
    item = structure.add_content_item(
        lesson=lesson,
        kind=kind,
        title=(request.POST.get("title") or "").strip(),
        body=request.POST.get("body", ""),
        url=request.POST.get("url", ""),
        media=request.FILES.get("media"),
    )
    return render(request, "content/partials/item.html", {"item": item})


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
@require_POST
def reorder_modules(request, slug):
    course = _owned_course(request, slug)
    structure.reorder_modules(course=course, ordered_ids=request.POST.getlist("id"))
    return HttpResponse(status=204)


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
@require_POST
def reorder_lessons(request, module_id):
    module = get_object_or_404(Module.objects.select_related("course"), id=module_id)
    _assert_owns(request, module.course)
    structure.reorder_lessons(module=module, ordered_ids=request.POST.getlist("id"))
    return HttpResponse(status=204)


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
@require_POST
def delete_module(request, module_id):
    module = get_object_or_404(Module.objects.select_related("course"), id=module_id)
    _assert_owns(request, module.course)
    module.delete()
    return HttpResponse(status=200)


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
@require_POST
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("module__course"), id=lesson_id
    )
    _assert_owns(request, lesson.module.course)
    lesson.delete()
    return HttpResponse(status=200)


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
@require_POST
def delete_item(request, item_id):
    item = get_object_or_404(
        ContentItem.objects.select_related("lesson__module__course"), id=item_id
    )
    _assert_owns(request, item.lesson.module.course)
    item.delete()
    return HttpResponse(status=200)
