import hashlib
import hmac
import json
import time

import pytest
from django.test import override_settings
from django.urls import reverse

from apps.enrollment.models import Enrollment
from apps.payments.models import Order
from core.enums import CourseState, OrderStatus, PricingModel
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db

WEBHOOK_SECRET = "whsec_testsecret"


def _signed(payload: dict) -> tuple[bytes, str]:
    body = json.dumps(payload).encode()
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.".encode() + body
    signature = hmac.new(
        WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256
    ).hexdigest()
    return body, f"t={timestamp},v1={signature}"


@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
def test_webhook_with_valid_signature_fulfills_order(client):
    course = CourseFactory(
        state=CourseState.PUBLISHED, pricing_model=PricingModel.ONE_TIME, price=40
    )
    student = UserFactory()
    order = Order.objects.create(
        student=student, course=course, amount=40, stripe_session_id="cs_v"
    )
    payload = {
        "id": "evt_1",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_v",
                "payment_intent": "pi_v",
                "metadata": {"kind": "course", "order_id": str(order.id)},
            }
        },
    }
    body, sig = _signed(payload)
    resp = client.post(
        reverse("payments:stripe_webhook"),
        data=body,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=sig,
    )
    assert resp.status_code == 200
    order.refresh_from_db()
    assert order.status == OrderStatus.PAID
    assert Enrollment.objects.filter(student=student, course=course).exists()


@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
def test_webhook_with_bad_signature_is_rejected(client):
    payload = {"type": "checkout.session.completed", "data": {"object": {}}}
    body = json.dumps(payload).encode()
    resp = client.post(
        reverse("payments:stripe_webhook"),
        data=body,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=deadbeef",
    )
    assert resp.status_code == 400


def test_checkout_creates_pending_order_and_redirects(client, monkeypatch, password):
    course = CourseFactory(
        state=CourseState.PUBLISHED, pricing_model=PricingModel.ONE_TIME, price=25
    )
    student = UserFactory(password=password)
    client.force_login(student)

    monkeypatch.setattr(
        "apps.payments.gateway.create_checkout_session",
        lambda **kw: {"id": "cs_new", "url": "https://stripe.test/checkout/cs_new"},
    )

    resp = client.post(reverse("payments:checkout", args=[course.slug]))
    assert resp.status_code == 302
    assert resp["Location"] == "https://stripe.test/checkout/cs_new"
    order = Order.objects.get(student=student, course=course)
    assert order.status == OrderStatus.PENDING
    assert order.stripe_session_id == "cs_new"


def test_checkout_enrolls_directly_when_already_entitled(client, monkeypatch, password):
    course = CourseFactory(
        state=CourseState.PUBLISHED, pricing_model=PricingModel.ONE_TIME, price=25
    )
    student = UserFactory(password=password)
    client.force_login(student)
    Order.objects.create(
        student=student, course=course, amount=25, status=OrderStatus.PAID
    )

    resp = client.post(reverse("payments:checkout", args=[course.slug]))
    assert resp.status_code == 302
    assert Enrollment.objects.filter(student=student, course=course).exists()
