from django.contrib import admin

from .models import CourseDailyStat, Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["kind", "actor", "course", "created_at"]
    list_filter = ["kind"]
    search_fields = ["actor__email", "course__title"]
    readonly_fields = ["kind", "actor", "course", "lesson", "metadata", "created_at"]


@admin.register(CourseDailyStat)
class CourseDailyStatAdmin(admin.ModelAdmin):
    list_display = ["course", "date", "new_enrollments", "completions", "active_learners", "event_count"]
    list_filter = ["date"]
    search_fields = ["course__title"]
