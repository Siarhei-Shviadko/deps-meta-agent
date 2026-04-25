from datetime import datetime, timezone

from deps_meta_agent.domain.model import AgenticManifest
from deps_meta_agent.infrastructure.adapters.types import RawConversationTurn

__all__ = ["Session"]


class Session:  # noqa: WPS230
    def __init__(
        self,
        conversation_id: str,
        manifests: list[AgenticManifest],
    ) -> None:
        self.conversation_id = conversation_id
        self.manifests = manifests
        self.created_at = datetime.now(timezone.utc)
        self.last_accessed_at = datetime.now(timezone.utc)

        self.active_agent_code: str | None = None

        self.conversation_history: list[RawConversationTurn] = []

        self.supervisor_notes: list[str] = []

    def set_active_agent(self, agent_code: str | None) -> None:
        self.active_agent_code = agent_code
        self.last_accessed_at = datetime.now(timezone.utc)

    def has_active_agent(self) -> bool:
        return self.active_agent_code is not None

    def add_conversation_turn(self, question: str, answer: str) -> None:
        self.conversation_history.append(
            {
                "question": question,
                "answer": answer,
            }
        )
        self.last_accessed_at = datetime.now(timezone.utc)

    def add_supervisor_note(self, note: str) -> None:
        self.supervisor_notes.append(note)
        self.last_accessed_at = datetime.now(timezone.utc)

    def clear_active_agent(self) -> None:
        self.active_agent_code = None
        self.last_accessed_at = datetime.now(timezone.utc)

    def update_manifests(self, manifests: list[AgenticManifest]) -> None:
        self.manifests = manifests
        self.last_accessed_at = datetime.now(timezone.utc)
