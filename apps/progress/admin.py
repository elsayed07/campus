from django.contrib import admin

from .models import LessonProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ["enrollment", "lesson", "completed_at"]
    search_fields = ["enrollment__student__email", "lesson__title"]
    autocomplete_fields = ["enrollment", "lesson"]
