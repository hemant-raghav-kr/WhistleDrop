"""API Dependency Injection providers for multi-role authorization."""

import uuid
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.moderator import Moderator, UserRole
from app.services.auth_service import get_moderator_by_id

security_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Provide scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token_auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Moderator:
    """Validate JWT token and resolve active user from the database.
    
    Guarantees:
    - Returns HTTP 401 if token is missing, forged, expired, or user not found.
    - Returns HTTP 403 if account is disabled.
    - Resolves live database entity so role changes apply instantly.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token_auth or not token_auth.credentials:
        raise credentials_exception

    payload = decode_access_token(token_auth.credentials)
    if not payload:
        raise credentials_exception

    subject = payload.get("sub")
    if not subject:
        raise credentials_exception

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise credentials_exception

    user = get_moderator_by_id(db, moderator_id=user_id)
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account",
        )

    return user


def require_authenticated_user(
    current_user: Moderator = Depends(get_current_user),
) -> Moderator:
    """Require any active authenticated user (USER, MODERATOR, or ADMIN)."""
    return current_user


def get_current_moderator(
    current_user: Moderator = Depends(get_current_user),
) -> Moderator:
    """Require MODERATOR or ADMIN role. Returns HTTP 403 Forbidden for USER."""
    if current_user.role not in (UserRole.MODERATOR, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator privileges required to access this resource",
        )
    return current_user


def require_moderator(
    current_moderator: Moderator = Depends(get_current_moderator),
) -> Moderator:
    """Alias for get_current_moderator."""
    return current_moderator


def require_admin(
    current_user: Moderator = Depends(get_current_user),
) -> Moderator:
    """Require ADMIN role. Returns HTTP 403 Forbidden for USER and MODERATOR."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required to access this resource",
        )
    return current_user
