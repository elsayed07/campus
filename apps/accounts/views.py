from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_ratelimit.decorators import ratelimit

from .forms import EmailLoginForm, SignupForm


@method_decorator(
    ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post"
)
class CampusLoginView(LoginView):
    template_name = "account/login.html"
    form_class = EmailLoginForm
    redirect_authenticated_user = True


class CampusLogoutView(LogoutView):
    next_page = reverse_lazy("home")


class SignupView(CreateView):
    template_name = "account/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(
            self.request,
            self.object,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        return response
