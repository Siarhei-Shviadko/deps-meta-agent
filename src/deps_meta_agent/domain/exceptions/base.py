__all__ = ["MetaAgentException", "NotFoundError", "IllegalArgument"]


class MetaAgentException(Exception):
    code = "meta_agent_exception"


class BusinessException(MetaAgentException):
    code = "business_exception"


class NotFoundError(MetaAgentException):
    code = "not_found_error"


class IllegalArgument(MetaAgentException):
    code = "illegal_argument"
