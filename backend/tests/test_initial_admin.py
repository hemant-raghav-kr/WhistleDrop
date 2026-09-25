"""Automated tests for initial administrator account provisioning."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.moderator import Moderator, UserRole
from scripts.create_initial_admin import create_or_update_admin


def test_create_initial_admin_success(db: Session, client: TestClient):
    """Test creating initial administrator account on empty database."""
    # Ensure no admin exists
    db.query(Moderator).delete()
    db.commit()

    admin = create_or_update_admin(
        db=db,
        email="admin@whistledrop.org",
        username="admin",
        name="System Administrator",
        password="SuperSecureAdminPassword2026!",
    )

    assert admin.id is not None
    assert admin.email == "admin@whistledrop.org"
    assert admin.username == "admin"
    assert admin.role == UserRole.ADMIN
    assert admin.is_active is True
    assert verify_password("SuperSecureAdminPassword2026!", admin.hashed_password) is True

    # Test login endpoint with newly provisioned admin
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin", "password": "SuperSecureAdminPassword2026!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert token_data["role"] == "ADMIN"
    assert "access_token" in token_data


def test_create_initial_admin_updates_existing(db: Session):
    """Test re-running provisioning updates password and guarantees role=ADMIN."""
    admin1 = create_or_update_admin(
        db=db,
        email="admin@whistledrop.org",
        username="admin",
        name="System Administrator",
        password="InitialPassword123!",
    )
    admin_id = admin1.id

    # Re-run with updated password
    admin2 = create_or_update_admin(
        db=db,
        email="admin@whistledrop.org",
        username="admin",
        name="System Administrator Updated",
        password="NewAdminPassword456!",
    )

    assert admin2.id == admin_id
    assert admin2.name == "System Administrator Updated"
    assert verify_password("NewAdminPassword456!", admin2.hashed_password) is True
    assert verify_password("InitialPassword123!", admin2.hashed_password) is False


def test_create_initial_admin_rejects_short_password(db: Session):
    """Test that password under 8 characters raises ValueError."""
    with pytest.raises(ValueError, match="at least 8 characters"):
        create_or_update_admin(
            db=db,
            email="admin@whistledrop.org",
            username="admin",
            name="System Administrator",
            password="short",
        )
