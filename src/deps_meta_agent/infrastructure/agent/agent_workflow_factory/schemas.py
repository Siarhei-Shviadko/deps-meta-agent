from pydantic import BaseModel

__all__ = ["AgentSelectionOutput", "ResponseEvaluationOutput"]


class AgentSelectionOutput(BaseModel):
    selected_agent_code: str
    reasoning: str


class ResponseEvaluationOutput(BaseModel):
    satisfied: bool
    reasoning: str
