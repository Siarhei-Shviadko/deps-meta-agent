import json
import logging
from typing import AsyncIterator

import httpx
from httpx_retries import Retry, RetryTransport

from deps_meta_agent.domain.model import AgenticManifest
from deps_meta_agent.infrastructure.access_management import user
from deps_meta_agent.infrastructure.agent.types import AgenticPayload

from .deps_token_auth import DEPSAsyncTokenAuth
from .exceptions import SpecificAgentAdapterError
from .sse_event_parser import SSEEventParser
from .types import SSEEvent, SSEEventType

__all__ = ["HttpAgentStreamClient"]

DEFAULT_RETRY_TOTAL = 8
DEFAULT_RETRY_BACKOFF = 1.0
DEFAULT_TIMEOUT_SECONDS = 300


class HttpAgentStreamClient:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._auth = DEPSAsyncTokenAuth(user_context=user)
        self._clients: dict[str, httpx.AsyncClient] = {}

    async def stream_chat(  # noqa: WPS231
        self,
        manifest: AgenticManifest,
        payload: AgenticPayload,
    ) -> AsyncIterator[SSEEvent]:
        client = await self._get_or_create_client(
            base_url=manifest.endpoint.url,
            timeout=manifest.endpoint.timeout,
        )

        params = self._build_request_params(payload)
        parser = SSEEventParser()

        self._logger.debug(
            "Requesting agent at %s " "(conversation_id=%s, turn_id=%s)",
            manifest.endpoint.url,
            payload.conversation_id,
            payload.turn_id,
        )

        try:
            async with client.stream("GET", manifest.endpoint.url, params=params) as response:
                response.raise_for_status()
                async for event in self._parse_sse_stream(response, parser):
                    yield event
                    if event["type"] == SSEEventType.FINAL:
                        break  # noqa: WPS220

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:  # noqa: WPS505
                response_body = await e.response.aread()
                response_text = response_body.decode("utf-8", errors="replace")
            except Exception:
                response_text = None

            error_msg = (
                f"Agent returned HTTP {status_code} for {manifest.endpoint.url} "
                f"(conversation_id={payload.conversation_id}, turn_id={payload.turn_id})"
            )
            self._logger.error(
                "%s. Response body: %s",
                error_msg,
                response_text[:500] if response_text else "N/A",  # noqa: WPS432
                exc_info=True,
            )
            raise SpecificAgentAdapterError(
                message=error_msg,
                status_code=status_code,
                response_body=response_text,
                agent_url=manifest.endpoint.url,
            ) from e

        except httpx.TimeoutException as e:
            error_msg = (
                f"Timeout calling agent at {manifest.endpoint.url} "
                f"(conversation_id={payload.conversation_id}, turn_id={payload.turn_id})"
            )
            self._logger.error(error_msg, exc_info=True)
            raise SpecificAgentAdapterError(
                message=error_msg,
                agent_url=manifest.endpoint.url,
            ) from e

        except httpx.RequestError as e:
            error_msg = (
                f"Network error calling agent at {manifest.endpoint.url}: {type(e).__name__} "
                f"(conversation_id={payload.conversation_id}, turn_id={payload.turn_id})"
            )
            self._logger.error(error_msg, exc_info=True)
            raise SpecificAgentAdapterError(
                message=error_msg,
                agent_url=manifest.endpoint.url,
            ) from e

    async def _get_or_create_client(
        self,
        base_url: str,
        timeout: int,
    ) -> httpx.AsyncClient:
        if base_url in self._clients:
            client = self._clients[base_url]
            if not client.is_closed:
                return client
            del self._clients[base_url]

        client = await self._create_client(base_url, timeout)
        self._clients[base_url] = client
        return client

    async def _create_client(self, base_url: str, timeout: int) -> httpx.AsyncClient:
        transport = RetryTransport(retry=Retry(total=DEFAULT_RETRY_TOTAL, backoff_factor=DEFAULT_RETRY_BACKOFF))

        return httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout or DEFAULT_TIMEOUT_SECONDS),
            transport=transport,
            auth=self._auth,
        )

    async def _parse_sse_stream(
        self,
        response: httpx.Response,
        parser: SSEEventParser,
    ) -> AsyncIterator[SSEEvent]:
        async for line in response.aiter_lines():
            event = parser.parse_line(line)
            if event:
                yield event

    def _build_request_params(self, payload: AgenticPayload) -> dict[str, str]:
        return {
            "request": json.dumps(
                {
                    "conversationId": payload.conversation_id,
                    "turnId": payload.turn_id,
                    "userQuestion": payload.question,
                    "contextBundle": {"conversationTrim": payload.context_bundle.get("conversation_trim", [])},
                    "arguments": payload.arguments,
                }
            )
        }
