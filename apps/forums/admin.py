from django.contrib import admin

from .models import Post, Thread


class PostInline(admin.TabularInline):
    model = Post
    extra = 0
    fields = ["author", "body", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "author", "is_pinned", "is_locked", "last_activity_at"]
    list_filter = ["is_pinned", "is_locked"]
    search_fields = ["title", "course__title", "author__email"]
    inlines = [PostInline]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["thread", "author", "created_at"]
    search_fields = ["thread__title", "author__email", "body"]
