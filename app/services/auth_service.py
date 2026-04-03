from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.redis import (
    blacklist_token,
    store_refresh_token,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
    is_refresh_token_valid,
    is_token_blacklisted,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenResponse
from datetime import timedelta
from app.core.config import settings

async def register_user(db: Session, payload: UserCreate) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

async def login_user(db: Session, email: str, password: str) -> TokenResponse:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token, access_jti = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token, refresh_jti = create_refresh_token({"sub": str(user.id), "role": user.role.value})

    # Store refresh token in Redis
    await store_refresh_token(
        str(user.id),
        refresh_jti,
        expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )

async def refresh_access_token(refresh_token: str) -> dict:
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    jti = payload.get("jti")

    if not await is_refresh_token_valid(user_id, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    access_token, _ = create_access_token({"sub": user_id, "role": payload.get("role")})

    return {"access_token": access_token, "token_type": "bearer"}

async def logout_user(access_token: str, refresh_token: str, user_id: str):
    # Blacklist access token
    payload = decode_token(access_token)
    if payload and payload.get("jti"):
        remaining = int(payload["exp"] - timedelta(seconds=0).total_seconds())
        await blacklist_token(payload["jti"], settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    # Revoke refresh token
    refresh_payload = decode_token(refresh_token)
    if refresh_payload and refresh_payload.get("jti"):
        await revoke_refresh_token(user_id, refresh_payload["jti"])

async def logout_all_devices(user_id: str, access_token: str):
    """Logout from all devices"""
    payload = decode_token(access_token)
    if payload and payload.get("jti"):
        await blacklist_token(payload["jti"], settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    await revoke_all_refresh_tokens(user_id)
