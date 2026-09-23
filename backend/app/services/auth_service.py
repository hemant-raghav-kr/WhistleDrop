"""Authentication and account services for staff moderators."""

import uuid
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.moderator import Moderator
from app.schemas.moderator import ModeratorCreate


class AuthenticationError(Exception):
    """Base class for authentication failures."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when the username/email does not exist or password does not match."""
    pass


class InactiveModeratorError(AuthenticationError):
    """Raised when credentials match but the moderator account has been deactivated."""
    pass


def get_moderator_by_id(db: Session, moderator_id: uuid.UUID) -> Optional[Moderator]:
    """Retrieve moderator by primary key ID."""
    return db.query(Moderator).filter(Moderator.id == moderator_id).first()


def get_moderator_by_email(db: Session, email: str) -> Optional[Moderator]:
    """Retrieve moderator by unique email."""
    return db.query(Moderator).filter(Moderator.email == email.lower()).first()


def get_moderator_by_username(db: Session, username: str) -> Optional[Moderator]:
    """Retrieve moderator by unique username."""
    return db.query(Moderator).filter(Moderator.username == username).first()


def create_moderator(db: Session, moderator_in: ModeratorCreate) -> Moderator:
    """Register a new moderator with salted bcrypt password hashing."""
    moderator = Moderator(
        email=moderator_in.email.lower(),
        username=moderator_in.username,
        hashed_password=get_password_hash(moderator_in.password),
        is_active=True,
    )
    db.add(moderator)
    db.commit()
    db.refresh(moderator)
    return moderator


def authenticate_moderator(
    db: Session,
    username_or_email: str,
    password: str,
) -> Moderator:
    """Verify credentials for moderator login.

    Raises:
        InvalidCredentialsError: If identifier not found or password incorrect (HTTP 401).
        InactiveModeratorError: If credentials match but account is disabled (HTTP 403).
    """
    identifier = username_or_email.strip()
    moderator = (
        db.query(Moderator)
        .filter(
            or_(
                Moderator.email == identifier.lower(),
                Moderator.username == identifier,
            )
        )
        .first()
    )

    if not moderator or not verify_password(password, moderator.hashed_password):
        raise InvalidCredentialsError("Incorrect username/email or password.")

    if not moderator.is_active:
        raise InactiveModeratorError("Moderator account is inactive.")

    return moderator
