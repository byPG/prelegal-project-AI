import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_connection
from ..deps import get_current_user
from ..schemas import SigninRequest, SignupRequest, TokenResponse, UserResponse
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Hashed once at import time and compared against on every "unknown email"
# signin attempt so lookup failures take about as long as a real password
# check — otherwise the bcrypt-free fast path leaks which emails are registered.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-password-used-only-for-timing-safety")


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> UserResponse:
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
                (payload.email, hash_password(payload.password)),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Relies on the UNIQUE constraint on users.email as the source of
        # truth (rather than a SELECT-then-INSERT check) so concurrent
        # signups for the same address can't both slip past a race and
        # surface as an unhandled 500.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    return UserResponse(id=user_id, email=payload.email)


@router.post("/signin", response_model=TokenResponse)
def signin(payload: SigninRequest) -> TokenResponse:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, hashed_password FROM users WHERE email = ?", (payload.email,)
        ).fetchone()

    hashed_password = row["hashed_password"] if row is not None else _DUMMY_PASSWORD_HASH
    password_matches = verify_password(payload.password, hashed_password)

    if row is None or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=str(row["id"]))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
