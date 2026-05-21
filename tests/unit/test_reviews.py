from decimal import Decimal

import pytest

from apps.enrollment.services import enrolling
from apps.reviews.models import Review
from apps.reviews.services import upsert_review
from core.enums import CourseState
from shared.exceptions import PermissionDeniedError, ValidationError
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def _enrolled(course):
    student = UserFactory()
    enrolling.enroll(student=student, course=course)
    return student


def test_review_requires_enrollment():
    course = CourseFactory(state=CourseState.PUBLISHED)
    with pytest.raises(PermissionDeniedError):
        upsert_review(course=course, student=UserFactory(), rating=5)


def test_review_updates_course_aggregate():
    course = CourseFactory(state=CourseState.PUBLISHED)
    upsert_review(course=course, student=_enrolled(course), rating=4)
    upsert_review(course=course, student=_enrolled(course), rating=2)
    course.refresh_from_db()
    assert course.rating_count == 2
    assert course.rating_avg == Decimal("3.00")


def test_review_is_upserted_not_duplicated():
    course = CourseFactory(state=CourseState.PUBLISHED)
    student = _enrolled(course)
    upsert_review(course=course, student=student, rating=3, body="ok")
    upsert_review(course=course, student=student, rating=5, body="great")
    assert Review.objects.filter(course=course, student=student).count() == 1
    course.refresh_from_db()
    assert course.rating_avg == Decimal("5.00")


def test_invalid_rating_rejected():
    course = CourseFactory(state=CourseState.PUBLISHED)
    with pytest.raises(ValidationError):
        upsert_review(course=course, student=_enrolled(course), rating=9)
