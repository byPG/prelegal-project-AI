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
