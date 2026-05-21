import pytest

from apps.payments.models import Order, Plan, Subscription
from apps.payments.services import access
from core.enums import (
    CourseState,
    OrderStatus,
    PricingModel,
    SubscriptionStatus,
)
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_free_course_is_accessible():
    course = CourseFactory(state=CourseState.PUBLISHED, pricing_model=PricingModel.FREE)
    assert access.can_access(student=UserFactory(), course=course) is True


def test_one_time_course_requires_paid_order():
    course = CourseFactory(
        state=CourseState.PUBLISHED, pricing_model=PricingModel.ONE_TIME, price=20
    )
    student = UserFactory()
    assert access.can_access(student=student, course=course) is False

    Order.objects.create(
        student=student, course=course, amount=20, status=OrderStatus.PAID
    )
    assert access.can_access(student=student, course=course) is True


def test_subscription_course_requires_active_subscription():
    course = CourseFactory(
        state=CourseState.PUBLISHED, pricing_model=PricingModel.SUBSCRIPTION, price=0
    )
    student = UserFactory()
    plan = Plan.objects.create(name="Pro", amount=15)
    sub = Subscription.objects.create(
        user=student, plan=plan, status=SubscriptionStatus.CANCELED
    )
    assert access.can_access(student=student, course=course) is False

    sub.status = SubscriptionStatus.ACTIVE
    sub.save()
    assert access.can_access(student=student, course=course) is True
