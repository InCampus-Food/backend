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
