import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import RefreshToken, User, UserRole


settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token_session(
    db: Session,
    user: User,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, RefreshToken]:
    token = secrets.token_urlsafe(64)
    session = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(token),
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
        user_agent=(user_agent or "")[:255] or None,
        ip_address=(ip_address or "")[:64] or None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return token, session


def rotate_refresh_token_session(
    db: Session,
    raw_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str, User]:
    session = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_refresh_token(raw_token)).first()
    if not session or session.revoked_at is not None or session.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    new_raw_token = secrets.token_urlsafe(64)
    new_session = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_raw_token),
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
        user_agent=(user_agent or "")[:255] or None,
        ip_address=(ip_address or "")[:64] or None,
    )
    db.add(new_session)
    db.flush()
    session.revoked_at = datetime.utcnow()
    session.replaced_by_token_id = new_session.id
    db.commit()
    db.refresh(user)
    return create_access_token(str(user.id)), new_raw_token, user


def revoke_refresh_token_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    session = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_refresh_token(raw_token)).first()
    if session and session.revoked_at is None:
        session.revoked_at = datetime.utcnow()
        db.commit()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError as exc:
        raise credentials_error from exc

    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_error
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user


def require_role(*roles: UserRole):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return checker
