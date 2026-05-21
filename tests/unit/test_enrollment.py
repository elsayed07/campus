import pytest

from apps.catalog.models import Course
from apps.enrollment.services import enrolling
from core.enums import CourseState, EnrollmentStatus, PricingModel
from shared.exceptions import ConflictError, PaymentError, ValidationError
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def _published(**kwargs) -> Course:
    return CourseFactory(state=CourseState.PUBLISHED, **kwargs)


def test_enroll_in_free_published_course():
    course = _published()
    student = UserFactory()
    enrollment = enrolling.enroll(student=student, course=course)
    assert enrollment.status == EnrollmentStatus.ACTIVE
    course.refresh_from_db()
    assert course.enrolled_count == 1


def test_enroll_rejects_unpublished_course():
    course = CourseFactory(state=CourseState.DRAFT)
    with pytest.raises(ValidationError):
        enrolling.enroll(student=UserFactory(), course=course)


def test_paid_course_requires_payment():
    course = _published(pricing_model=PricingModel.ONE_TIME, price=49)
    with pytest.raises(PaymentError):
        enrolling.enroll(student=UserFactory(), course=course)
    # The payment flow passes payment_verified=True.
    enrollment = enrolling.enroll(
        student=UserFactory(), course=course, payment_verified=True
    )
    assert enrollment.is_active


def test_duplicate_enrollment_conflicts():
    course = _published()
    student = UserFactory()
    enrolling.enroll(student=student, course=course)
    with pytest.raises(ConflictError):
        enrolling.enroll(student=student, course=course)


def test_unenroll_decrements_count():
    course = _published()
    student = UserFactory()
    enrollment = enrolling.enroll(student=student, course=course)
    enrolling.unenroll(enrollment=enrollment)
    course.refresh_from_db()
    assert course.enrolled_count == 0
    assert enrollment.status == EnrollmentStatus.CANCELLED
