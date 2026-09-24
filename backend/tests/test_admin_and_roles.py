"""Automated tests for Admin User Management, Registration, Multi-Role Authorization,
Search, and Permanent Case Closure.
"""

import io
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, get_password_hash
from app.models.moderator import Moderator, UserRole
from app.models.report import Report, ReportCategory, ReportStatus


@pytest.fixture
def admin_user(db) -> Moderator:
    """Fixture creating a primary ADMIN user."""
    admin = Moderator(
        name="System Administrator",
        email="admin@whistledrop.org",
        username="admin",
        hashed_password=get_password_hash("AdminPassword123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def moderator_user(db) -> Moderator:
    """Fixture creating a MODERATOR user."""
    mod = Moderator(
        name="Staff Moderator",
        email="mod@whistledrop.org",
        username="staff_mod",
        hashed_password=get_password_hash("ModPassword123!"),
        role=UserRole.MODERATOR,
        is_active=True,
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)
    return mod


@pytest.fixture
def regular_user(db) -> Moderator:
    """Fixture creating a normal USER."""
    user = Moderator(
        name="Normal User",
        email="user@whistledrop.org",
        username="normal_user",
        hashed_password=get_password_hash("UserPassword123!"),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user: Moderator) -> dict:
    token = create_access_token(subject=str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def moderator_headers(moderator_user: Moderator) -> dict:
    token = create_access_token(subject=str(moderator_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(regular_user: Moderator) -> dict:
    token = create_access_token(subject=str(regular_user.id))
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. REGISTRATION TESTS
# ==============================================================================

def test_1_valid_registration_creates_user(client: TestClient):
    """Scenario 1: Valid registration creates an account with default role USER."""
    payload = {
        "name": "Alice Reporter",
        "email": "alice@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "alice@example.com"
    assert data["name"] == "Alice Reporter"
    assert data["role"] == "USER"
    assert "hashed_password" not in data
    assert "password" not in data


def test_2_registration_rejects_duplicate_email(client: TestClient):
    """Scenario 2: Registering an existing email returns 409 Conflict."""
    payload = {
        "name": "Bob Test",
        "email": "bob@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_3_registration_rejects_invalid_email(client: TestClient):
    """Scenario 3: Invalid email format returns 422 Unprocessable Entity."""
    payload = {
        "name": "Invalid Email",
        "email": "not-an-email",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 422


def test_4_registration_rejects_password_mismatch(client: TestClient):
    """Scenario 4: Mismatched password and confirm_password returns 422."""
    payload = {
        "name": "Mismatch Test",
        "email": "mismatch@example.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword456!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 422
    assert "Passwords do not match" in str(res.json())


def test_5_registration_rejects_short_password(client: TestClient):
    """Scenario 5: Password under 8 characters returns 422."""
    payload = {
        "name": "Short Pass",
        "email": "short@example.com",
        "password": "short",
        "confirm_password": "short",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 422


def test_6_registration_privilege_escalation_impossible(client: TestClient):
    """Scenario 6: Attempting to send role: ADMIN or role: MODERATOR still creates USER."""
    payload_admin = {
        "name": "Attacker Admin",
        "email": "attacker1@example.com",
        "password": "AttackPassword123!",
        "confirm_password": "AttackPassword123!",
        "role": "ADMIN",
    }
    res1 = client.post("/api/v1/auth/register", json=payload_admin)
    assert res1.status_code == 201
    assert res1.json()["role"] == "USER"

    payload_mod = {
        "name": "Attacker Mod",
        "email": "attacker2@example.com",
        "password": "AttackPassword123!",
        "confirm_password": "AttackPassword123!",
        "role": "MODERATOR",
    }
    res2 = client.post("/api/v1/auth/register", json=payload_mod)
    assert res2.status_code == 201
    assert res2.json()["role"] == "USER"


# ==============================================================================
# 2. AUTHORIZATION MATRIX TESTS
# ==============================================================================

def test_7_anonymous_cannot_access_admin_or_moderator(client: TestClient):
    """Scenario 7: Unauthenticated calls to protected endpoints return 401."""
    res_admin = client.get("/api/v1/admin/users")
    assert res_admin.status_code == 401

    res_mod = client.get("/api/v1/moderator/reports")
    assert res_mod.status_code == 401


def test_8_user_cannot_access_admin_or_moderator(client: TestClient, user_headers: dict):
    """Scenario 8: Normal USER receives 403 on admin and moderator endpoints."""
    res_admin = client.get("/api/v1/admin/users", headers=user_headers)
    assert res_admin.status_code == 403

    res_mod = client.get("/api/v1/moderator/reports", headers=user_headers)
    assert res_mod.status_code == 403


def test_9_moderator_cannot_access_admin(client: TestClient, moderator_headers: dict):
    """Scenario 9: MODERATOR receives 403 on admin endpoint, but 200 on moderator endpoint."""
    res_admin = client.get("/api/v1/admin/users", headers=moderator_headers)
    assert res_admin.status_code == 403

    res_mod = client.get("/api/v1/moderator/reports", headers=moderator_headers)
    assert res_mod.status_code == 200


def test_10_admin_can_access_both_endpoints(client: TestClient, admin_headers: dict):
    """Scenario 10: ADMIN can access both admin and moderator endpoints."""
    res_admin = client.get("/api/v1/admin/users", headers=admin_headers)
    assert res_admin.status_code == 200

    res_mod = client.get("/api/v1/moderator/reports", headers=admin_headers)
    assert res_mod.status_code == 200


# ==============================================================================
# 3. ADMIN ROLE MANAGEMENT & REVOCATION FLOW
# ==============================================================================

def test_11_admin_grants_and_revokes_moderator(
    client: TestClient,
    admin_headers: dict,
    regular_user: Moderator,
):
    """Scenario 11: ADMIN promotes USER to MODERATOR, and then demotes back to USER."""
    user_id = str(regular_user.id)
    user_token = create_access_token(subject=user_id)
    user_auth = {"Authorization": f"Bearer {user_token}"}

    # Step A: User cannot access moderator queue
    assert client.get("/api/v1/moderator/reports", headers=user_auth).status_code == 403

    # Step B: Admin grants MODERATOR
    grant_res = client.patch(
        f"/api/v1/admin/users/{user_id}/role",
        headers=admin_headers,
        json={"role": "MODERATOR"},
    )
    assert grant_res.status_code == 200
    assert grant_res.json()["role"] == "MODERATOR"

    # Step C: User now immediately gets 200 on moderator queue
    assert client.get("/api/v1/moderator/reports", headers=user_auth).status_code == 200

    # Step D: Admin revokes MODERATOR
    revoke_res = client.patch(
        f"/api/v1/admin/users/{user_id}/role",
        headers=admin_headers,
        json={"role": "USER"},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["role"] == "USER"

    # Step E: User immediately loses access (403)
    assert client.get("/api/v1/moderator/reports", headers=user_auth).status_code == 403


def test_12_admin_account_is_protected_from_downgrade(
    client: TestClient,
    admin_headers: dict,
    admin_user: Moderator,
):
    """Scenario 12: Attempting to downgrade the primary ADMIN returns 400 Bad Request."""
    admin_id = str(admin_user.id)
    res = client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        headers=admin_headers,
        json={"role": "USER"},
    )
    assert res.status_code == 400
    assert "cannot be downgraded" in res.json()["detail"]


def test_13_moderator_cannot_grant_or_revoke_roles(
    client: TestClient,
    moderator_headers: dict,
    regular_user: Moderator,
):
    """Scenario 13: MODERATOR cannot call PATCH /admin/users/{id}/role (403)."""
    user_id = str(regular_user.id)
    res = client.patch(
        f"/api/v1/admin/users/{user_id}/role",
        headers=moderator_headers,
        json={"role": "MODERATOR"},
    )
    assert res.status_code == 403


def test_14_admin_user_role_invalid_targets(client: TestClient, admin_headers: dict):
    """Scenario 14: Nonexistent user returns 404; malformed UUID returns 422."""
    fake_id = str(uuid.uuid4())
    res_404 = client.patch(
        f"/api/v1/admin/users/{fake_id}/role",
        headers=admin_headers,
        json={"role": "MODERATOR"},
    )
    assert res_404.status_code == 404

    res_422 = client.patch(
        "/api/v1/admin/users/not-a-valid-uuid/role",
        headers=admin_headers,
        json={"role": "MODERATOR"},
    )
    assert res_422.status_code == 422


# ==============================================================================
# 4. ADMIN USER SEARCH & FILTERING
# ==============================================================================

def test_15_admin_users_search_and_role_filters(
    client: TestClient,
    admin_headers: dict,
    admin_user: Moderator,
    moderator_user: Moderator,
    regular_user: Moderator,
):
    """Scenario 15: Admin users list supports keyword search and role filtering."""
    # List all
    res_all = client.get("/api/v1/admin/users", headers=admin_headers)
    assert res_all.status_code == 200
    assert len(res_all.json()) >= 3

    # Filter by role
    res_mods = client.get("/api/v1/admin/users?role=MODERATOR", headers=admin_headers)
    assert res_mods.status_code == 200
    for u in res_mods.json():
        assert u["role"] == "MODERATOR"

    # Search by keyword
    res_search = client.get("/api/v1/admin/users?search=normal_user", headers=admin_headers)
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["email"] == regular_user.email


# ==============================================================================
# 5. PERMANENT CASE CLOSURE & SEARCH
# ==============================================================================

def test_16_permanent_case_closure(client: TestClient, moderator_headers: dict):
    """Scenario 16: Moderator permanently closes case; further transitions rejected."""
    # 1. Submit report anonymously
    sub_res = client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Case to be permanently closed."},
    )
    assert sub_res.status_code == 201
    case_code = sub_res.json()["case_code"]

    # 2. Get report ID from queue
    q_res = client.get("/api/v1/moderator/reports", headers=moderator_headers)
    report = [r for r in q_res.json() if "Case to be permanently closed." in r["description"]][0]
    report_id = report["id"]

    # 3. Permanently close case
    close_res = client.post(f"/api/v1/moderator/reports/{report_id}/close", headers=moderator_headers)
    assert close_res.status_code == 200
    assert close_res.json()["is_closed"] is True

    # 4. Attempting further transition returns 400
    trans_res = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=moderator_headers,
        json={"status": "UNDER_REVIEW", "message": "Trying to reopen"},
    )
    assert trans_res.status_code == 400
    assert "permanently closed" in trans_res.json()["detail"]

    # 5. Public case tracking shows closed status
    track_res = client.get(f"/api/v1/reports/{case_code}")
    assert track_res.status_code == 200
    assert track_res.json()["is_closed"] is True


def test_17_moderator_report_search(client: TestClient, moderator_headers: dict):
    """Scenario 17: Moderator search filter matches keywords in report description."""
    client.post(
        "/api/v1/reports",
        json={"category": "TECHNICAL", "description": "Database outage on replica cluster-04."},
    )
    client.post(
        "/api/v1/reports",
        json={"category": "HARASSMENT", "description": "Unrelated incident in hallway."},
    )

    res = client.get("/api/v1/moderator/reports?search=replica", headers=moderator_headers)
    assert res.status_code == 200
    results = res.json()
    assert len(results) >= 1
    assert any("cluster-04" in r["description"] for r in results)


def test_18_auth_me_endpoint_returns_live_role(
    client: TestClient,
    admin_headers: dict,
    moderator_headers: dict,
    user_headers: dict,
):
    """Scenario 18: /api/v1/auth/me returns the correct live profile and role."""
    r_admin = client.get("/api/v1/auth/me", headers=admin_headers)
    assert r_admin.status_code == 200
    assert r_admin.json()["role"] == "ADMIN"

    r_mod = client.get("/api/v1/auth/me", headers=moderator_headers)
    assert r_mod.status_code == 200
    assert r_mod.json()["role"] == "MODERATOR"

    r_user = client.get("/api/v1/auth/me", headers=user_headers)
    assert r_user.status_code == 200
    assert r_user.json()["role"] == "USER"
