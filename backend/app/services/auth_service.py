"""Authentication, registration, and user management services."""

import uuid
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.moderator import Moderator, UserRole
from app.schemas.auth import RegisterRequest
from app.schemas.moderator import ModeratorCreate


class AuthenticationError(Exception):
    """Base class for authentication failures."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when the username/email does not exist or password does not match."""
    pass


class InactiveModeratorError(AuthenticationError):
    """Raised when credentials match but the account has been deactivated."""
    pass


class DuplicateEmailError(AuthenticationError):
    """Raised when registering an email that already exists."""
    pass


class AdminProtectedError(AuthenticationError):
    """Raised when attempting to modify or downgrade the protected admin account."""
    pass


def get_moderator_by_id(db: Session, moderator_id: uuid.UUID) -> Optional[Moderator]:
    """Retrieve user/moderator by primary key ID."""
    return db.query(Moderator).filter(Moderator.id == moderator_id).first()


def get_moderator_by_email(db: Session, email: str) -> Optional[Moderator]:
    """Retrieve user/moderator by unique email."""
    return db.query(Moderator).filter(Moderator.email == email.lower().strip()).first()


def get_moderator_by_username(db: Session, username: str) -> Optional[Moderator]:
    """Retrieve user/moderator by unique username."""
    return db.query(Moderator).filter(Moderator.username == username.strip()).first()


def register_user(db: Session, reg_in: RegisterRequest) -> Moderator:
    """Register a new user account. Unconditionally assigns role = USER.
    
    Guarantees:
    - Rejects duplicate email addresses with DuplicateEmailError.
    - Hashes password securely via salted bcrypt.
    - Assigns role = UserRole.USER (client input cannot elevate privileges).
    """
    clean_email = reg_in.email.lower().strip()
    existing = get_moderator_by_email(db, clean_email)
    if existing:
        raise DuplicateEmailError("An account with this email address already exists.")

    # Generate a unique username based on email prefix
    base_username = clean_email.split("@")[0]
    username = base_username
    counter = 1
    while get_moderator_by_username(db, username):
        username = f"{base_username}_{counter}"
        counter += 1

    user = Moderator(
        name=reg_in.name.strip(),
        email=clean_email,
        username=username,
        hashed_password=get_password_hash(reg_in.password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_moderator(db: Session, moderator_in: ModeratorCreate) -> Moderator:
    """Register a new moderator (for testing/setup)."""
    moderator = Moderator(
        name=moderator_in.username,
        email=moderator_in.email.lower().strip(),
        username=moderator_in.username.strip(),
        hashed_password=get_password_hash(moderator_in.password),
        role=UserRole.MODERATOR,
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
    """Verify credentials for user/moderator/admin login.

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
        raise InactiveModeratorError("Account is inactive.")

    return moderator


def list_users(
    db: Session,
    search: Optional[str] = None,
    role_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Moderator]:
    """Retrieve users with optional search and role filtering for admin management."""
    query = db.query(Moderator)

    if role_filter and role_filter.upper() != "ALL":
        query = query.filter(Moderator.role == role_filter.upper())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Moderator.name.ilike(term),
                Moderator.email.ilike(term),
                Moderator.username.ilike(term),
            )
        )

    return query.order_by(Moderator.created_at.desc()).offset(skip).limit(limit).all()


def update_user_role(
    db: Session,
    user: Moderator,
    new_role: UserRole,
) -> Moderator:
    """Update a user's role between USER and MODERATOR.
    
    Guarantees:
    - Protects the primary ADMIN account from accidental downgrade or modification.
    - Prevents promoting users to ADMIN through this endpoint.
    """
    if user.role == UserRole.ADMIN:
        raise AdminProtectedError("The primary administrator account cannot be downgraded or modified.")

    if new_role not in (UserRole.USER, UserRole.MODERATOR):
        raise ValueError("Role can only be changed to USER or MODERATOR.")

    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


def reset_admin_password(db: Session, new_password: str) -> Moderator:
    """Safely reset or initialize the system administrator password.

    Guarantees:
    - Finds the existing ADMIN account.
    - If no user has role ADMIN, checks username 'admin' or email 'admin@whistledrop.org'.
    - If neither exists, creates a fresh admin account.
    - Hashes new password with standard bcrypt (12 rounds).
    - Ensures is_active is True and role is UserRole.ADMIN.
    - Never modifies other users, moderators, reports, or evidence data.
    """
    admin = db.query(Moderator).filter(Moderator.role == UserRole.ADMIN).first()
    if not admin:
        admin = (
            db.query(Moderator)
            .filter(
                or_(
                    Moderator.username == "admin",
                    Moderator.email == "admin@whistledrop.org",
                )
            )
            .first()
        )
        if admin:
            admin.role = UserRole.ADMIN

    if not admin:
        admin = Moderator(
            name="System Administrator",
            email="admin@whistledrop.org",
            username="admin",
            hashed_password=get_password_hash(new_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
    else:
        admin.hashed_password = get_password_hash(new_password)
        admin.is_active = True
        admin.role = UserRole.ADMIN

    db.commit()
    db.refresh(admin)
    return admin

