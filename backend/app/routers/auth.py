from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    create_refresh_token_session,
    get_current_user,
    hash_password,
    revoke_refresh_token_session,
    rotate_refresh_token_session,
    verify_password,
)
from app.config import get_settings
from app.database import get_db
from app.models import Company, StudentProfile, User, UserRole
from app.schemas import LoginRequest, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
login_attempts: dict[str, list[datetime]] = {}


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def apply_login_rate_limit(request: Request, email: str) -> None:
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=settings.login_rate_limit_window_seconds)
    key = f"{client_ip(request)}:{email.lower()}"
    attempts = [attempt for attempt in login_attempts.get(key, []) if attempt > window_start]
    if len(attempts) >= settings.login_rate_limit_attempts:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")
    attempts.append(now)
    login_attempts[key] = attempts


def clear_login_rate_limit(request: Request, email: str) -> None:
    login_attempts.pop(f"{client_ip(request)}:{email.lower()}", None)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/auth",
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, response: Response, request: Request, db: Session = Depends(get_db)):
    if payload.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts must be created by seed script or an existing admin",
        )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()
    if payload.role == UserRole.student:
        db.add(StudentProfile(user_id=user.id))
    elif payload.role == UserRole.company:
        db.add(Company(user_id=user.id, company_name=payload.name))
    db.commit()
    db.refresh(user)
    refresh_token, _ = create_refresh_token_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    set_refresh_cookie(response, refresh_token)
    return Token(access_token=create_access_token(str(user.id)), user=user)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    apply_login_rate_limit(request, payload.email)
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    clear_login_rate_limit(request, payload.email)
    refresh_token, _ = create_refresh_token_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    set_refresh_cookie(response, refresh_token)
    return Token(access_token=create_access_token(str(user.id)), user=user)


@router.post("/refresh", response_model=Token)
def refresh(response: Response, request: Request, db: Session = Depends(get_db)):
    raw_refresh_token = request.cookies.get(settings.refresh_cookie_name)
    access_token, new_refresh_token, user = rotate_refresh_token_session(
        db,
        raw_refresh_token or "",
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    set_refresh_cookie(response, new_refresh_token)
    return Token(access_token=access_token, user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    revoke_refresh_token_session(db, request.cookies.get(settings.refresh_cookie_name))
    clear_refresh_cookie(response)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
