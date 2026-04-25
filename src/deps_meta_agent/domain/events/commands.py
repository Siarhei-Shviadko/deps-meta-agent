from dataclasses import dataclass

from deps_message_flow.commands.common import Command

__all__ = ["TestCommand", "TestCommandReply"]


class TestCommand(Command):  # noqa: WPS604
    pass  # noqa: WPS604


@dataclass
class TestCommandReply(Command):
    test: str
