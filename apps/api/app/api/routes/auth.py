from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_session_token, get_password_hash, verify_password
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import AuthStatusResponse, ChangePasswordRequest, LoginRequest, UserResponse
from app.services.audit_service import create_audit_log
from app.services.system_log_service import create_system_log

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite=settings.session_cookie_samesite,
        secure=settings.session_cookie_secure,
        max_age=settings.session_max_age_seconds,
    )


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)) -> UserResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        create_system_log(db, "WARNING", "auth", "Login failed.", {"username": payload.username})
        create_audit_log(db, "auth.login_failed", "User", None, before={"username": payload.username}, request=request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

    token = create_session_token(user.id)
    _set_session_cookie(response, token)
    create_system_log(db, "INFO", "auth", "Login success.", {"username": user.username})
    create_audit_log(db, "auth.login", "User", str(user.id), actor_user=user, after={"username": user.username}, request=request)
    return UserResponse.model_validate(user)


@router.post("/logout")
def logout(response: Response, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, secure=settings.session_cookie_secure, samesite=settings.session_cookie_samesite)
    create_system_log(db, "INFO", "auth", "Logout success.", {"username": current_user.username})
    create_audit_log(db, "auth.logout", "User", str(current_user.id), actor_user=current_user, request=request)
    return {"success": True}


@router.get("/me", response_model=AuthStatusResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthStatusResponse:
    return AuthStatusResponse(authenticated=True, user=UserResponse.model_validate(current_user))


@router.post("/change-password", response_model=UserResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    if not verify_password(payload.current_password, current_user.password_hash):
        create_system_log(db, "WARNING", "auth", "Password change failed.", {"username": current_user.username})
        create_audit_log(db, "auth.change_password_failed", "User", str(current_user.id), actor_user=current_user, request=request)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

    current_user.password_hash = get_password_hash(payload.new_password)
    current_user.force_password_change = False
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    create_system_log(db, "INFO", "auth", "Password changed.", {"username": current_user.username})
    create_audit_log(db, "auth.change_password", "User", str(current_user.id), actor_user=current_user, after={"force_password_change": False}, request=request)
    return UserResponse.model_validate(current_user)
