from django.urls import path

from . import views

app_name = "forums"

urlpatterns = [
    path("learn/<slug:slug>/forum/", views.forum_index, name="index"),
    path("learn/<slug:slug>/forum/new/", views.new_thread, name="new_thread"),
    path("learn/<slug:slug>/forum/<uuid:thread_id>/", views.thread_detail, name="thread"),
]
