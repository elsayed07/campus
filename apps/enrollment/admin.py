from django.contrib import admin

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "status", "progress_percent", "completed_at"]
    list_filter = ["status"]
    search_fields = ["student__email", "course__title"]
    autocomplete_fields = ["student", "course"]
    readonly_fields = ["progress_percent", "last_activity_at", "completed_at"]
