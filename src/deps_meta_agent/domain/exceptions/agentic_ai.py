from .base import MetaAgentException

__all__ = [
    "AgenticAIClientError",
    "AgentVendorAlreadyExistsError",
    "AgentVendorNotFoundError",
]


class AgenticAIClientError(MetaAgentException):
    code = "agentic_ai_client_error"


class AgentVendorAlreadyExistsError(AgenticAIClientError):
    code = "agent_vendor_already_exists"


class AgentVendorNotFoundError(AgenticAIClientError):
    code = "agent_vendor_not_found"
