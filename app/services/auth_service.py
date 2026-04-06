from fastapi import HTTPException, Request, Response, status
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
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, LoginResponse
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


async def login_user(db: Session, email: str, password: str, response: Response) -> LoginResponse:
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

    access_token, _ = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token, refresh_jti = create_refresh_token({"sub": str(user.id), "role": user.role.value})

    # Store refresh token JTI in Redis
    await store_refresh_token(
        str(user.id),
        refresh_jti,
        expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    # Set access_token as HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Set refresh_token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

    return LoginResponse(user=UserResponse.model_validate(user))


async def refresh_access_token(request: Request, response: Response) -> dict:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    jti = payload.get("jti")

    if not await is_refresh_token_valid(user_id, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    access_token, _ = create_access_token({"sub": user_id, "role": payload.get("role")})

    # Rotate access_token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {"message": "Token refreshed"}


async def logout_user(request: Request, response: Response, user_id: str):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    # Blacklist access token
    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("jti"):
            await blacklist_token(payload["jti"], settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    # Revoke refresh token
    if refresh_token:
        refresh_payload = decode_token(refresh_token)
        if refresh_payload and refresh_payload.get("jti"):
            await revoke_refresh_token(user_id, refresh_payload["jti"])

    # Clear cookies from browser
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


async def logout_all_devices(request: Request, response: Response, user_id: str):
    """Logout from all devices — revokes all refresh tokens for the user."""
    access_token = request.cookies.get("access_token")

    # Blacklist current access token
    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("jti"):
            await blacklist_token(payload["jti"], settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    # Revoke every refresh token for this user in Redis
    await revoke_all_refresh_tokens(user_id)

    # Clear cookies on current device
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
