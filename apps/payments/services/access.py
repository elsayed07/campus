from apps.catalog.models import Course
from core.enums import OrderStatus, PricingModel

from ..models import Order, Subscription


def has_active_subscription(user) -> bool:
    sub = Subscription.objects.filter(user=user).first()
    return sub is not None and sub.is_active


def has_paid_order(*, student, course: Course) -> bool:
    return Order.objects.filter(
        student=student, course=course, status=OrderStatus.PAID
    ).exists()


def can_access(*, student, course: Course) -> bool:
    """Whether a student is entitled to enroll/learn without further payment."""
    if course.is_free:
        return True
    if course.pricing_model == PricingModel.SUBSCRIPTION:
        return has_active_subscription(student)
    return has_paid_order(student=student, course=course)
