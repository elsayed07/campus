class DomainError(Exception):
    """Base class for application/domain errors raised by the service layer."""

    default_message = "A domain error occurred."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class ValidationError(DomainError):
    default_message = "The submitted data is invalid."


class ConflictError(DomainError):
    default_message = "The request conflicts with the current state."


class NotFoundError(DomainError):
    default_message = "The requested resource was not found."


class PermissionDeniedError(DomainError):
    default_message = "You do not have permission to perform this action."


class PaymentError(DomainError):
    default_message = "The payment could not be processed."
