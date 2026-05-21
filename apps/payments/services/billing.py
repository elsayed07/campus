from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Course
from apps.enrollment.services import enrolling
from core.enums import OrderStatus, SubscriptionStatus
from shared.exceptions import NotFoundError, ValidationError

from .. import gateway
from ..models import Order, Plan, Subscription


def start_course_checkout(*, student, course: Course, success_url: str, cancel_url: str) -> str:
    if course.is_free:
        raise ValidationError("This course is free — no checkout required.")

    order = Order.objects.create(
        student=student, course=course, amount=course.price, currency="usd"
    )
    session = gateway.create_checkout_session(
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(student.id),
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(course.price * 100),
                    "product_data": {"name": course.title},
                },
            }
        ],
        metadata={"kind": "course", "order_id": str(order.id)},
    )
    order.stripe_session_id = session["id"]
    order.save(update_fields=["stripe_session_id", "updated_at"])
    return session["url"]


def start_subscription_checkout(*, user, plan: Plan, success_url: str, cancel_url: str) -> str:
    session = gateway.create_checkout_session(
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(user.id),
        line_items=[{"quantity": 1, "price": plan.stripe_price_id}],
        metadata={"kind": "subscription", "plan_id": str(plan.id), "user_id": str(user.id)},
    )
    return session["url"]


# --- Webhook event handling (pure: operates on a parsed event dict) ---------

def process_event(event: dict) -> None:
    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})
    if event_type == "checkout.session.completed":
        _handle_checkout_completed(obj)
    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        _handle_subscription_change(obj)


def _handle_checkout_completed(session: dict) -> None:
    metadata = session.get("metadata") or {}
    if metadata.get("kind") == "subscription":
        _activate_subscription(session, metadata)
    else:
        _fulfill_course_order(session, metadata)


@transaction.atomic
def _fulfill_course_order(session: dict, metadata: dict) -> None:
    order_id = metadata.get("order_id")
    order = (
        Order.objects.select_for_update()
        .filter(id=order_id)
        .select_related("course", "student")
        .first()
        if order_id
        else None
    )
    if order is None:
        order = (
            Order.objects.select_for_update()
            .filter(stripe_session_id=session.get("id"))
            .select_related("course", "student")
            .first()
        )
    if order is None:
        raise NotFoundError("Order not found for checkout session.")
    if order.is_paid:
        return

    order.status = OrderStatus.PAID
    order.stripe_payment_intent = session.get("payment_intent", "") or ""
    order.save(update_fields=["status", "stripe_payment_intent", "updated_at"])

    enrolling.enroll(
        student=order.student, course=order.course, payment_verified=True
    )

    from apps.analytics.events import record_event
    from core.enums import EventKind

    record_event(
        kind=EventKind.PAYMENT,
        actor=order.student,
        course=order.course,
        amount=float(order.amount),
    )


@transaction.atomic
def _activate_subscription(session: dict, metadata: dict) -> None:
    from django.contrib.auth import get_user_model

    user_id = metadata.get("user_id") or session.get("client_reference_id")
    plan = Plan.objects.filter(id=metadata.get("plan_id")).first()
    user = get_user_model().objects.filter(id=user_id).first()
    if user is None or plan is None:
        raise NotFoundError("User or plan not found for subscription.")

    Subscription.objects.update_or_create(
        user=user,
        defaults={
            "plan": plan,
            "status": SubscriptionStatus.ACTIVE,
            "stripe_customer_id": session.get("customer", "") or "",
            "stripe_subscription_id": session.get("subscription", "") or "",
        },
    )


def _handle_subscription_change(sub_object: dict) -> None:
    sub = Subscription.objects.filter(
        stripe_subscription_id=sub_object.get("id")
    ).first()
    if sub is None:
        return
    status = sub_object.get("status", "")
    if status in SubscriptionStatus.values:
        sub.status = status
    period_end = sub_object.get("current_period_end")
    if period_end:
        sub.current_period_end = timezone.datetime.fromtimestamp(
            period_end, tz=timezone.get_current_timezone()
        )
    sub.save(update_fields=["status", "current_period_end", "updated_at"])
