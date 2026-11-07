from app.api.errors import error_body, status_for
from app.models.errors import DomainError, ServiceUnavailable


def test_domain_error_body_shape() -> None:
    error = ServiceUnavailable()
    assert error_body(error.code, error.message) == {
        "error": {"code": "SERVICE_UNAVAILABLE", "message": error.message}
    }
    assert error.message  # the Turkish user message is never empty


def test_service_unavailable_maps_to_503_and_other_rule_violations_to_409() -> None:
    assert status_for(ServiceUnavailable()) == 503
    assert status_for(DomainError()) == 409
