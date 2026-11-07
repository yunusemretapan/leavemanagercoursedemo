"""Domain error hierarchy (docs/conventions.md, Error handling).

Every error carries a stable English ``code`` for machines and a Turkish ``message`` for users.
The HTTP status is chosen by the api layer, never here.
"""


class DomainError(Exception):
    code = "DOMAIN_ERROR"
    message = "İşlem iş kurallarına aykırı."

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class ServiceUnavailable(DomainError):
    code = "SERVICE_UNAVAILABLE"
    message = "Hizmet şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin."


class Unauthenticated(DomainError):
    code = "UNAUTHENTICATED"
    message = "Bu işlem için giriş yapmanız gerekiyor."


class SessionExpired(DomainError):
    code = "SESSION_EXPIRED"
    message = "Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın."


class InvalidCredentials(DomainError):
    code = "INVALID_CREDENTIALS"
    message = "Kullanıcı adı veya parola hatalı."


class ConfigurationError(Exception):
    """Invalid startup configuration: the application refuses to start (never an HTTP error)."""


class TooManyAttempts(DomainError):
    code = "TOO_MANY_ATTEMPTS"
    message = "Çok fazla başarısız giriş denemesi. Lütfen 15 dakika sonra tekrar deneyin."

    def __init__(self, retry_after: int) -> None:
        super().__init__()
        self.retry_after = retry_after
