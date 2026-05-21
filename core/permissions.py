from collections.abc import Callable
from functools import wraps

from django.contrib.auth.mixins import AccessMixin
from django.http import HttpRequest, HttpResponse

from core.enums import Role
from shared.exceptions import PermissionDeniedError


def has_role(user, *roles: str) -> bool:
    return bool(getattr(user, "is_authenticated", False)) and user.role in roles


def require_role(user, *roles: str) -> None:
    """Service-layer guard: raise a typed error when the role is not allowed."""
    if not has_role(user, *roles):
        raise PermissionDeniedError()


class RoleRequiredMixin(AccessMixin):
    """CBV guard restricting a view to one or more roles."""

    allowed_roles: tuple[str, ...] = ()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class InstructorRequiredMixin(RoleRequiredMixin):
    allowed_roles = (Role.INSTRUCTOR, Role.ADMIN)


def role_required(*roles: str) -> Callable:
    """FBV decorator equivalent of RoleRequiredMixin."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapped(request: HttpRequest, *args, **kwargs):
            if not has_role(request.user, *roles):
                raise PermissionDeniedError()
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
