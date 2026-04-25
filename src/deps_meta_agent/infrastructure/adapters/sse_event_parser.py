import json
import logging

from .types import SSEEvent, SSEEventType

__all__ = ["SSEEventParser"]


class SSEEventParser:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._current_data: list[str] = []

    def parse_line(self, line: str) -> SSEEvent | None:
        line = line.rstrip("\n\r")

        if not line:
            return self._parse_complete_event()

        if line.startswith(":"):
            return None

        if not line.startswith("data:"):
            return None

        data_value = line[5:].lstrip()
        self._current_data.append(data_value)
        return None

    def _parse_complete_event(self) -> SSEEvent | None:
        if not self._current_data:
            return None

        data_value = "\n".join(self._current_data)
        self._current_data.clear()

        if not data_value:
            return None

        return self._parse_event_data(data_value)

    def _parse_event_data(self, data_value: str) -> SSEEvent | None:
        try:
            event_data = json.loads(data_value)
            return self._validate_and_create_event(event_data, data_value)
        except json.JSONDecodeError as e:
            self._logger.warning("Failed to parse SSE event JSON: %s, error: %s", data_value, e)
            return None

    def _validate_and_create_event(self, event_data: dict, data_value: str) -> SSEEvent | None:
        if not isinstance(event_data, dict):
            self._logger.warning("SSE event data is not a JSON object: %s", data_value)
            return None

        type_str = event_data.get("type")
        text = event_data.get("text")

        if type_str is None or text is None:
            self._logger.warning("SSE event missing required fields (type or text): %s", data_value)
            return None

        event_type = SSEEventType.from_string(type_str)
        if event_type is None:
            self._logger.warning("Invalid SSE event type: %s, data: %s", type_str, data_value)
            return None

        return SSEEvent(type=event_type, text=text)
