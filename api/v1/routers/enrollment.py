from django.shortcuts import get_object_or_404
from ninja import Router

from apps.catalog.models import Course
from apps.enrollment import selectors
from apps.enrollment.services import enrolling
from apps.payments.services import access

from ..schemas import EnrollmentOut

router = Router(tags=["enrollment"])


@router.get("/enrollments", response=list[EnrollmentOut])
def my_enrollments(request):
    return selectors.active_enrollments(student=request.user)


@router.post("/courses/{slug}/enroll", response=EnrollmentOut)
def enroll(request, slug: str):
    course = get_object_or_404(Course, slug=slug)
    entitled = access.can_access(student=request.user, course=course)
    return enrolling.enroll(
        student=request.user, course=course, payment_verified=entitled
    )
