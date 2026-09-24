import enum
from typing import Optional
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    """Authorization roles within WhistleDrop."""
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class Moderator(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authenticated user/staff account supporting USER, MODERATOR, and ADMIN roles."""
    __tablename__ = "moderators"

    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        default=UserRole.USER,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Moderator username={self.username} role={self.role} active={self.is_active}>"
