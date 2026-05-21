from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("plans/", views.plans, name="plans"),
    path("plans/<slug:slug>/subscribe/", views.subscribe, name="subscribe"),
    path("courses/<slug:slug>/checkout/", views.checkout, name="checkout"),
    path("courses/<slug:slug>/success/", views.checkout_success, name="success"),
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
]
