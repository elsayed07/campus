from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("learn/<slug:slug>/chat/", views.chat_room, name="room"),
]
