from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.catalog.models import Course
from apps.enrollment.services import enrolling
from core.enums import PricingModel
from shared.exceptions import DomainError

from . import gateway
from .models import Plan
from .services import access, billing


@login_required
@require_POST
def checkout(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if access.can_access(student=request.user, course=course):
        try:
            enrolling.enroll(student=request.user, course=course, payment_verified=True)
        except DomainError as exc:
            messages.info(request, exc.message)
        return redirect("progress:classroom", slug=course.slug)

    if course.pricing_model == PricingModel.SUBSCRIPTION:
        messages.info(request, "Subscribe to access this course.")
        return redirect("payments:plans")

    success = request.build_absolute_uri(
        reverse("payments:success", args=[course.slug])
    )
    cancel = request.build_absolute_uri(
        reverse("catalog:course_detail", args=[course.slug])
    )
    try:
        url = billing.start_course_checkout(
            student=request.user, course=course, success_url=success, cancel_url=cancel
        )
    except DomainError as exc:
        messages.error(request, exc.message)
        return redirect("catalog:course_detail", slug=course.slug)
    return redirect(url)


@login_required
def checkout_success(request, slug):
    course = get_object_or_404(Course, slug=slug)
    return render(request, "payments/success.html", {"course": course})


@login_required
def plans(request):
    return render(
        request, "payments/plans.html", {"plans": Plan.objects.filter(is_active=True)}
    )


@login_required
@require_POST
def subscribe(request, slug):
    plan = get_object_or_404(Plan, slug=slug, is_active=True)
    success = request.build_absolute_uri(reverse("enrollment:my_courses"))
    cancel = request.build_absolute_uri(reverse("payments:plans"))
    try:
        url = billing.start_subscription_checkout(
            user=request.user, plan=plan, success_url=success, cancel_url=cancel
        )
    except DomainError as exc:
        messages.error(request, exc.message)
        return redirect("payments:plans")
    return redirect(url)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = gateway.construct_event(request.body, sig_header)
    except DomainError:
        return HttpResponseBadRequest("Invalid signature.")
    billing.process_event(event)
    return HttpResponse(status=200)
