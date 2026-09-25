"""Admin endpoints for user and role management."""

import hmac
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.core.config import settings
from app.models.moderator import Moderator
from app.schemas.admin import (
    AdminRecoveryResetRequest,
    AdminRecoveryResetResponse,
    UserAdminRead,
    UserRoleUpdate,
)
from app.services.auth_service import (
    AdminProtectedError,
    get_moderator_by_id,
    list_users,
    reset_admin_password,
    update_user_role,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory tracking for recovery brute-force protection
_recovery_state: Dict[str, Any] = {
    "failed_attempts": 0,
    "lockout_until": None,
}


def _reset_recovery_state() -> None:
    """Helper for testing: reset attempt counter and lockout."""
    _recovery_state["failed_attempts"] = 0
    _recovery_state["lockout_until"] = None



@router.get(
    "/users",
    response_model=List[UserAdminRead],
    status_code=status.HTTP_200_OK,
    summary="List all registered accounts (Admin Only)",
    description=(
        "Retrieve all registered users and staff accounts with optional search and role filtering. "
        "Strictly accessible only to authenticated users with ADMIN role. "
        "Anonymous returns 401; USER or MODERATOR returns 403."
    ),
    responses={
        200: {"description": "List of accounts retrieved successfully"},
        401: {"description": "Unauthorized; missing or invalid token"},
        403: {"description": "Forbidden; non-admin account"},
    },
)
def get_users_list(
    search: Optional[str] = Query(None, description="Search term matching name, email, or username"),
    role: Optional[str] = Query(None, description="Filter by role (ALL, USER, MODERATOR, ADMIN)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
    admin: Moderator = Depends(require_admin),
) -> List[UserAdminRead]:
    """List users for admin management."""
    users = list_users(
        db=db,
        search=search,
        role_filter=role,
        skip=skip,
        limit=limit,
    )
    return [UserAdminRead.model_validate(u) for u in users]


@router.patch(
    "/users/{user_id}/role",
    response_model=UserAdminRead,
    status_code=status.HTTP_200_OK,
    summary="Update a user's role: Grant or Revoke Moderator (Admin Only)",
    description=(
        "Change a user's role to MODERATOR (Grant) or USER (Revoke). "
        "Strictly accessible only to ADMIN. "
        "The primary ADMIN account is protected and cannot be downgraded. "
        "Returns 400 if attempting to modify ADMIN, 404 if user not found, 422 if UUID malformed."
    ),
    responses={
        200: {"description": "Role updated successfully"},
        400: {"description": "Cannot downgrade protected admin or invalid role"},
        401: {"description": "Unauthorized; missing or invalid token"},
        403: {"description": "Forbidden; non-admin caller"},
        404: {"description": "User account not found"},
        422: {"description": "Malformed user UUID"},
    },
)
def change_user_role(
    user_id: uuid.UUID,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: Moderator = Depends(require_admin),
) -> UserAdminRead:
    """Grant or revoke moderator role for a user account."""
    target_user = get_moderator_by_id(db, moderator_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found with the specified ID.",
        )

    try:
        updated_user = update_user_role(
            db=db,
            user=target_user,
            new_role=role_update.role,
        )
        return UserAdminRead.model_validate(updated_user)
    except AdminProtectedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/recovery/reset-password",
    response_model=AdminRecoveryResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Temporary emergency admin password reset (Recovery Secret Required)",
    description=(
        "Emergency recovery endpoint to reset the system administrator password without shell access. "
        "Requires a strong one-time recovery secret configured in server environment (ADMIN_RECOVERY_SECRET). "
        "Returns 404 when disabled or unconfigured. Rate limited with cooldown on repeated failures."
    ),
    responses={
        200: {"description": "Admin password successfully reset"},
        401: {"description": "Invalid recovery secret"},
        404: {"description": "Recovery endpoint disabled"},
        422: {"description": "Validation error (e.g. password too short)"},
        429: {"description": "Too many failed recovery attempts; temporarily locked"},
    },
)
def recovery_reset_admin_password(
    body: AdminRecoveryResetRequest,
    db: Session = Depends(get_db),
    x_recovery_secret: Optional[str] = Header(None, alias="X-Recovery-Secret"),
) -> AdminRecoveryResetResponse:
    """Emergency reset endpoint for administrator account."""
    configured_secret = (settings.ADMIN_RECOVERY_SECRET or "").strip()
    disallowed_secrets = {"", "placeholder", "changeme", "default", "none", "secret", "admin"}

    # 1. Verification: Disabled if secret is unset, too short (<16 chars), or placeholder
    if not configured_secret or len(configured_secret) < 16 or configured_secret.lower() in disallowed_secrets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin recovery service is disabled.",
        )

    # 2. Safety: Lockout check on repeated failures
    now = datetime.now(timezone.utc)
    if _recovery_state["lockout_until"] and now < _recovery_state["lockout_until"]:
        remaining = int((_recovery_state["lockout_until"] - now).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed recovery attempts. Locked out for {remaining} seconds.",
        )

    # 3. Extract candidate secret from header or request body
    provided_secret = (x_recovery_secret or body.recovery_secret or "").strip()

    # 4. Constant-time secret comparison
    is_valid = bool(provided_secret) and hmac.compare_digest(
        provided_secret.encode("utf-8"),
        configured_secret.encode("utf-8"),
    )

    if not is_valid:
        _recovery_state["failed_attempts"] += 1
        if _recovery_state["failed_attempts"] >= 5:
            _recovery_state["lockout_until"] = now + timedelta(minutes=15)
            logger.warning("Admin recovery locked out for 15 minutes due to 5 consecutive failed attempts.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid recovery secret.",
        )

    # 5. Success: reset lockout state and update password
    _recovery_state["failed_attempts"] = 0
    _recovery_state["lockout_until"] = None

    reset_admin_password(db=db, new_password=body.new_password)
    logger.warning("Admin account password was successfully reset via verified recovery secret.")

    return AdminRecoveryResetResponse(
        status="success",
        detail="Admin password has been reset successfully.",
    )



