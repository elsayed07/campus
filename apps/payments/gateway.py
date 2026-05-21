"""Thin wrapper around the Stripe SDK.

Isolating Stripe here keeps the service layer testable (tests monkeypatch these
functions) and confines all SDK/config coupling to one module.
"""

import json
from typing import Any

import stripe
from django.conf import settings

from shared.exceptions import PaymentError


def _client():
    if not settings.STRIPE_SECRET_KEY:
        raise PaymentError("Payments are not configured.")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_checkout_session(**params: Any) -> Any:
    return _client().checkout.Session.create(**params)


def construct_event(payload: bytes, sig_header: str) -> dict:
    """Verify the webhook signature and return the parsed event."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise PaymentError("Webhook secret is not configured.")
    try:
        stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise PaymentError("Invalid webhook signature.") from exc
    # The payload is now verified; parse it into plain dicts so the service layer
    # stays decoupled from StripeObject.
    return json.loads(payload)
