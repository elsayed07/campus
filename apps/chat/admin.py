from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["author", "course", "created_at"]
    search_fields = ["author__email", "course__title", "body"]
    list_filter = ["course"]
