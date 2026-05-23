"""Authentication router — Google OAuth and JWT token management."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import jwt
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.deps import get_db, require_user
from app.models import User, UserRead

router = APIRouter()


class GoogleLoginRequest(BaseModel):
    """Request body for Google login — contains the OAuth credential token."""

    credential: str
    # Optional refresh token for Google Drive access
    refresh_token: str | None = None


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead


def create_access_token(user_id: str) -> str:
    """Create a JWT access token for the given user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


@router.post("/google/login", response_model=TokenResponse)
async def google_login(body: GoogleLoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """
    Authenticate with Google OAuth.
    The frontend sends a Google ID token (from Google Sign-In).
    We verify it and create/update the user in our database.
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            body.credential, google_requests.Request(), settings.google_client_id
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = idinfo.get("email")
    name = idinfo.get("name", "")
    avatar_url = idinfo.get("picture")

    if not email:
        raise HTTPException(status_code=401, detail="Email not provided by Google")

    # Find or create user
    result = await db.exec(select(User).where(User.email == email))
    user = result.first()

    if user is None:
        user = User(email=email, name=name, avatar_url=avatar_url)
        db.add(user)
    else:
        user.name = name
        user.avatar_url = avatar_url

    # Store refresh token if provided (for Google Drive access)
    if body.refresh_token:
        user.google_refresh_token = body.refresh_token

    await db.commit()
    await db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(require_user)) -> UserRead:
    """Get the current authenticated user."""
    return UserRead.model_validate(user)
