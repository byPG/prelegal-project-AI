from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, create_model, field_validator

from .templates import DOCUMENT_IDS

# bcrypt's limit is 72 *bytes*, not characters, so a naive Field(max_length=72)
# lets multi-byte passwords (accents, emoji, ...) slip past validation and
# blow up inside bcrypt.hashpw/checkpw instead of returning a clean 422.
def _validate_password_byte_length(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes when UTF-8 encoded")
    return value


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

    _validate_password = field_validator("password")(_validate_password_byte_length)


class SigninRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    _validate_password = field_validator("password")(_validate_password_byte_length)


class UserResponse(BaseModel):
    id: int
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Chat (PREL-5: AI chat; PREL-6: generalized to all 11 document types) ---

# Any of the 11 catalog documents, or None while the assistant hasn't
# established which one the user needs yet. Built once from templates.py's
# static catalog (unlike field_updates below, this doesn't vary per
# request) so the LLM's structured output is constrained to a real
# document id rather than free-typing something that doesn't exist.
DocumentIdLiteral = Literal[tuple(DOCUMENT_IDS)]  # type: ignore[valid-type]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class GreetingResponse(BaseModel):
    reply: str


class ChatTurnRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    document_id: str | None = None
    fields: dict[str, str] = {}


class ChatTurnResponse(BaseModel):
    reply: str
    document_id: str | None
    # Sparse: only what the model changed this turn, not merged with the
    # request's known fields. The client merges this into its own current
    # state so a concurrent edit made while the request was in flight
    # doesn't get overwritten by a stale echoed-back value.
    fields: dict[str, str | None]


def build_chat_reply_model(field_keys: list[str]) -> type[BaseModel]:
    """Builds a per-request structured-output schema for the LLM.

    field_keys come from whichever document is currently active (empty
    before a document type has been established), so the model is
    schema-constrained to exactly that document's valid field keys for
    this turn — not free-typing key names that might not match ours.
    `extra="forbid"` makes that a hard constraint (additionalProperties:
    false) in the generated JSON schema, not just a naming convention.
    """
    field_updates_fields = {key: (str | None, None) for key in field_keys}
    FieldUpdates = create_model(
        "FieldUpdates", __config__=ConfigDict(extra="forbid"), **field_updates_fields
    )
    return create_model(
        "ChatTurnReply",
        reply=(str, ...),
        document_id=(DocumentIdLiteral | None, None),
        field_updates=(FieldUpdates, FieldUpdates()),
    )
