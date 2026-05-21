from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("teach/analytics/", views.instructor_dashboard, name="dashboard"),
    path("teach/analytics/<slug:slug>/", views.course_analytics, name="course"),
]
