from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from core.enums import Role

User = get_user_model()


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )


class SignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=False)
    as_instructor = forms.BooleanField(
        required=False, label="I want to teach on Campus"
    )

    class Meta:
        model = User
        fields = ("email", "full_name")

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.full_name = self.cleaned_data.get("full_name", "")
        if self.cleaned_data.get("as_instructor"):
            user.role = Role.INSTRUCTOR
        if commit:
            user.save()
        return user
