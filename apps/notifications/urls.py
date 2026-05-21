from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("notifications/", views.inbox, name="inbox"),
    path("notifications/read-all/", views.read_all, name="read_all"),
    path("notifications/<uuid:pk>/read/", views.read_one, name="read_one"),
]
