import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from ..settings import OrchestratorSettings
from ..state import OrchestratorState
from ..types import AgenticPayload
from .agent_caller import AgentCaller
from .schemas import AgentSelectionOutput, ResponseEvaluationOutput
from .system_message import AGENT_SELECTION_PROMPT, RESPONSE_EVALUATION_PROMPT

__all__ = ["OrchestratorWorkflowFactory"]

MAX_RESPONSE_PREVIEW_LENGTH = 2000


class OrchestratorWorkflowFactory:  # noqa: WPS214
    def __init__(
        self,
        llm: BaseChatModel,
        settings: OrchestratorSettings,
        agent_caller: AgentCaller,
    ) -> None:
        self._llm = llm
        self._settings = settings
        self._agent_caller = agent_caller

        self._logger = logging.getLogger(self.__class__.__name__)

    def create_workflow(self) -> CompiledStateGraph:
        graph_builder = StateGraph(OrchestratorState)

        graph_builder.add_node("select_agent", self._select_agent)
        graph_builder.add_node("call_agent", self._call_agent)
        graph_builder.add_node("evaluate_response", self._evaluate_response)

        graph_builder.set_entry_point("select_agent")
        graph_builder.add_edge("select_agent", "call_agent")
        graph_builder.add_edge("call_agent", "evaluate_response")
        graph_builder.add_conditional_edges("evaluate_response", self._route_decision)

        return graph_builder.compile()

    def _check_active_agent_reuse(self, state: OrchestratorState) -> str | None:
        if not state.session.has_active_agent():
            return None

        active_code = state.session.active_agent_code
        if active_code in state.attempted_agents:
            self._logger.info("Active agent '%s' previously attempted, performing fresh selection", active_code)
            state.session.clear_active_agent()
            return None

        if any(m.code == active_code for m in state.available_manifests):
            self._logger.info("Reusing active agent '%s' from session", active_code)
            return active_code
        else:
            self._logger.warning("Active agent '%s' not in current manifests, clearing", active_code)
            state.session.clear_active_agent()
            return None

    def _get_available_unattempted_agents(self, state: OrchestratorState) -> list:
        return [m for m in state.available_manifests if m.code not in state.attempted_agents]

    def _select_agent_with_llm(self, available_agents: list, state: OrchestratorState) -> AgentSelectionOutput:
        manifest_list = "\n".join(
            [f"- Code: {m.code}, Name: {m.name}, Description: {m.description}" for m in available_agents],
        )

        attempted_agents_str = ", ".join(state.attempted_agents) if state.attempted_agents else "none"

        prompt = AGENT_SELECTION_PROMPT.format(
            manifest_list=manifest_list,
            question=state.question,
            attempted_agents=attempted_agents_str,
        )

        structured_llm = self._llm.with_structured_output(AgentSelectionOutput)
        return structured_llm.invoke([SystemMessage(content=prompt)])

    def _select_agent(self, state: OrchestratorState) -> OrchestratorState:
        if not state.available_manifests:
            self._logger.error("No manifests available for selection")
            state.final_answer = "No agents are available to handle your request."
            return state

        active_agent_code = self._check_active_agent_reuse(state)
        if active_agent_code:
            state.current_agent_code = active_agent_code
            state.iteration_count += 1
            self._logger.info("Reusing active agent '%s' (iteration %s)", active_agent_code, state.iteration_count)
            return state

        available_agents = self._get_available_unattempted_agents(state)

        if not available_agents:
            self._logger.warning("All available agents have been attempted")
            state.final_answer = (
                f"I tried all available agents but couldn't find a satisfactory answer. "
                f"Last response: {state.current_agent_response}"
            )
            return state

        result = self._select_agent_with_llm(available_agents, state)
        state.current_agent_code = result.selected_agent_code
        state.current_agent_response = result.reasoning
        state.iteration_count += 1

        self._logger.info(
            "Selected agent '%s' (iteration %s): %s",
            result.selected_agent_code,
            state.iteration_count,
            result.reasoning,
        )

        return state

    async def _call_agent(self, state: OrchestratorState) -> OrchestratorState:
        self._logger.info("Calling agent '%s'", state.current_agent_code)
        state.current_agent_events = []
        state.evaluation_reasoning = None

        if not state.current_agent_code:
            self._logger.error("No agent selected to call")
            state.final_answer = "Internal error: No agent was selected."
            return state

        manifest = next(
            (m for m in state.session.manifests if m.code == state.current_agent_code),
            None,
        )

        if not manifest:
            self._logger.error("Manifest not found in session for agent '%s'", state.current_agent_code)
            state.attempted_agents.append(state.current_agent_code)
            state.current_agent_response = f"Error: Manifest not found for agent '{state.current_agent_code}'."
            return state

        state.attempted_agents.append(state.current_agent_code)

        try:
            payload = AgenticPayload(
                conversation_id=state.conversation_id,
                turn_id=state.turn_id,
                question=state.question,
                arguments=state.arguments,
                context_bundle=state.context_bundle,
            )

            events, response_text = await self._agent_caller.call_agent(manifest, payload)
            state.current_agent_events = events
            state.current_agent_response = response_text

        except Exception as e:
            self._logger.error("Error calling agent '%s': %s", state.current_agent_code, e, exc_info=True)
            state.current_agent_response = f"Error calling agent: {str(e)}"

        return state

    def _create_evaluation_prompt(self, question: str, response: str) -> str:
        truncated_response = response[:MAX_RESPONSE_PREVIEW_LENGTH]
        return RESPONSE_EVALUATION_PROMPT.format(
            question=question,
            agent_response=truncated_response,
        )

    def _evaluate_with_llm(self, prompt: str) -> ResponseEvaluationOutput:
        structured_llm = self._llm.with_structured_output(ResponseEvaluationOutput)
        return structured_llm.invoke([SystemMessage(content=prompt)])

    def _update_state_with_evaluation(
        self,
        state: OrchestratorState,
        evaluation: ResponseEvaluationOutput,
    ) -> None:
        state.evaluation_reasoning = evaluation.reasoning

        evaluation_note = (
            f"Agent '{state.current_agent_code}' evaluation: "
            f"{'satisfied' if evaluation.satisfied else 'not satisfied'} - {evaluation.reasoning}"
        )
        state.session.add_supervisor_note(evaluation_note)

        if evaluation.satisfied:
            state.final_answer = state.current_agent_response
        else:
            self._logger.info(
                "Response from '%s' not satisfactory, will attempt another agent if available",
                state.current_agent_code,
            )

    def _evaluate_response(self, state: OrchestratorState) -> OrchestratorState:
        self._logger.info("Evaluating response: %s", state.current_agent_response)

        if not state.current_agent_response:
            self._logger.warning("No response to evaluate")
            state.session.add_supervisor_note("No response received from agent")
            return state

        prompt = self._create_evaluation_prompt(state.question, state.current_agent_response)
        evaluation = self._evaluate_with_llm(prompt)

        self._logger.info("Response evaluation: satisfied=%s, reasoning=%s", evaluation.satisfied, evaluation.reasoning)

        self._update_state_with_evaluation(state, evaluation)

        return state

    def _should_end_workflow(self, state: OrchestratorState) -> bool:
        return state.final_answer is not None or state.iteration_count >= self._settings.max_iterations

    def _create_max_iterations_message(self, state: OrchestratorState) -> str:
        return (
            f"I tried {state.iteration_count} agents but couldn't provide a fully satisfactory answer. "
            f"Best response: {state.current_agent_response}"
        )

    def _route_decision(self, state: OrchestratorState) -> str:
        self._logger.info(
            "Routing decision: final_answer=%s, iteration_count=%s", state.final_answer, state.iteration_count
        )

        if state.final_answer:
            self._logger.info("Final answer determined, ending workflow")
            return END

        if state.iteration_count >= self._settings.max_iterations:
            self._logger.warning("Max iterations (%s) reached", self._settings.max_iterations)
            state.final_answer = self._create_max_iterations_message(state)
            return END

        self._logger.info("Response not satisfactory, attempting next agent (iteration %s)", state.iteration_count)
        return "select_agent"
