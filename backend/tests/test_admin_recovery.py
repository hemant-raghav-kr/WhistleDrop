"""Automated tests for temporary production admin recovery mechanism."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.endpoints.admin import _reset_recovery_state
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.moderator import Moderator, UserRole
from app.models.report import Report, ReportCategory, ReportStatus


VALID_TEST_SECRET = "super-secret-recovery-token-for-admin-test-12345"


@pytest.fixture(autouse=True)
def clean_recovery_state():
    """Ensure in-memory lockout and counter are clean before and after every test."""
    _reset_recovery_state()
    original_secret = settings.ADMIN_RECOVERY_SECRET
    yield
    _reset_recovery_state()
    settings.ADMIN_RECOVERY_SECRET = original_secret


def test_recovery_disabled_when_secret_unset(client: TestClient):
    """Test 1: When ADMIN_RECOVERY_SECRET is None or empty, returns 404."""
    settings.ADMIN_RECOVERY_SECRET = None
    res = client.post(
        "/api/v1/admin/recovery/reset-password",
        json={"recovery_secret": "any-secret", "new_password": "NewAdminPassword123!"},
    )
    assert res.status_code == 404
    assert "disabled" in res.json()["detail"].lower()

    settings.ADMIN_RECOVERY_SECRET = ""
    res = client.post(
        "/api/v1/admin/recovery/reset-password",
        json={"recovery_secret": "any-secret", "new_password": "NewAdminPassword123!"},
    )
    assert res.status_code == 404


def test_recovery_disabled_when_secret_trivial_or_short(client: TestClient):
    """Test 2: When ADMIN_RECOVERY_SECRET is too short (<16 chars) or a placeholder, returns 404."""
    for weak_secret in ["placeholder", "changeme", "default", "none", "secret", "short-key-123"]:
        settings.ADMIN_RECOVERY_SECRET = weak_secret
        res = client.post(
            "/api/v1/admin/recovery/reset-password",
            json={"recovery_secret": weak_secret, "new_password": "NewAdminPassword123!"},
        )
        assert res.status_code == 404
        assert "disabled" in res.json()["detail"].lower()


def test_recovery_rejects_invalid_secret(client: TestClient):
    """Test 3: Valid configured secret returns 401 when invalid secret is supplied."""
    settings.ADMIN_RECOVERY_SECRET = VALID_TEST_SECRET

    res = client.post(
        "/api/v1/admin/recovery/reset-password",
        json={"recovery_secret": "wrong-secret-token-attempt", "new_password": "NewAdminPassword123!"},
    )
    assert res.status_code == 401
    assert "Invalid recovery secret" in res.json()["detail"]


def test_recovery_brute_force_lockout(client: TestClient):
    """Test 4: 5 consecutive failed attempts trigger 429 Too Many Requests lockout."""
    settings.ADMIN_RECOVERY_SECRET = VALID_TEST_SECRET

    # First 5 attempts return 401
    for _ in range(5):
        res = client.post(
            "/api/v1/admin/recovery/reset-password",
            json={"recovery_secret": "wrong-secret", "new_password": "NewAdminPassword123!"},
        )
        assert res.status_code == 401

    # 6th attempt is locked out with 429
    res_lockout = client.post(
        "/api/v1/admin/recovery/reset-password",
        json={"recovery_secret": VALID_TEST_SECRET, "new_password": "NewAdminPassword123!"},
    )
    assert res_lockout.status_code == 429
    assert "Too many failed recovery attempts" in res_lockout.json()["detail"]


def test_recovery_rejects_short_password(client: TestClient):
    """Test 5: Password validation enforces minimum length (8 chars)."""
    settings.ADMIN_RECOVERY_SECRET = VALID_TEST_SECRET

    res = client.post(
        "/api/v1/admin/recovery/reset-password",
        json={"recovery_secret": VALID_TEST_SECRET, "new_password": "short"},
    )
    assert res.status_code == 422


def test_recovery_resets_existing_admin_via_header(client: TestClient, db: Session):
    """Test 6: Valid secret in X-Recovery-Secret header successfully resets admin password."""
    settings.ADMIN_RECOVERY_SECRET = VALID_TEST_SECRET

    # Create initial admin with old password
    admin = Moderator(
        name="System Administrator",
        email="admin@whistledrop.org",
        username="admin",
        hashed_password=get_password_hash("OldPassword123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()

    # Reset password via header
    res = client.post(
        "/api/v1/admin/recovery/reset-password",
        headers={"X-Recovery-Secret": VALID_TEST_SECRET},
        json={"new_password": "BrandNewAdminPassword2026!"},
    )
    assert res.status_code == 200
    assert res.json() == {
        "status": "success",
        "detail": "Admin password has been reset successfully.",
    }

    # Verify old password fails login
    old_login = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin", "password": "OldPassword123!"},
    )
    assert old_login.status_code == 401

    # Verify new password succeeds login
    new_login = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin", "password": "BrandNewAdminPassword2026!"},
    )
    assert new_login.status_code == 200
    token_data = new_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_recovery_resets_existing_admin_via_body(client: TestClient, db: Session):
    """Test 7: Valid secret in JSON payload successfully resets admin password."""
    settings.ADMIN_RECOVERY_SECRET = VALID_TEST_SECRET

    admin = Moderator(
        name="System Administrator",
        email="admin@whistledrop.org",
        username="admin",
        hashed_password=get_password_hash("InitialOldPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()

    res = client.post(
        "/api/v1/admin/recovery/reset-password",
        json={
            "recovery_secret": VALID_TEST_SECRET,
            "new_password": "NewSecretViaBodyPassword2026!",
        },
    )
    assert res.status_code == 200

    login_res = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin", "password": "NewSecretViaBodyPassword2026!"},
    )
    assert login_res.status_code == 200


def test_recovery_preserves_other_data(client: TestClient, db: Session):
    """Test 8: Recovery strictly preserves all other reports, users, and moderators."""
    settings.ADMIN_RECOVERY_SECRET = VALID_TEST_SECRET

    # Create admin
    admin = Moderator(
        name="System Administrator",
        email="admin@whistledrop.org",
        username="admin",
        hashed_password=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    # Create colleague moderator
    mod = Moderator(
        name="Colleague Mod",
        email="colleague@whistledrop.org",
        username="colleague_mod",
        hashed_password=get_password_hash("ColleaguePass123!"),
        role=UserRole.MODERATOR,
        is_active=True,
    )
    # Create regular user
    user = Moderator(
        name="Regular User",
        email="user@whistledrop.org",
        username="reg_user",
        hashed_password=get_password_hash("UserPass123!"),
        role=UserRole.USER,
        is_active=True,
    )
    # Create report
    report = Report(
        case_code_hash="testcasehash12345",
        category=ReportCategory.CORRUPTION,
        description="Important confidential report that must not be deleted.",
        status=ReportStatus.SUBMITTED,
    )
    db.add_all([admin, mod, user, report])
    db.commit()

    report_id = report.id
    mod_id = mod.id
    user_id = user.id

    # Execute admin password recovery
    res = client.post(
        "/api/v1/admin/recovery/reset-password",
        json={
            "recovery_secret": VALID_TEST_SECRET,
            "new_password": "FreshAdminRecoveryPassword2026!",
        },
    )
    assert res.status_code == 200

    # Verify report is untouched
    db_report = db.query(Report).filter(Report.id == report_id).first()
    assert db_report is not None
    assert db_report.description == "Important confidential report that must not be deleted."
    assert db_report.category == ReportCategory.CORRUPTION

    # Verify colleague moderator is untouched and can still log in
    mod_login = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "colleague_mod", "password": "ColleaguePass123!"},
    )
    assert mod_login.status_code == 200

    # Verify user is untouched
    db_user = db.query(Moderator).filter(Moderator.id == user_id).first()
    assert db_user is not None
    assert db_user.role == UserRole.USER


def test_recovery_initializes_admin_if_missing(client: TestClient, db: Session):
    """Test 9: If no admin exists in the database, recovery creates one."""
    settings.ADMIN_RECOVERY_SECRET = VALID_TEST_SECRET

    # Clear any existing moderators
    db.query(Moderator).delete()
    db.commit()

    res = client.post(
        "/api/v1/admin/recovery/reset-password",
        json={
            "recovery_secret": VALID_TEST_SECRET,
            "new_password": "NewlyInitializedAdminPassword2026!",
        },
    )
    assert res.status_code == 200

    # Verify admin was created and can log in
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin", "password": "NewlyInitializedAdminPassword2026!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Verify role is ADMIN
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["role"] == "ADMIN"

