"""API foundation, security constraints, and lifecycle transition tests."""

from fastapi.testclient import TestClient

from app.models.moderator import Moderator


def test_root_and_health(client: TestClient):
    """Test health check and service metadata endpoints."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "healthy"}


def test_openapi_schema_generated(client: TestClient):
    """Test OpenAPI schema availability and title."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/reports" in schema["paths"]
    assert "/api/v1/reports/{case_code}" in schema["paths"]
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/moderator/reports" in schema["paths"]


def test_submit_report_privacy_guarantee(client: TestClient):
    """Verify report submission succeeds and NEVER returns database internal IDs."""
    payload = {
        "category": "SECURITY",
        "description": "Observed significant electrical and physical hazards in building block B lab.",
        "evidence_url": "https://example.org/photo-evidence.jpg",
    }
    response = client.post("/api/v1/reports", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Must contain case code
    assert "case_code" in data
    assert data["case_code"].startswith("WD-")
    assert data["category"] == "SECURITY"
    assert data["status"] == "SUBMITTED"
    assert "created_at" in data

    # Security check: MUST NOT reveal internal database ID or hash
    assert "id" not in data
    assert "case_code_hash" not in data


def test_track_report_by_case_code(client: TestClient):
    """Verify that a reporter can track status using their generated case code."""
    # 1. Submit report
    submit_res = client.post(
        "/api/v1/reports",
        json={
            "category": "CORRUPTION",
            "description": "Unauthorized alteration of procurement records and invoice numbers.",
        },
    )
    assert submit_res.status_code == 201
    case_code = submit_res.json()["case_code"]

    # 2. Track report
    track_res = client.get(f"/api/v1/reports/{case_code}")
    assert track_res.status_code == 200
    data = track_res.json()

    assert data["category"] == "CORRUPTION"
    assert data["status"] == "SUBMITTED"
    assert "submitted_at" in data
    assert "updates" in data
    assert len(data["updates"]) == 1
    assert data["updates"][0]["status"] == "SUBMITTED"
    assert "message" in data["updates"][0]

    # Security check: Internal DB id must NOT be in public lookup
    assert "id" not in data
    assert "case_code_hash" not in data


def test_track_report_invalid_code_returns_404(client: TestClient):
    """Verify invalid case code returns standard 404."""
    response = client.get("/api/v1/reports/WD-NONEXISTENT-CODE")
    assert response.status_code == 404
    assert "No report found" in response.json()["detail"]


def test_moderator_login_success_and_failure(client: TestClient, test_moderator: Moderator):
    """Verify moderator authentication produces a valid JWT token."""
    # Correct login
    valid_res = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": test_moderator.email,
            "password": "SecureTestPassword123!",
        },
    )
    assert valid_res.status_code == 200
    assert "access_token" in valid_res.json()
    assert valid_res.json()["token_type"] == "bearer"

    # Invalid password
    invalid_res = client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": test_moderator.email,
            "password": "WrongPassword!",
        },
    )
    assert invalid_res.status_code == 401


def test_moderator_report_management_lifecycle(
    client: TestClient,
    test_moderator: Moderator,
    auth_headers: dict,
):
    """Verify moderator end-to-end report review and status transitions."""
    # 1. Anonymous reporter submits a report
    submit_res = client.post(
        "/api/v1/reports",
        json={
            "category": "TECHNICAL",
            "description": "Production credentials inadvertently leaked into public deployment script.",
        },
    )
    case_code = submit_res.json()["case_code"]

    # 2. Unauthenticated access to moderator endpoints must be rejected (401)
    unauth_res = client.get("/api/v1/moderator/reports")
    assert unauth_res.status_code == 401

    # 3. Authenticated moderator lists reports
    list_res = client.get("/api/v1/moderator/reports", headers=auth_headers)
    assert list_res.status_code == 200
    reports = list_res.json()
    assert len(reports) >= 1
    report_id = reports[0]["id"]

    # 4. Moderator views detailed report by ID
    detail_res = client.get(f"/api/v1/moderator/reports/{report_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == report_id

    # 5. Moderator transitions status: SUBMITTED -> UNDER_REVIEW
    transition_1 = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=auth_headers,
        json={
            "status": "UNDER_REVIEW",
            "message": "Assigned to the Security Operations Team for formal inquiry.",
        },
    )
    assert transition_1.status_code == 200
    assert transition_1.json()["status"] == "UNDER_REVIEW"
    assert len(transition_1.json()["updates"]) == 2

    # 6. Reporter tracks case and sees the update
    track_res = client.get(f"/api/v1/reports/{case_code}")
    assert track_res.status_code == 200
    track_data = track_res.json()
    assert track_data["status"] == "UNDER_REVIEW"
    assert len(track_data["updates"]) == 2
    assert track_data["updates"][-1]["message"] == "Assigned to the Security Operations Team for formal inquiry."

    # 7. Moderator transitions status: UNDER_REVIEW -> RESOLVED
    transition_2 = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=auth_headers,
        json={
            "status": "RESOLVED",
            "message": "Revoked exposed credentials and rotated all secret environment keys.",
        },
    )
    assert transition_2.status_code == 200
    assert transition_2.json()["status"] == "RESOLVED"

    # 8. Invalid transition attempt (RESOLVED is terminal -> cannot transition to SUBMITTED) must be rejected with 400
    invalid_transition = client.patch(
        f"/api/v1/moderator/reports/{report_id}/status",
        headers=auth_headers,
        json={
            "status": "SUBMITTED",
            "message": "Illegal attempt to re-submit resolved case.",
        },
    )
    assert invalid_transition.status_code == 400
    assert "terminal status" in invalid_transition.json()["detail"]
