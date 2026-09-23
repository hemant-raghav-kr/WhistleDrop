"""API Dependency Injection providers."""

import uuid
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.moderator import Moderator
from app.services.auth_service import get_moderator_by_id

security_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Provide scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_moderator(
    db: Session = Depends(get_db),
    token_auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Moderator:
    """Validate JWT token and resolve active Moderator."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate moderator credentials",
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
        moderator_id = uuid.UUID(subject)
    except ValueError:
        raise credentials_exception

    moderator = get_moderator_by_id(db, moderator_id=moderator_id)
    if not moderator:
        raise credentials_exception

    if not moderator.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive moderator account",
        )

    return moderator
