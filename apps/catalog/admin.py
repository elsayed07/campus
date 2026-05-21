from django.contrib import admin

from .models import Course, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "subject", "state", "pricing_model", "published_at"]
    list_filter = ["state", "pricing_model", "subject"]
    search_fields = ["title", "owner__email"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["owner", "subject"]
    readonly_fields = ["rating_avg", "rating_count", "enrolled_count", "published_at"]
