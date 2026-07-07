from fastapi import APIRouter

from magicai.assistant import MagicAI
from magicai.api.schemas import AskRequest, AskResponse


router = APIRouter()

assistant = MagicAI()


@router.get("/")
def root():

    return {
        "status": "ok",
        "project": "MagicAI",
        "version": "0.1.0",
    }


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):

    answer = assistant.ask(request.question)

    return AskResponse(answer=answer)