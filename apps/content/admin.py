from django.contrib import admin

from .models import ContentItem, Lesson, Module


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ["title", "position", "is_preview"]


class ContentItemInline(admin.TabularInline):
    model = ContentItem
    extra = 0
    fields = ["kind", "title", "position"]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "position"]
    list_filter = ["course"]
    search_fields = ["title", "course__title"]
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "module", "position", "is_preview"]
    list_filter = ["is_preview"]
    search_fields = ["title", "module__title"]
    inlines = [ContentItemInline]


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ["__str__", "lesson", "kind", "position"]
    list_filter = ["kind"]
    search_fields = ["title", "lesson__title"]
