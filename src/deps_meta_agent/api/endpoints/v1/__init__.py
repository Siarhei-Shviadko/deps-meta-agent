from fastapi import APIRouter

from .chat import *
from .manifests import *

__all__ = ["v1_router"]


v1_router = APIRouter(prefix="/v1")

v1_router.include_router(chat_router)
v1_router.include_router(manifests_router)
