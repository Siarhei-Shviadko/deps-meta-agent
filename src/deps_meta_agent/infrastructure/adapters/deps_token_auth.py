import json
from contextvars import ContextVar
from typing import Generator

import httpx

__all__ = ["DEPSAsyncTokenAuth"]


class DEPSAsyncTokenAuth(httpx.Auth):
    DEPS_TOKEN_HEADER = "deps-token"  # noqa: S105

    def __init__(self, user_context: ContextVar) -> None:
        self._user_context = user_context

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers.update(self._make_deps_token_header())
        yield request

    def _make_deps_token_header(self) -> dict[str, str]:
        return {self.DEPS_TOKEN_HEADER: json.dumps(self._user_context.get(None))}
