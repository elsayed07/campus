from django.urls import path

from . import views

app_name = "enrollment"

urlpatterns = [
    path("learn/", views.my_courses, name="my_courses"),
    path("courses/<slug:slug>/enroll/", views.enroll, name="enroll"),
]
