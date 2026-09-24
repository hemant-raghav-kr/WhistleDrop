"""Admin endpoints for user and role management."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.moderator import Moderator
from app.schemas.admin import UserAdminRead, UserRoleUpdate
from app.services.auth_service import (
    AdminProtectedError,
    get_moderator_by_id,
    list_users,
    update_user_role,
)

router = APIRouter()


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
