import pytest

from apps.enrollment.models import Enrollment
from apps.payments.models import Order, Plan, Subscription
from apps.payments.services import billing
from core.enums import (
    CourseState,
    EnrollmentStatus,
    OrderStatus,
    PricingModel,
    SubscriptionStatus,
)
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def _checkout_event(metadata, **obj):
    return {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": metadata, **obj}},
    }


def test_course_order_fulfillment_marks_paid_and_enrolls():
    course = CourseFactory(
        state=CourseState.PUBLISHED, pricing_model=PricingModel.ONE_TIME, price=30
    )
    student = UserFactory()
    order = Order.objects.create(
        student=student, course=course, amount=30, stripe_session_id="cs_1"
    )

    billing.process_event(
        _checkout_event(
            {"kind": "course", "order_id": str(order.id)},
            id="cs_1",
            payment_intent="pi_1",
        )
    )

    order.refresh_from_db()
    assert order.status == OrderStatus.PAID
    assert order.stripe_payment_intent == "pi_1"
    assert Enrollment.objects.filter(
        student=student, course=course, status=EnrollmentStatus.ACTIVE
    ).exists()


def test_course_fulfillment_is_idempotent():
    course = CourseFactory(
        state=CourseState.PUBLISHED, pricing_model=PricingModel.ONE_TIME, price=30
    )
    student = UserFactory()
    order = Order.objects.create(
        student=student, course=course, amount=30, stripe_session_id="cs_2"
    )
    event = _checkout_event(
        {"kind": "course", "order_id": str(order.id)}, id="cs_2", payment_intent="pi_2"
    )
    billing.process_event(event)
    billing.process_event(event)  # replayed webhook
    assert Enrollment.objects.filter(student=student, course=course).count() == 1


def test_subscription_activation_and_cancellation():
    student = UserFactory()
    plan = Plan.objects.create(name="Pro", amount=15)

    billing.process_event(
        _checkout_event(
            {"kind": "subscription", "plan_id": str(plan.id), "user_id": str(student.id)},
            customer="cus_1",
            subscription="sub_1",
        )
    )
    sub = Subscription.objects.get(user=student)
    assert sub.status == SubscriptionStatus.ACTIVE
    assert sub.stripe_subscription_id == "sub_1"

    billing.process_event(
        {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_1", "status": "canceled"}},
        }
    )
    sub.refresh_from_db()
    assert sub.status == SubscriptionStatus.CANCELED
