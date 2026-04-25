from deps_meta_agent.domain.exceptions import MetaAgentException

__all__ = ["SpecificAgentAdapterError"]


class SpecificAgentAdapterError(MetaAgentException):
    code = "specific_agent_adapter_error"

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
        agent_url: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.agent_url = agent_url
