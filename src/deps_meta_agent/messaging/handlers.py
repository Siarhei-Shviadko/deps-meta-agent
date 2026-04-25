import logging

from deps_message_flow.commands.consumer.command_message import CommandMessage
from deps_message_flow.events.subscriber.domain_event_envelope import (
    DomainEventEnvelope,
)

logger = logging.getLogger(__name__)


def test_event_handler(dee: DomainEventEnvelope) -> None:
    pass


def test_command_handler(command_message: CommandMessage):
    pass
