__all__ = ["format_sse_message", "format_sse_error"]


def format_sse_message(data: str) -> dict[str, str]:
    return {"event": "message", "data": data}


def format_sse_error(error_text: str) -> dict[str, str]:
    return {"event": "error", "data": error_text}
