from django.contrib.auth import get_user_model
from ninja.security import HttpBearer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class JWTAuth(HttpBearer):
    """Authenticate requests with a SimpleJWT access token (Bearer scheme)."""

    def authenticate(self, request, token):
        try:
            access = AccessToken(token)
        except TokenError:
            return None
        user = User.objects.filter(id=access.get("user_id"), is_active=True).first()
        if user is not None:
            request.user = user
        return user
