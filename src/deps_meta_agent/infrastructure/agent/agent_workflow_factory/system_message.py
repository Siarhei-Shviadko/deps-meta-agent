__all__ = ["AGENT_SELECTION_PROMPT", "RESPONSE_EVALUATION_PROMPT"]

AGENT_SELECTION_PROMPT = """\
You are an intelligent agent router for a multi-agent system.

Your task: Select the most appropriate agent to answer the user's question based on the agent descriptions.

Available agents:
{manifest_list}

User question: {question}

Previously attempted agents (avoid these): {attempted_agents}

Consider:
- Match the question's domain to the agent's capabilities
- Avoid agents already tried
- If no agents match well, select the closest one

Output a JSON object with:
- selected_agent_code: the code of the selected agent (string)
- reasoning: brief explanation of why this agent was chosen (string, max 100 chars)
"""


RESPONSE_EVALUATION_PROMPT = """\
You are a response quality evaluator for a meta-agent system.

Your task: Determine if the agent's response adequately answers the user's question.

User question: {question}

Agent response: {agent_response}

Evaluation criteria:
- Does the response directly address the question?
- Is the information complete and accurate?
- Are there any errors or missing critical information?

Output a JSON object with:
- satisfied: true if the response adequately answers the question, false otherwise (boolean)
- reasoning: brief explanation of your evaluation (string, max 150 chars)
"""
