import json
import logging
from http import HTTPStatus
from typing import Any, Dict

from fastapi import Request

from deps_meta_agent.domain.exceptions import AuthError
from deps_meta_agent.infrastructure.access_management import user

__all__ = ["set_user_from_token"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PUBLIC_ENDPOINTS = (
    "/api/meta-agent/v1/docs",
    "/api/meta-agent/v1/openapi.json",
    "/api/meta-agent/debug/500",
    "/api/meta-agent/healthcheck",
    "/api/meta-agent/service-info/version",
    "/favicon.ico",
)

PUBLIC_METHOD_ENDPOINTS = (("POST", "/api/meta-agent/v1/manifests"),)


def set_user_from_token(
    request: Request,
) -> None:
    if request.url.path in PUBLIC_ENDPOINTS:
        return

    if (request.method, request.url.path) in PUBLIC_METHOD_ENDPOINTS:
        return

    try:
        deps_token = json.loads(request.headers["deps-token"])
        _validate_deps_token(deps_token)
        deps_token["deps_token"] = request.headers["deps-token"]
        user.set(deps_token)

    except KeyError:
        raise AuthError("Deps-token doesn't provided.")

    except TypeError:
        raise AuthError("Provided deps-token isn't correct.")


def _validate_deps_token(deps_token: Dict[str, Any]) -> None:
    if not deps_token:
        raise AuthError("Deps-token validation fails. Deps-token is invalid.")
    elif not deps_token.get("organisation"):
        raise AuthError(
            detail="User without organisation.",
            status_code=HTTPStatus.FORBIDDEN,
        )
