from fastapi import APIRouter

from magicai.assistant import MagicAI
from magicai.api.schemas import AskRequest, AskResponse
from magicai.conversation.manager import ConversationManager


router = APIRouter()

assistant = MagicAI()
conversation_manager = ConversationManager()


@router.get("/")
def root():

    return {
        "status": "ok",
        "project": "MagicAI",
        "version": "0.1.0",
    }


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):

    session_id, conversation = conversation_manager.get_or_create(
        request.session_id
    )

    answer = assistant.ask(
        conversation,
        request.question,
    )

    return AskResponse(
        answer=answer,
        session_id=session_id,
    )
