import http

from .base import MetaAgentException

__all__ = ["AuthError"]


class AuthError(MetaAgentException):
    code = "authentication_error"

    def __init__(self, detail: str, status_code: int = http.HTTPStatus.UNAUTHORIZED):
        super().__init__(detail)
        self.status_code = status_code
