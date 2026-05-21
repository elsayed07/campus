from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("courses/", views.course_list, name="course_list"),
    path("teach/", views.instructor_courses, name="teach"),
    path("teach/new/", views.course_create, name="course_create"),
    path("teach/<slug:slug>/edit/", views.course_edit, name="course_edit"),
    path("teach/<slug:slug>/publish/", views.course_publish, name="course_publish"),
    path("courses/<slug:slug>/", views.course_detail, name="course_detail"),
]
