from dataclasses import dataclass

from magicai.conversation import Conversation


@dataclass(slots=True)
class ResolvedQuestion:

    question: str

    follow_up: bool


def resolve(
    conversation: Conversation,
    question: str,
) -> ResolvedQuestion:

    #
    # Primera versión:
    # todavía no modifica nada.
    #

    return ResolvedQuestion(

        question=question,

        follow_up=False,

    )