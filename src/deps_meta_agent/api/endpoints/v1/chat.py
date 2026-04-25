import json
import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status
from sse_starlette.sse import EventSourceResponse

from deps_meta_agent.api.serializers.chat import ChatRequest, SSEEventSerializer
from deps_meta_agent.api.sse_utils import format_sse_error, format_sse_message
from deps_meta_agent.application import ChatService
from deps_meta_agent.containers import Containers
from deps_meta_agent.infrastructure.adapters.types import SSEEventType

from ...endpoint_marker import MarkerRoute
from ...endpoint_visibility import Visibility

__all__ = ["chat_router"]


chat_router = APIRouter(tags=["Chat"], route_class=MarkerRoute)
logger = logging.getLogger(__name__)


def _parse_chat_request(query_params: str = Query(..., alias="request")) -> ChatRequest:
    return ChatRequest.model_validate_json(query_params)


@chat_router.get(
    "/chat",
    status_code=status.HTTP_200_OK,
    openapi_extra={"visibility": Visibility.PUBLIC},
)
@inject
async def chat(
    request: ChatRequest = Depends(_parse_chat_request),
    service: ChatService = Depends(Provide[Containers.chat_service]),
):
    manifests = service.validate_chat_preconditions(set(request.active_tool_sets))

    async def event_generator():  # noqa: WPS430
        try:
            event_stream = service.stream_chat(
                conversation_id=request.conversation_id,
                user_question=request.user_question,
                turn_id=request.turn_id,
                context_bundle=request.raw_context_bundle(),
                arguments=request.raw_arguments(),
                manifests=manifests,
            )
            async for event in event_stream:
                event_json = json.dumps(SSEEventSerializer(**event).to_dict())
                yield format_sse_message(event_json)

                if event.get("type") == SSEEventType.FINAL:
                    logger.debug("Final event received for turn %s", request.turn_id)
                    break

        except Exception as e:
            logger.error(
                "Error during chat stream for conversation %s: %s",
                request.conversation_id,
                e,
                exc_info=True,
            )
            error_event = {"type": "Error", "text": str(e)}
            error_json = json.dumps(error_event)
            yield format_sse_error(error_json)

    return EventSourceResponse(event_generator(), media_type="text/event-stream")
