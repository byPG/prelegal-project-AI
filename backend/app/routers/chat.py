from fastapi import APIRouter, HTTPException, status

from ..llm import LlmUnavailableError, complete_structured
from ..mutual_nda import GREETING, build_system_prompt
from ..schemas import ChatTurnReply, ChatTurnRequest, ChatTurnResponse, GreetingResponse
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

    system_prompt = build_system_prompt(payload.fields.model_dump())
    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": message.role, "content": message.content} for message in payload.messages
    ]

    try:
        result = complete_structured(messages, ChatTurnReply)
    except DailyLimitExceededError as exc:
        # Raised here (rather than only by the pre-check above) when the
        # primary model failed and the fallback attempt itself would blow
        # the remaining daily budget.
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    except LlmUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is temporarily unavailable. Please try again shortly.",
        )

    # Deliberately sparse (only what changed this turn), not a merge with
    # payload.fields: the frontend merges this into whatever its *current*
    # form state is when the response lands, not a stale request-time
    # snapshot — otherwise a manual edit made while a chat request is in
    # flight gets silently overwritten by the echoed-back old value.
    return ChatTurnResponse(reply=result.reply, fields=result.field_updates)
