from fastapi import APIRouter, HTTPException, status

from ..documents import GREETING, build_system_prompt
from ..llm import LlmUnavailableError, complete_structured
from ..schemas import ChatTurnRequest, ChatTurnResponse, GreetingResponse, build_chat_reply_model
from ..templates import get_document
from ..usage import DailyLimitExceededError, daily_request_counter

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/greeting", response_model=GreetingResponse)
def greeting() -> GreetingResponse:
    # Hardcoded on purpose: the opening message never varies, so answering
    # it never needs to spend any of the free-tier daily request budget.
    return GreetingResponse(reply=GREETING)


@router.post("/message", response_model=ChatTurnResponse)
def send_message(payload: ChatTurnRequest) -> ChatTurnResponse:
    try:
        daily_request_counter.record_and_check()
    except DailyLimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))

    active_document = get_document(payload.document_id) if payload.document_id else None
    field_keys = [field.key for field in active_document.fields] if active_document else []

    system_prompt = build_system_prompt(active_document.id if active_document else None, payload.fields)
    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": message.role, "content": message.content} for message in payload.messages
    ]

    reply_model = build_chat_reply_model(field_keys)

    try:
        result = complete_structured(messages, reply_model)
    except DailyLimitExceededError as exc:
        # Raised here (rather than only by the pre-check above) when the
        # first attempt failed and the retry attempt itself would blow the
        # remaining daily budget.
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    except LlmUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is temporarily unavailable. Please try again shortly.",
        )

    # document_id is "sticky": once established, only an explicit new
    # value from the model changes it — the same sparse-update philosophy
    # as fields, so a turn where the model doesn't mention it can't
    # accidentally reset an already-established document type.
    resolved_document_id = result.document_id or payload.document_id

    # Deliberately sparse (only what changed this turn), not a merge with
    # payload.fields: the frontend merges this into whatever its *current*
    # form state is when the response lands, not a stale request-time
    # snapshot — otherwise a manual edit made while a chat request is in
    # flight gets silently overwritten by the echoed-back old value.
    field_updates = result.field_updates.model_dump() if field_keys else {}

    return ChatTurnResponse(reply=result.reply, document_id=resolved_document_id, fields=field_updates)
