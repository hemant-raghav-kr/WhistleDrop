"""Exhaustive tests for WhistleDrop backend hardening, validation, security, and state machine."""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.moderator import Moderator
from app.models.report import ReportCategory, ReportStatus


# ==============================================================================
# 1. ANONYMOUS REPORTING TESTS
# ==============================================================================

def test_report_submission_all_supported_categories(client: TestClient):
    """Verify submission succeeds for every supported category and normalizes case."""
    categories = ["SECURITY", "HARASSMENT", "CORRUPTION", "TECHNICAL", "OTHER"]
    for cat in categories:
        res = client.post(
            "/api/v1/reports",
            json={
                "category": cat,
                "description": f"Valid report description for category {cat}.",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["category"] == cat
        assert data["status"] == "SUBMITTED"
        assert "case_code" in data
        assert "id" not in data
        assert "case_code_hash" not in data


def test_report_submission_case_insensitive_category(client: TestClient):
    """Verify category input is normalized (e.g. 'Technical' -> 'TECHNICAL')."""
    res = client.post(
        "/api/v1/reports",
        json={
            "category": "Technical",
            "description": "System architecture diagram leaked onto public pastebin.",
        },
    )
    assert res.status_code == 201
    assert res.json()["category"] == "TECHNICAL"


def test_report_submission_invalid_category(client: TestClient):
    """Verify unsupported categories are rejected with 422."""
    res = client.post(
        "/api/v1/reports",
        json={
            "category": "UNSUPPORTED_CATEGORY",
            "description": "Some description that is long enough.",
        },
    )
    assert res.status_code == 422
    assert "error_type" in res.json()
    assert res.json()["error_type"] == "VALIDATION_ERROR"


def test_report_submission_missing_fields(client: TestClient):
    """Verify missing required fields return 422."""
    # Missing category
    res1 = client.post(
        "/api/v1/reports",
        json={"description": "Valid description without category."},
    )
    assert res1.status_code == 422

    # Missing description
    res2 = client.post(
        "/api/v1/reports",
        json={"category": "SECURITY"},
    )
    assert res2.status_code == 422


def test_report_submission_short_or_whitespace_description(client: TestClient):
    """Verify descriptions under 10 non-whitespace characters are rejected with 422."""
    # Too short (< 10 chars)
    res1 = client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Too short"},
    )
    assert res1.status_code == 422

    # Whitespace only
    res2 = client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "            "},
    )
    assert res2.status_code == 422


def test_report_submission_evidence_url_validation(client: TestClient):
    """Verify evidence_url accepts valid http/https URLs and rejects invalid formats."""
    # Valid https
    res1 = client.post(
        "/api/v1/reports",
        json={
            "category": "SECURITY",
            "description": "Valid description with https link.",
            "evidence_url": "https://example.com/proof.pdf",
        },
    )
    assert res1.status_code == 201

    # Valid http
    res2 = client.post(
        "/api/v1/reports",
        json={
            "category": "SECURITY",
            "description": "Valid description with http link.",
            "evidence_url": "http://example.com/evidence",
        },
    )
    assert res2.status_code == 201

    # Invalid non-http scheme (ftp)
    res3 = client.post(
        "/api/v1/reports",
        json={
            "category": "SECURITY",
            "description": "Valid description with invalid ftp link.",
            "evidence_url": "ftp://example.com/bad",
        },
    )
    assert res3.status_code == 422

    # Malformed string
    res4 = client.post(
        "/api/v1/reports",
        json={
            "category": "SECURITY",
            "description": "Valid description with malformed url.",
            "evidence_url": "not-a-valid-url",
        },
    )
    assert res4.status_code == 422


# ==============================================================================
# 2. CASE TRACKING & PRIVACY TESTS
# ==============================================================================

def test_case_tracking_public_view_privacy(client: TestClient):
    """Verify case tracking strictly conceals internal DB UUID, hash, and moderator identity."""
    submit_res = client.post(
        "/api/v1/reports",
        json={
            "category": "HARASSMENT",
            "description": "Incident witnessed in common hall during departmental event.",
        },
    )
    case_code = submit_res.json()["case_code"]

    # Public tracking request
    track_res = client.get(f"/api/v1/reports/{case_code}")
    assert track_res.status_code == 200
    data = track_res.json()

    # Required public fields
    assert data["category"] == "HARASSMENT"
    assert data["status"] == "SUBMITTED"
    assert "submitted_at" in data
    assert "updated_at" in data
    assert "updates" in data
    assert len(data["updates"]) == 1

    # Strict privacy verification
    assert "id" not in data
    assert "case_code_hash" not in data
    assert "moderator" not in data
    assert "moderator_id" not in data
    assert "author" not in data

    # Update items must not leak internal IDs
    for item in data["updates"]:
        assert "id" not in item
        assert "report_id" not in item
        assert "status" in item
        assert "message" in item
        assert "created_at" in item


def test_case_tracking_case_insensitivity(client: TestClient):
    """Verify case tracking works regardless of input letter casing or surrounding whitespace."""
    submit_res = client.post(
        "/api/v1/reports",
        json={
            "category": "OTHER",
            "description": "General facilities neglect in secondary storage area.",
        },
    )
    case_code = submit_res.json()["case_code"]

    # Query with lowercase
    lower_code = case_code.lower()
    res = client.get(f"/api/v1/reports/{lower_code}")
    assert res.status_code == 200
    assert res.json()["status"] == "SUBMITTED"

    # Query with padded whitespace
    spaced_code = f"  {case_code}  "
    res_spaced = client.get(f"/api/v1/reports/{spaced_code}")
    assert res_spaced.status_code == 200


def test_case_tracking_nonexistent_and_invalid(client: TestClient):
    """Verify 404 for invalid, malformed, or nonexistent case codes."""
    res1 = client.get("/api/v1/reports/WD-XXXX-YYYY-ZZZZ-0000")
    assert res1.status_code == 404

    res2 = client.get("/api/v1/reports/totally-bogus-code")
    assert res2.status_code == 404


# ==============================================================================
# 3. MODERATOR AUTHENTICATION TESTS
# ==============================================================================

def test_moderator_auth_success(client: TestClient, test_moderator: Moderator):
    """Verify moderator can authenticate using email or username."""
    # Login via email
    res1 = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": test_moderator.email,
            "password": "SecureTestPassword123!",
        },
    )
    assert res1.status_code == 200
    assert "access_token" in res1.json()

    # Login via username
    res2 = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": test_moderator.username,
            "password": "SecureTestPassword123!",
        },
    )
    assert res2.status_code == 200
    assert "access_token" in res2.json()


def test_moderator_auth_invalid_credentials(client: TestClient, test_moderator: Moderator):
    """Verify 401 Unauthorized for unknown user or wrong password."""
    # Wrong password
    res1 = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": test_moderator.email,
            "password": "WrongPassword999!",
        },
    )
    assert res1.status_code == 401
    assert "Incorrect" in res1.json()["detail"]

    # Unknown user
    res2 = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "nonexistent_mod@whistledrop.org",
            "password": "AnyPassword123!",
        },
    )
    assert res2.status_code == 401


def test_moderator_auth_inactive_account(client: TestClient, inactive_moderator: Moderator):
    """Verify 403 Forbidden when moderator account is deactivated."""
    res = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": inactive_moderator.email,
            "password": "DeactivatedPassword123!",
        },
    )
    assert res.status_code == 403
    assert "Inactive moderator account" in res.json()["detail"]


def test_moderator_protected_endpoints_reject_invalid_tokens(client: TestClient):
    """Verify 401 for missing, tampered, or malformed JWT tokens."""
    # Missing token
    res1 = client.get("/api/v1/moderator/reports")
    assert res1.status_code == 401

    # Malformed header
    res2 = client.get(
        "/api/v1/moderator/reports",
        headers={"Authorization": "Bearer this-is-not-a-valid-jwt"},
    )
    assert res2.status_code == 401

    # Random fake signature token
    fake_token = create_access_token(subject=str(uuid.uuid4())) + "tampered"
    res3 = client.get(
        "/api/v1/moderator/reports",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert res3.status_code == 401


# ==============================================================================
# 4. MODERATOR REPORT MANAGEMENT & FILTERING TESTS
# ==============================================================================

def test_moderator_filtering_status_and_category(client: TestClient, auth_headers: dict):
    """Verify moderator can filter reports by status, category, or both combined."""
    # Seed reports with different categories
    client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Security incident report test."},
    )
    client.post(
        "/api/v1/reports",
        json={"category": "TECHNICAL", "description": "Technical glitch report test."},
    )
    client.post(
        "/api/v1/reports",
        json={"category": "HARASSMENT", "description": "Harassment incident report test."},
    )

    # Filter by category
    res_tech = client.get("/api/v1/moderator/reports?category=TECHNICAL", headers=auth_headers)
    assert res_tech.status_code == 200
    tech_reports = res_tech.json()
    assert all(r["category"] == "TECHNICAL" for r in tech_reports)

    # Filter by status
    res_status = client.get("/api/v1/moderator/reports?status=SUBMITTED", headers=auth_headers)
    assert res_status.status_code == 200
    sub_reports = res_status.json()
    assert all(r["status"] == "SUBMITTED" for r in sub_reports)

    # Combined filter
    res_comb = client.get(
        "/api/v1/moderator/reports?status=SUBMITTED&category=SECURITY",
        headers=auth_headers,
    )
    assert res_comb.status_code == 200
    comb_reports = res_comb.json()
    assert all(r["status"] == "SUBMITTED" and r["category"] == "SECURITY" for r in comb_reports)


def test_moderator_get_report_by_id(client: TestClient, auth_headers: dict):
    """Verify moderator can retrieve individual report by UUID."""
    submit_res = client.post(
        "/api/v1/reports",
        json={"category": "CORRUPTION", "description": "Procurement fraud in laboratory department."},
    )
    # Find ID from moderator list
    list_res = client.get("/api/v1/moderator/reports?category=CORRUPTION", headers=auth_headers)
    report_id = list_res.json()[0]["id"]

    # Get details
    detail_res = client.get(f"/api/v1/moderator/reports/{report_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["id"] == report_id
    assert data["category"] == "CORRUPTION"
    assert "case_code_hash" not in data  # Privacy: hash never exposed to moderator


def test_moderator_get_report_invalid_or_nonexistent_id(client: TestClient, auth_headers: dict):
    """Verify 404 for nonexistent UUID and 422 for malformed UUID."""
    # Nonexistent valid UUID
    nonexistent = str(uuid.uuid4())
    res1 = client.get(f"/api/v1/moderator/reports/{nonexistent}", headers=auth_headers)
    assert res1.status_code == 404

    # Malformed UUID string
    res2 = client.get("/api/v1/moderator/reports/not-a-valid-uuid", headers=auth_headers)
    assert res2.status_code == 422


# ==============================================================================
# 5. STATE MACHINE & LIFECYCLE TRANSITION TESTS
# ==============================================================================

def test_state_machine_valid_branch_resolved(client: TestClient, auth_headers: dict):
    """Verify valid branch: SUBMITTED -> UNDER_REVIEW -> RESOLVED."""
    sub_res = client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Critical firewall misconfiguration test."},
    )
    case_code = sub_res.json()["case_code"]

    list_res = client.get("/api/v1/moderator/reports?category=SECURITY", headers=auth_headers)
    report_id = list_res.json()[0]["id"]

    # SUBMITTED -> UNDER_REVIEW
    t1 = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=auth_headers,
        json={"status": "UNDER_REVIEW", "message": "Triaging report."},
    )
    assert t1.status_code == 200
    assert t1.json()["status"] == "UNDER_REVIEW"

    # UNDER_REVIEW -> RESOLVED
    t2 = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=auth_headers,
        json={"status": "RESOLVED", "message": "Patched firewall rules."},
    )
    assert t2.status_code == 200
    assert t2.json()["status"] == "RESOLVED"

    # Verify public tracking sees both updates
    track = client.get(f"/api/v1/reports/{case_code}")
    assert track.status_code == 200
    assert track.json()["status"] == "RESOLVED"
    assert len(track.json()["updates"]) == 3  # initial + 2 transitions


def test_state_machine_valid_branch_dismissed(client: TestClient, auth_headers: dict):
    """Verify valid branch: SUBMITTED -> UNDER_REVIEW -> DISMISSED."""
    sub_res = client.post(
        "/api/v1/reports",
        json={"category": "OTHER", "description": "Duplicate report submitted in error."},
    )
    case_code = sub_res.json()["case_code"]

    list_res = client.get("/api/v1/moderator/reports?category=OTHER", headers=auth_headers)
    report_id = list_res.json()[0]["id"]

    # SUBMITTED -> UNDER_REVIEW
    t1 = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=auth_headers,
        json={"status": "UNDER_REVIEW", "message": "Checking case veracity."},
    )
    assert t1.status_code == 200

    # UNDER_REVIEW -> DISMISSED
    t2 = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=auth_headers,
        json={"status": "DISMISSED", "message": "Report confirmed duplicate of existing case."},
    )
    assert t2.status_code == 200
    assert t2.json()["status"] == "DISMISSED"


def test_state_machine_invalid_transitions_rejected(client: TestClient, auth_headers: dict):
    """Verify all illegal transitions are rejected with HTTP 400 Bad Request."""
    # 1. Direct jump from SUBMITTED -> RESOLVED (Illegal)
    res1 = client.post(
        "/api/v1/reports",
        json={"category": "TECHNICAL", "description": "Testing illegal direct resolution jump."},
    )
    list1 = client.get("/api/v1/moderator/reports?category=TECHNICAL", headers=auth_headers)
    id1 = list1.json()[0]["id"]

    bad1 = client.patch(
        f"/api/v1/moderator/reports/{id1}/status",
        headers=auth_headers,
        json={"status": "RESOLVED", "message": "Direct resolve attempt."},
    )
    assert bad1.status_code == 400
    assert "Cannot transition from 'SUBMITTED' to 'RESOLVED'" in bad1.json()["detail"]

    # 2. Direct jump from SUBMITTED -> DISMISSED (Illegal)
    bad2 = client.patch(
        f"/api/v1/moderator/reports/{id1}/status",
        headers=auth_headers,
        json={"status": "DISMISSED", "message": "Direct dismiss attempt."},
    )
    assert bad2.status_code == 400
    assert "Cannot transition from 'SUBMITTED' to 'DISMISSED'" in bad2.json()["detail"]

    # 3. Transition to same status SUBMITTED -> SUBMITTED (Illegal)
    bad3 = client.patch(
        f"/api/v1/moderator/reports/{id1}/status",
        headers=auth_headers,
        json={"status": "SUBMITTED", "message": "Redundant transition."},
    )
    assert bad3.status_code == 400
    assert "already in 'SUBMITTED' status" in bad3.json()["detail"]

    # Progress to UNDER_REVIEW
    client.patch(
        f"/api/v1/moderator/reports/{id1}/status",
        headers=auth_headers,
        json={"status": "UNDER_REVIEW", "message": "Legitimate transition."},
    )

    # Progress to RESOLVED
    client.patch(
        f"/api/v1/moderator/reports/{id1}/status",
        headers=auth_headers,
        json={"status": "RESOLVED", "message": "Legitimate resolution."},
    )

    # 4. RESOLVED is terminal -> cannot transition to UNDER_REVIEW or SUBMITTED
    bad4 = client.patch(
        f"/api/v1/moderator/reports/{id1}/status",
        headers=auth_headers,
        json={"status": "UNDER_REVIEW", "message": "Illegal reopen attempt."},
    )
    assert bad4.status_code == 400
    assert "terminal status" in bad4.json()["detail"]

    bad5 = client.patch(
        f"/api/v1/moderator/reports/{id1}/status",
        headers=auth_headers,
        json={"status": "SUBMITTED", "message": "Illegal resubmit attempt."},
    )
    assert bad5.status_code == 400
    assert "terminal status" in bad5.json()["detail"]


def test_status_update_empty_message_rejected(client: TestClient, auth_headers: dict):
    """Verify empty or whitespace-only update messages are rejected with 422."""
    sub_res = client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Testing empty message validation."},
    )
    list_res = client.get("/api/v1/moderator/reports?category=SECURITY", headers=auth_headers)
    report_id = list_res.json()[0]["id"]

    # Whitespace message
    bad = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=auth_headers,
        json={"status": "UNDER_REVIEW", "message": "    "},
    )
    assert bad.status_code == 422


def test_moderator_report_uuid_and_auth_matrix(client: TestClient, auth_headers: dict):
    """Verify exact HTTP response codes for authentication and UUID validation:
    - missing JWT -> 401
    - invalid JWT -> 401
    - valid JWT + malformed UUID -> 422
    - valid JWT + valid nonexistent UUID -> 404
    - valid JWT + valid existing UUID -> 200
    """
    # 1. Create a valid report to get a valid existing UUID
    create_res = client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Testing UUID validation matrix."},
    )
    assert create_res.status_code == 201
    list_res = client.get("/api/v1/moderator/reports", headers=auth_headers)
    existing_id = list_res.json()[0]["id"]

    # Case 1: Missing JWT -> 401
    res_no_jwt = client.get(f"/api/v1/moderator/reports/{existing_id}")
    assert res_no_jwt.status_code == 401

    # Case 2: Invalid JWT -> 401
    res_bad_jwt = client.get(
        f"/api/v1/moderator/reports/{existing_id}",
        headers={"Authorization": "Bearer invalid_garbage_token"},
    )
    assert res_bad_jwt.status_code == 401

    # Case 3: Valid JWT + malformed UUID string -> 422
    res_malformed_uuid = client.get(
        "/api/v1/moderator/reports/not-a-valid-uuid",
        headers=auth_headers,
    )
    assert res_malformed_uuid.status_code == 422
    err_body = res_malformed_uuid.json()
    assert err_body["error_type"] == "VALIDATION_ERROR"

    # Case 4: Valid JWT + valid syntax UUID that does not exist in DB -> 404
    nonexistent_uuid = "00000000-0000-0000-0000-000000000000"
    res_nonexistent = client.get(
        f"/api/v1/moderator/reports/{nonexistent_uuid}",
        headers=auth_headers,
    )
    assert res_nonexistent.status_code == 404
    assert f"Report with ID '{nonexistent_uuid}' not found." in res_nonexistent.json()["detail"]

    # Case 5: Valid JWT + valid existing UUID -> 200
    res_existing = client.get(
        f"/api/v1/moderator/reports/{existing_id}",
        headers=auth_headers,
    )
    assert res_existing.status_code == 200
    assert res_existing.json()["id"] == existing_id
