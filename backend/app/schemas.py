from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

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


# --- Chat (PREL-5: AI chat, still just the Mutual NDA) ---


class MutualNdaFields(BaseModel):
    """Mirrors frontend/types/mutual-nda.ts's MutualNdaFormData keys.

    All-optional: as a request payload, an unset field means "not filled
    in yet"; as part of a model response, it means "no new information
    about this field in the latest message."
    """

    partyOneName: str | None = None
    partyOneAddress: str | None = None
    partyTwoName: str | None = None
    partyTwoAddress: str | None = None
    purpose: str | None = None
    effectiveDate: str | None = None
    mndaTerm: str | None = None
    termOfConfidentiality: str | None = None
    governingLaw: str | None = None
    jurisdiction: str | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class GreetingResponse(BaseModel):
    reply: str


class ChatTurnRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    fields: MutualNdaFields = MutualNdaFields()


class ChatTurnReply(BaseModel):
    """Structured-output shape the model itself is asked to produce."""

    reply: str
    field_updates: MutualNdaFields = MutualNdaFields()


class ChatTurnResponse(BaseModel):
    reply: str
    # Sparse: the same field_updates the model produced, not merged with
    # the request's known fields. The client merges this into its own
    # current state so a concurrent edit made while the request was in
    # flight doesn't get overwritten by a stale echoed-back value.
    fields: MutualNdaFields
