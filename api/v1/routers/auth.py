from django.contrib.auth import authenticate
from ninja import Router
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from shared.exceptions import PermissionDeniedError, ValidationError

from ..schemas import AccessOut, RefreshIn, TokenIn, TokenOut

router = Router(tags=["auth"])


@router.post("/token", response=TokenOut, auth=None)
def obtain_token(request, payload: TokenIn):
    user = authenticate(request, username=payload.email, password=payload.password)
    if user is None:
        raise PermissionDeniedError("Invalid credentials.")
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@router.post("/refresh", response=AccessOut, auth=None)
def refresh_token(request, payload: RefreshIn):
    try:
        refresh = RefreshToken(payload.refresh)
    except TokenError as exc:
        raise ValidationError("Invalid refresh token.") from exc
    return {"access": str(refresh.access_token)}
