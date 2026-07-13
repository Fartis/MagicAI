from fastapi import APIRouter

from magicai.assistant import MagicAI
from magicai.api.health import build_health_payload
from magicai.api.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    MetaResponse,
)
from magicai.conversation.manager import ConversationManager
from magicai.judge_result import (
    JudgeConfidence,
    JudgeOrigin,
    JudgeStatus,
)
from magicai.versioning import (
    API_CONTRACT_VERSION,
    JUDGE_RESULT_SCHEMA_VERSION,
    get_project_version,
)


router = APIRouter()

assistant = MagicAI()
conversation_manager = ConversationManager()


@router.get("/")
def root():
    return {
        "status": "ok",
        "project": "MagicAI",
        "project_version": get_project_version(),
        "api_contract_version": API_CONTRACT_VERSION,
        "judge_result_schema_version": JUDGE_RESULT_SCHEMA_VERSION,
        "ui": "/ui",
    }


@router.get("/meta", response_model=MetaResponse)
def meta():
    return {
        "project": "MagicAI",
        "project_version": get_project_version(),
        "api_contract_version": API_CONTRACT_VERSION,
        "judge_result_schema_version": JUDGE_RESULT_SCHEMA_VERSION,
        "authority": "judge",
        "judge_statuses": [item.value for item in JudgeStatus],
        "judge_origins": [item.value for item in JudgeOrigin],
        "confidence_levels": [item.value for item in JudgeConfidence],
    }


@router.get("/health", response_model=HealthResponse)
def health():
    return build_health_payload()


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    session_id, conversation = conversation_manager.get_or_create(
        request.session_id
    )

    result = assistant.ask_result(
        conversation,
        request.question,
    )

    return AskResponse(
        session_id=session_id,
        **result.to_dict(),
    )
