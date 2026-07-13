import sqlite3

from fastapi import APIRouter, HTTPException, Query

from magicai.assistant import MagicAI
from magicai.api.health import build_health_payload
from magicai.api.schemas import (
    AskRequest,
    AskResponse,
    ConversationDeleteResponse,
    ConversationDetailResponse,
    ConversationRenameRequest,
    ConversationSummaryResponse,
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

    payload = result.to_dict()
    try:
        conversation_manager.save(
            session_id,
            conversation,
            last_result={
                "session_id": session_id,
                **payload,
            },
        )
    except (OSError, sqlite3.Error):
        payload["warnings"] = [
            *payload.get("warnings", []),
            "La respuesta es válida, pero no se pudo guardar esta conversación en el historial local.",
        ]

    return AskResponse(
        session_id=session_id,
        **payload,
    )


@router.get(
    "/conversations",
    response_model=list[ConversationSummaryResponse],
)
def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
):
    return [
        _summary_response(summary)
        for summary in conversation_manager.list(limit=limit)
    ]


@router.get(
    "/conversations/{session_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation(session_id: str):
    record = conversation_manager.load(session_id)
    if not record:
        raise _conversation_not_found()

    summary = record.summary
    return ConversationDetailResponse(
        session_id=summary.session_id,
        title=summary.title,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        message_count=summary.message_count,
        messages=[
            {"role": message.role, "content": message.content}
            for message in record.conversation.history
        ],
        last_result=record.last_result,
    )


@router.patch(
    "/conversations/{session_id}",
    response_model=ConversationSummaryResponse,
)
def rename_conversation(
    session_id: str,
    request: ConversationRenameRequest,
):
    summary = conversation_manager.rename(session_id, request.title)
    if not summary:
        raise _conversation_not_found()
    return _summary_response(summary)


@router.delete(
    "/conversations/{session_id}",
    response_model=ConversationDeleteResponse,
)
def delete_conversation(session_id: str):
    deleted = conversation_manager.delete(session_id)
    if not deleted:
        raise _conversation_not_found()
    return ConversationDeleteResponse(
        session_id=session_id,
        deleted=True,
    )


def _summary_response(summary) -> ConversationSummaryResponse:
    return ConversationSummaryResponse(
        session_id=summary.session_id,
        title=summary.title,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        message_count=summary.message_count,
    )


def _conversation_not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "code": "conversation_not_found",
            "message": "The requested local conversation does not exist.",
            "retryable": False,
        },
    )
