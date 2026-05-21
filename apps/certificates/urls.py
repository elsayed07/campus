from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("verify/<str:serial>/", views.verify, name="verify"),
    path("learn/<slug:slug>/certificate/", views.detail, name="detail"),
    path("learn/<slug:slug>/certificate/download/", views.download, name="download"),
]
