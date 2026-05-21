from django.urls import path

from .views import CampusLoginView, CampusLogoutView, SignupView

app_name = "accounts"

urlpatterns = [
    path("login/", CampusLoginView.as_view(), name="login"),
    path("logout/", CampusLogoutView.as_view(), name="logout"),
    path("signup/", SignupView.as_view(), name="signup"),
]
