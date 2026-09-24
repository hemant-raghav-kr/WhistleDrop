"""Authentication and registration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_authenticated_user
from app.core.security import create_access_token
from app.models.moderator import Moderator
from app.schemas.auth import LoginRequest, RegisterRequest, Token, UserRead
from app.services.auth_service import (
    DuplicateEmailError,
    InactiveModeratorError,
    InvalidCredentialsError,
    authenticate_moderator,
    register_user,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Register a new user account. Every new registration unconditionally receives role = USER. "
        "Client cannot elevate privileges. Returns 409 Conflict if the email address is already in use."
    ),
    responses={
        201: {"description": "User account created successfully (role = USER)"},
        409: {"description": "Email address already registered"},
        422: {"description": "Validation error (invalid email, password mismatch, short password)"},
    },
)
def register(
    reg_data: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserRead:
    """Register a new user account with default USER role."""
    try:
        user = register_user(db=db, reg_in=reg_data)
        return UserRead.model_validate(user)
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User/Moderator/Admin authentication",
    description=(
        "Authenticate credentials and receive a signed JWT bearer token with role metadata. "
        "Returns 401 for invalid credentials and 403 for inactive accounts."
    ),
    responses={
        200: {"description": "Authentication successful; JWT bearer token issued"},
        401: {"description": "Invalid username/email or password"},
        403: {"description": "Account is inactive or disabled"},
        422: {"description": "Validation error in login request format"},
    },
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate account and issue JWT bearer token."""
    try:
        user = authenticate_moderator(
            db=db,
            username_or_email=login_data.username_or_email,
            password=login_data.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveModeratorError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive moderator account",
        )

    access_token = create_access_token(subject=str(user.id))
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        name=user.name,
        email=user.email,
    )


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the profile and live database role of the currently authenticated user.",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Unauthorized; missing or invalid token"},
        403: {"description": "Account is inactive"},
    },
)
def get_current_user_profile(
    current_user: Moderator = Depends(require_authenticated_user),
) -> UserRead:
    """Return the profile and live role of the authenticated user."""
    return UserRead.model_validate(current_user)
