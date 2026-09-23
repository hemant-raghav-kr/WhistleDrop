"""Automated tests for secure anonymous evidence file upload and moderator retrieval."""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.moderator import Moderator
from app.models.report import Report
from app.services.storage_service import get_storage_service

# Valid sample file binary payloads with correct magic bytes
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
VALID_JPG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"
VALID_PDF_BYTES = b"%PDF-1.4\n%Fake PDF content for test verification\n%%EOF"
VALID_WEBP_BYTES = b"RIFF\x24\x00\x00\x00WEBPVP8 \x18\x00\x00\x00"
VALID_TXT_BYTES = b"Log entry: unauthorized database access detected at 02:00 UTC."


def test_1_report_without_evidence_json(client: TestClient):
    """Scenario 1: Report submission with no evidence via JSON."""
    res = client.post(
        "/api/v1/reports",
        json={"category": "SECURITY", "description": "Report with no evidence attached."},
    )
    assert res.status_code == 201
    data = res.json()
    assert "case_code" in data
    assert data["has_evidence"] is False


def test_2_url_only_report(client: TestClient):
    """Scenario 2: Report with reference URL only."""
    res = client.post(
        "/api/v1/reports",
        json={
            "category": "TECHNICAL",
            "description": "Report with reference URL only provided.",
            "evidence_url": "https://example.com/incident-log.pdf",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["has_evidence"] is True


def test_3_file_only_report_multipart(client: TestClient):
    """Scenario 3: Report with uploaded file only via multipart/form-data."""
    files = {
        "evidence_file": ("security_audit.png", io.BytesIO(VALID_PNG_BYTES), "image/png"),
    }
    data = {
        "category": "SECURITY",
        "description": "Confidential report with attached PNG screenshot.",
    }
    res = client.post("/api/v1/reports", data=data, files=files)
    assert res.status_code == 201
    resp_data = res.json()
    assert resp_data["has_evidence"] is True
    assert "case_code" in resp_data


def test_4_url_plus_file_report_multipart(client: TestClient):
    """Scenario 4: Report with BOTH reference URL and uploaded file."""
    files = {
        "evidence_file": ("incident_details.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf"),
    }
    data = {
        "category": "CORRUPTION",
        "description": "Report with both external reference URL and attached PDF document.",
        "evidence_url": "https://example.com/contract_archive.html",
    }
    res = client.post("/api/v1/reports", data=data, files=files)
    assert res.status_code == 201
    resp_data = res.json()
    assert resp_data["has_evidence"] is True


def test_5_valid_png_upload(client: TestClient):
    """Scenario 5: Upload valid PNG image."""
    files = {"evidence_file": ("test.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    data = {"category": "SECURITY", "description": "Testing valid PNG upload format."}
    res = client.post("/api/v1/reports", data=data, files=files)
    assert res.status_code == 201


def test_6_valid_jpg_upload(client: TestClient):
    """Scenario 6: Upload valid JPG/JPEG image."""
    files = {"evidence_file": ("photo.jpg", io.BytesIO(VALID_JPG_BYTES), "image/jpeg")}
    data = {"category": "HARASSMENT", "description": "Testing valid JPG upload format."}
    res = client.post("/api/v1/reports", data=data, files=files)
    assert res.status_code == 201


def test_7_valid_webp_upload(client: TestClient):
    """Scenario 7: Upload valid WEBP image."""
    files = {"evidence_file": ("diagram.webp", io.BytesIO(VALID_WEBP_BYTES), "image/webp")}
    data = {"category": "TECHNICAL", "description": "Testing valid WEBP upload format."}
    res = client.post("/api/v1/reports", data=data, files=files)
    assert res.status_code == 201


def test_8_valid_pdf_upload(client: TestClient):
    """Scenario 8: Upload valid PDF document."""
    files = {"evidence_file": ("document.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    data = {"category": "CORRUPTION", "description": "Testing valid PDF upload format."}
    res = client.post("/api/v1/reports", data=data, files=files)
    assert res.status_code == 201


def test_9_valid_txt_upload(client: TestClient):
    """Scenario 9: Upload valid TXT log file."""
    files = {"evidence_file": ("server.txt", io.BytesIO(VALID_TXT_BYTES), "text/plain")}
    data = {"category": "TECHNICAL", "description": "Testing valid TXT upload format."}
    res = client.post("/api/v1/reports", data=data, files=files)
    assert res.status_code == 201


def test_10_unsupported_file_type_rejected(client: TestClient):
    """Scenario 10: Prohibited executable and script files (.exe, .svg, .js) are rejected."""
    # Test .exe
    files_exe = {"evidence_file": ("malware.exe", io.BytesIO(b"MZ\x90\x00test"), "application/x-msdownload")}
    res_exe = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Attempting exe upload."}, files=files_exe)
    assert res_exe.status_code == 422
    assert "prohibited" in str(res_exe.json()).lower()

    # Test .svg
    files_svg = {"evidence_file": ("xss.svg", io.BytesIO(b"<svg onload=alert(1)>"), "image/svg+xml")}
    res_svg = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Attempting svg upload."}, files=files_svg)
    assert res_svg.status_code == 422

    # Test .js
    files_js = {"evidence_file": ("script.js", io.BytesIO(b"console.log(1);"), "application/javascript")}
    res_js = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Attempting js upload."}, files=files_js)
    assert res_js.status_code == 422


def test_11_oversized_file_rejected(client: TestClient):
    """Scenario 11: File exceeding 10 MB is rejected with 422."""
    oversized_bytes = b"0" * (10 * 1024 * 1024 + 1024)  # 10 MB + 1 KB
    files = {"evidence_file": ("huge.txt", io.BytesIO(oversized_bytes), "text/plain")}
    res = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Testing oversized file upload."}, files=files)
    assert res.status_code == 422
    assert "exceeds maximum allowed limit of 10 MB" in str(res.json())


def test_12_malformed_upload_signature_mismatch(client: TestClient):
    """Scenario 12: Extension declared as PNG but file bytes are text (magic byte spoofing)."""
    spoofed_bytes = b"This is just plain text, not a real PNG image."
    files = {"evidence_file": ("fake_image.png", io.BytesIO(spoofed_bytes), "image/png")}
    res = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Testing spoofed file signature."}, files=files)
    assert res.status_code == 422
    assert "does not match declared type" in str(res.json())


def test_13_unauthorized_evidence_access(client: TestClient, auth_headers: dict):
    """Scenario 13: Accessing evidence without JWT returns 401."""
    # First submit report with valid file
    files = {"evidence_file": ("proof.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    res = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Testing unauthorized access."}, files=files)
    assert res.status_code == 201

    # Get report and evidence ID from moderator queue
    queue_res = client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_data = [r for r in queue_res.json() if r["evidence_files"]][0]
    report_id = report_data["id"]
    file_id = report_data["evidence_files"][0]["id"]

    # Request without token -> 401
    res_no_auth = client.get(f"/api/v1/moderator/reports/{report_id}/evidence/{file_id}")
    assert res_no_auth.status_code == 401


def test_14_invalid_jwt_evidence_access(client: TestClient, auth_headers: dict):
    """Scenario 14: Accessing evidence with forged/invalid JWT returns 401."""
    # Create report with file first
    files = {"evidence_file": ("proof14.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    res = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Testing invalid JWT access."}, files=files)
    assert res.status_code == 201

    queue_res = client.get("/api/v1/moderator/reports", headers=auth_headers)
    report_data = [r for r in queue_res.json() if r["evidence_files"]][0]
    report_id = report_data["id"]
    file_id = report_data["evidence_files"][0]["id"]

    res_bad_auth = client.get(
        f"/api/v1/moderator/reports/{report_id}/evidence/{file_id}",
        headers={"Authorization": "Bearer forged.invalid.token"},
    )
    assert res_bad_auth.status_code == 401


def test_15_evidence_belonging_to_another_report(client: TestClient, auth_headers: dict):
    """Scenario 15: Cross-report ID mismatch returns 404."""
    # Create two reports with files
    f1 = {"evidence_file": ("f1.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    f2 = {"evidence_file": ("f2.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    r1 = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Report 1 file."}, files=f1)
    r2 = client.post("/api/v1/reports", data={"category": "TECHNICAL", "description": "Report 2 file."}, files=f2)

    q = client.get("/api/v1/moderator/reports", headers=auth_headers).json()
    rep1 = [r for r in q if r["category"] == "SECURITY" and r["evidence_files"]][0]
    rep2 = [r for r in q if r["category"] == "TECHNICAL" and r["evidence_files"]][0]

    # Query rep1 with rep2's file ID
    file_id_from_rep2 = rep2["evidence_files"][0]["id"]
    res_mismatch = client.get(
        f"/api/v1/moderator/reports/{rep1['id']}/evidence/{file_id_from_rep2}",
        headers=auth_headers,
    )
    assert res_mismatch.status_code == 404


def test_16_nonexistent_evidence_returns_404(client: TestClient, auth_headers: dict):
    """Scenario 16: Nonexistent evidence ID returns 404."""
    res = client.post("/api/v1/reports", json={"category": "SECURITY", "description": "Report for 404 check."})
    assert res.status_code == 201

    q = client.get("/api/v1/moderator/reports", headers=auth_headers).json()
    report_id = q[0]["id"]
    fake_file_id = str(uuid.uuid4())

    res = client.get(
        f"/api/v1/moderator/reports/{report_id}/evidence/{fake_file_id}",
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_17_successful_moderator_evidence_access(client: TestClient, auth_headers: dict):
    """Scenario 17: Authenticated moderator successfully retrieves signed access and streams evidence."""
    files = {"evidence_file": ("audit_evidence.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    sub_res = client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Report for moderator access test."}, files=files)
    assert sub_res.status_code == 201

    q = client.get("/api/v1/moderator/reports", headers=auth_headers).json()
    rep = [r for r in q if r["evidence_files"] and r["evidence_files"][0]["original_filename"] == "audit_evidence.pdf"][0]
    report_id = rep["id"]
    file_id = rep["evidence_files"][0]["id"]

    # 1. Fetch signed URL / download info
    res_access = client.get(
        f"/api/v1/moderator/reports/{report_id}/evidence/{file_id}",
        headers=auth_headers,
    )
    assert res_access.status_code == 200
    access_data = res_access.json()
    assert access_data["original_filename"] == "audit_evidence.pdf"
    assert access_data["mime_type"] == "application/pdf"
    assert "download_url" in access_data

    # 2. Stream file content directly
    res_stream = client.get(
        f"/api/v1/moderator/reports/{report_id}/evidence/{file_id}/stream",
        headers=auth_headers,
    )
    assert res_stream.status_code == 200
    assert res_stream.content == VALID_PDF_BYTES
    assert "application/pdf" in res_stream.headers.get("content-type", "")


def test_18_storage_cleanup_on_transaction_failure(client: TestClient, monkeypatch):
    """Scenario 18: If database commit fails after storage upload, uploaded object is deleted."""
    storage = get_storage_service()
    deleted_keys = []

    original_delete = storage.delete_file
    def mock_delete(key: str) -> bool:
        deleted_keys.append(key)
        return original_delete(key)
    monkeypatch.setattr(storage, "delete_file", mock_delete)

    # Monkeypatch commit on Session to raise an error
    from sqlalchemy.orm import Session
    def failing_commit(self):
        raise RuntimeError("Simulated database failure during report commit")
    monkeypatch.setattr(Session, "commit", failing_commit)

    files = {"evidence_file": ("cleanup_test.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    with pytest.raises(RuntimeError):
        client.post("/api/v1/reports", data={"category": "SECURITY", "description": "Testing atomic cleanup."}, files=files)

    assert len(deleted_keys) == 1
    assert "cleanup_test.png" in deleted_keys[0]
