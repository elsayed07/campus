from ninja import NinjaAPI
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

from shared.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    PaymentError,
    PermissionDeniedError,
    ValidationError,
)

from .routers import auth, courses, enrollment, forums, progress
from .security import JWTAuth

api = NinjaAPI(
    version="1.0.0",
    title="Campus API",
    description="Public REST API for the Campus e-learning platform.",
    auth=JWTAuth(),
    throttle=[AnonRateThrottle("30/m"), AuthRateThrottle("120/m")],
)

_STATUS = {
    ValidationError: 400,
    PermissionDeniedError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    PaymentError: 402,
}


@api.exception_handler(DomainError)
def on_domain_error(request, exc: DomainError):
    status = next((s for cls, s in _STATUS.items() if isinstance(exc, cls)), 400)
    return api.create_response(request, {"detail": exc.message}, status=status)


api.add_router("/auth", auth.router)
api.add_router("/courses", courses.router)
api.add_router("/", enrollment.router)
api.add_router("/", progress.router)
api.add_router("/", forums.router)
