from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from core.enums import Role
from core.permissions import role_required
from shared.exceptions import DomainError

from . import selectors
from .forms import CourseForm
from .models import Course, Subject
from .services import courses as course_service


def course_list(request):
    courses = selectors.published_courses(
        subject_slug=request.GET.get("subject"),
        search=request.GET.get("q"),
    )
    return render(
        request,
        "catalog/course_list.html",
        {"courses": courses, "subjects": Subject.objects.all()},
    )


def course_detail(request, slug):
    course = selectors.course_with_outline(slug=slug)
    if course is None or (not course.is_published and course.owner_id != request.user.id):
        raise Http404
    return render(request, "catalog/course_detail.html", {"course": course})


def _owned_course(request, slug) -> Course:
    course = get_object_or_404(Course, slug=slug)
    if course.owner_id != request.user.id and request.user.role != Role.ADMIN:
        raise Http404
    return course


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
def instructor_courses(request):
    courses = selectors.instructor_courses(user=request.user)
    return render(request, "catalog/teach/course_list.html", {"courses": courses})


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
def course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = course_service.create_course(
                owner=request.user,
                subject=form.cleaned_data["subject"],
                title=form.cleaned_data["title"],
                headline=form.cleaned_data["headline"],
                overview=form.cleaned_data["overview"],
                thumbnail=form.cleaned_data["thumbnail"],
                pricing_model=form.cleaned_data["pricing_model"],
                price=form.cleaned_data["price"],
            )
            messages.success(request, "Course created. Add your modules and lessons.")
            return redirect("content:course_builder", slug=course.slug)
    else:
        form = CourseForm()
    return render(request, "catalog/teach/course_form.html", {"form": form, "mode": "create"})


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
def course_edit(request, slug):
    course = _owned_course(request, slug)
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            course_service.update_course(course=course, **form.cleaned_data)
            messages.success(request, "Course updated.")
            return redirect("content:course_builder", slug=course.slug)
    else:
        form = CourseForm(instance=course)
    return render(
        request,
        "catalog/teach/course_form.html",
        {"form": form, "mode": "edit", "course": course},
    )


@login_required
@role_required(Role.INSTRUCTOR, Role.ADMIN)
def course_publish(request, slug):
    course = _owned_course(request, slug)
    try:
        course_service.publish_course(course=course)
        messages.success(request, "Course published.")
    except DomainError as exc:
        messages.error(request, exc.message)
    return redirect("content:course_builder", slug=course.slug)
