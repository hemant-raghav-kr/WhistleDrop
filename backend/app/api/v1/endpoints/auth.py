"""Authentication endpoints for staff moderators."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, Token
from app.services.auth_service import (
    InactiveModeratorError,
    InvalidCredentialsError,
    authenticate_moderator,
)

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Moderator authentication",
    description=(
        "Authenticate staff moderator credentials and receive a signed JWT bearer token. "
        "Returns 401 for invalid credentials and 403 for inactive moderator accounts."
    ),
    responses={
        200: {"description": "Authentication successful; JWT bearer token issued"},
        401: {"description": "Invalid username/email or password"},
        403: {"description": "Moderator account is inactive or disabled"},
        422: {"description": "Validation error in login request format"},
    },
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate moderator and issue JWT bearer token."""
    try:
        moderator = authenticate_moderator(
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

    access_token = create_access_token(subject=str(moderator.id))
    return Token(access_token=access_token, token_type="bearer")
