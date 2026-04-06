from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, LoginResponse
from app.services import auth_service
from app.core.security import decode_token, verify_password, hash_password
from app.core.redis import is_token_blacklisted
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserMe, UserUpdate, ChangePassword

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_current_user_id(request: Request) -> str:
    """Extract user_id from the access_token HttpOnly cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if await is_token_blacklisted(payload.get("jti", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    return payload.get("sub")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Session = Depends(get_db)):
    return await auth_service.register_user(db, payload)


@router.post("/login", response_model=LoginResponse)
async def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticates user and sets access_token + refresh_token as HttpOnly cookies."""
    return await auth_service.login_user(db, payload.email, payload.password, response)


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    """Reads refresh_token cookie, issues a new access_token cookie."""
    return await auth_service.refresh_access_token(request, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    user_id: str = Depends(get_current_user_id),
):
    """Blacklists tokens and clears both cookies."""
    await auth_service.logout_user(request, response, user_id)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    request: Request,
    response: Response,
    user_id: str = Depends(get_current_user_id),
):
    """Revokes all refresh tokens for this user across all devices and clears cookies."""
    await auth_service.logout_all_devices(request, response, user_id)


@router.get("/me", response_model=UserMe)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


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
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Password saat ini salah")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password baru minimal 6 karakter")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
