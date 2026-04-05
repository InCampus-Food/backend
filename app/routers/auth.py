from fastapi import APIRouter, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services import auth_service
from app.core.security import decode_token
from app.core.redis import is_token_blacklisted

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid token")
    if await is_token_blacklisted(payload.get("jti", "")):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Token has been revoked")
    return payload.get("sub")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Session = Depends(get_db)):
    return await auth_service.register_user(db, payload)

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    return await auth_service.login_user(db, payload.email, payload.password)

@router.post("/refresh")
async def refresh(refresh_token: str = Header(..., alias="X-Refresh-Token")):
    return await auth_service.refresh_access_token(refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: str = Header(..., alias="X-Refresh-Token"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_id: str = Depends(get_current_user_id),
):
    await auth_service.logout_user(credentials.credentials, refresh_token, user_id)

@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_id: str = Depends(get_current_user_id),
):
    await auth_service.logout_all_devices(user_id, credentials.credentials)


from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserMe

@router.get("/me", response_model=UserMe)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


from app.schemas.user import UserUpdate, ChangePassword
from app.core.security import verify_password, hash_password

@router.patch("/me", response_model=UserMe)
async def update_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Password saat ini salah")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password baru minimal 6 karakter")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
