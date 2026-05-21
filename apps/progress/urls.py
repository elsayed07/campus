from django.urls import path

from . import views

app_name = "progress"

urlpatterns = [
    path("learn/<slug:slug>/", views.classroom, name="classroom"),
    path("learn/<slug:slug>/lessons/<uuid:lesson_id>/", views.lesson_view, name="lesson"),
    path(
        "learn/<slug:slug>/lessons/<uuid:lesson_id>/complete/",
        views.complete_lesson,
        name="complete_lesson",
    ),
]
