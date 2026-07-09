from pydantic import BaseModel


class AskRequest(BaseModel):

    question: str
    session_id: str | None = None


class AskResponse(BaseModel):

    answer: str
    session_id: str
