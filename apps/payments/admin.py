from django.contrib import admin

from .models import Order, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "amount", "currency", "interval", "is_active"]
    list_filter = ["is_active", "interval"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "status", "current_period_end"]
    list_filter = ["status"]
    search_fields = ["user__email", "stripe_subscription_id"]
    autocomplete_fields = ["user", "plan"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["student__email", "course__title", "stripe_session_id"]
    autocomplete_fields = ["student", "course"]
    readonly_fields = ["stripe_session_id", "stripe_payment_intent"]
