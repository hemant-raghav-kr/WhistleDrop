"""Public endpoints for confidential report submission and case tracking."""

import json
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.report import (
    ReportCreate,
    ReportPublicCreated,
    ReportPublicLookup,
)
from app.services.report_service import create_report, get_report_by_case_code
from app.utils.file_validation import FileValidationError, validate_evidence_file

router = APIRouter()


@router.post(
    "",
    response_model=ReportPublicCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Submit anonymous report (Supports JSON or Multipart Evidence Upload)",
    description=(
        "Zero-knowledge confidential report submission endpoint. "
        "No reporter identity (name, email, phone, IP address, or device fingerprint) is collected or stored. "
        "Supports optional evidence URL and/or optional evidence file upload (max 10MB; PNG, JPG, WEBP, PDF, TXT). "
        "Accepts either application/json or multipart/form-data. "
        "Generates an unpredictable cryptographically secure case code (32^16 = 2^80 ≈ 1.2089 × 10^24 combinations, ~80 bits of entropy) and returns the "
        "raw code once to the reporter. The database persists only a one-way HMAC-SHA256 digest using a server-side secret key."
    ),
    responses={
        201: {"description": "Report submitted successfully; case code generated"},
        422: {"description": "Validation error (invalid category, short description, malformed URL, invalid file)"},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "example": "TECHNICAL", "description": "Report category"},
                            "description": {"type": "string", "example": "Incident description text...", "description": "10-10,000 characters"},
                            "evidence_url": {"type": "string", "example": "https://example.com/log.txt", "description": "Optional HTTP/HTTPS reference URL"},
                            "evidence_file": {"type": "string", "format": "binary", "description": "Optional evidence file (max 10MB; PNG, JPG, WEBP, PDF, TXT)"},
                        },
                        "required": ["category", "description"],
                    }
                },
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ReportCreate"}
                },
            }
        }
    },
)
async def submit_report(
    request: Request,
    db: Session = Depends(get_db),
) -> ReportPublicCreated:
    """Submit a confidential report anonymously with optional evidence attachment."""
    content_type = request.headers.get("content-type", "").lower()
    evidence_file_data = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        category = form.get("category")
        description = form.get("description")
        evidence_url = form.get("evidence_url")

        # Validate core text fields via Pydantic model
        try:
            report_in = ReportCreate(
                category=category,  # type: ignore
                description=description,  # type: ignore
                evidence_url=evidence_url if evidence_url else None,
            )
        except ValidationError as exc:
            raise RequestValidationError(exc.errors())

        # Validate optional file upload if present
        file_obj = form.get("evidence_file")
        if file_obj and hasattr(file_obj, "filename") and file_obj.filename:
            file_bytes = await file_obj.read()
            if len(file_bytes) > 0:
                try:
                    clean_name, mime, size = validate_evidence_file(
                        filename=file_obj.filename,
                        content_type=file_obj.content_type or "application/octet-stream",
                        file_bytes=file_bytes,
                    )
                    evidence_file_data = (clean_name, mime, size, file_bytes)
                except FileValidationError as e:
                    raise RequestValidationError([{
                        "loc": ["body", "evidence_file"],
                        "msg": str(e),
                        "type": "value_error",
                    }])
    else:
        # JSON payload parsing
        try:
            body = await request.json()
        except Exception:
            raise RequestValidationError([{
                "loc": ["body"],
                "msg": "Malformed JSON request body.",
                "type": "json_invalid",
            }])

        try:
            report_in = ReportCreate.model_validate(body)
        except ValidationError as exc:
            raise RequestValidationError(exc.errors())

    # Create report with atomicity and cleanup guarantees
    report, case_code = create_report(
        db=db,
        report_in=report_in,
        evidence_file_data=evidence_file_data,
    )

    has_ev = bool(report.evidence_url or evidence_file_data)
    return ReportPublicCreated(
        case_code=case_code,
        category=report.category,
        status=report.status,
        created_at=report.created_at,
        has_evidence=has_ev,
    )


@router.get(
    "/{case_code}",
    response_model=ReportPublicLookup,
    status_code=status.HTTP_200_OK,
    summary="Track report status by case code",
    description=(
        "Public case tracking endpoint. Hashes the provided case code using HMAC-SHA256 to lookup the case. "
        "Returns sanitized public case information: category, current status, submitted_at, updated_at, "
        "and the updates timeline. Internal database UUIDs, cryptographic hashes, private storage URLs, "
        "and moderator identities are strictly concealed."
    ),
    responses={
        200: {"description": "Report found; public status and updates returned"},
        404: {"description": "No report found with the provided case code"},
    },
)
def track_report(
    case_code: str,
    db: Session = Depends(get_db),
) -> ReportPublicLookup:
    """Retrieve report status and audit updates using the confidential case code."""
    report = get_report_by_case_code(db=db, case_code=case_code)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found with the provided case code. Please verify the code and try again.",
        )

    return ReportPublicLookup.model_validate(report)
