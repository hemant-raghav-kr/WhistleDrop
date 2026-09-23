"""Protected endpoints for moderator report management and status workflow."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_moderator, get_db
from app.models.moderator import Moderator
from app.models.report import ReportStatus
from app.schemas.evidence import EvidenceDownloadResponse
from app.schemas.report import (
    ReportModeratorRead,
    ReportStatusTransitionRequest,
)
from app.services.report_service import (
    InvalidStatusTransitionError,
    get_evidence_file,
    get_report_by_id,
    get_reports,
    update_report_status,
)
from app.services.storage_service import get_storage_service

router = APIRouter()


@router.get(
    "/reports",
    response_model=List[ReportModeratorRead],
    status_code=status.HTTP_200_OK,
    summary="List all reports (Moderator only)",
    description=(
        "Retrieve reports queue with pagination and optional filtering by status and/or category. "
        "Filters can be combined (e.g. ?status=UNDER_REVIEW&category=TECHNICAL). "
        "Contains full incident narrative and update history, but absolutely NO reporter identity "
        "information, which is never collected by the application."
    ),
    responses={
        200: {"description": "Filtered list of reports returned"},
        401: {"description": "Missing, invalid, or expired JWT bearer token"},
        403: {"description": "Inactive moderator account"},
    },
)
def list_reports(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Page limit (1-100)"),
    status_filter: Optional[ReportStatus] = Query(None, alias="status", description="Filter by status"),
    category_filter: Optional[str] = Query(None, alias="category", description="Filter by category (case-insensitive)"),
    db: Session = Depends(get_db),
    current_moderator: Moderator = Depends(get_current_moderator),
) -> List[ReportModeratorRead]:
    """List reports for moderator triage and review."""
    reports = get_reports(
        db=db,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        category_filter=category_filter,
    )
    return [ReportModeratorRead.model_validate(r) for r in reports]


@router.get(
    "/reports/{report_id}",
    response_model=ReportModeratorRead,
    status_code=status.HTTP_200_OK,
    summary="Get report details (Moderator only)",
    description=(
        "Retrieve full report details including internal ID, description, evidence URL, and status updates timeline. "
        "Case-code hashes and password hashes are never exposed."
    ),
    responses={
        200: {"description": "Report details returned"},
        401: {"description": "Missing, invalid, or expired JWT bearer token"},
        403: {"description": "Inactive moderator account"},
        404: {"description": "Report not found with the specified ID"},
        422: {"description": "Invalid UUID format in report_id parameter"},
    },
)
def get_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_moderator: Moderator = Depends(get_current_moderator),
) -> ReportModeratorRead:
    """Retrieve an individual report by internal UUID."""
    report = get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )
    return ReportModeratorRead.model_validate(report)


@router.patch(
    "/reports/{report_id}/status",
    response_model=ReportModeratorRead,
    status_code=status.HTTP_200_OK,
    summary="Transition report status (Moderator only)",
    description=(
        "Execute a transactional lifecycle state transition on a report: "
        "SUBMITTED -> UNDER_REVIEW -> RESOLVED or SUBMITTED -> UNDER_REVIEW -> DISMISSED. "
        "Invalid transitions are rejected with HTTP 400 Bad Request. "
        "Updates the report status and appends a status_updates audit record atomically."
    ),
    responses={
        200: {"description": "Report status successfully transitioned"},
        400: {"description": "Invalid status transition attempted"},
        401: {"description": "Missing, invalid, or expired JWT bearer token"},
        403: {"description": "Inactive moderator account"},
        404: {"description": "Report not found with the specified ID"},
        422: {"description": "Invalid UUID format or malformed request body"},
    },
)
def change_report_status(
    report_id: uuid.UUID,
    transition_in: ReportStatusTransitionRequest,
    db: Session = Depends(get_db),
    current_moderator: Moderator = Depends(get_current_moderator),
) -> ReportModeratorRead:
    """Execute a validated lifecycle state transition on a report."""
    report = get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )

    try:
        updated_report = update_report_status(
            db=db,
            report=report,
            new_status=transition_in.status,
            message=transition_in.message,
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ReportModeratorRead.model_validate(updated_report)


@router.get(
    "/reports/{report_id}/evidence/{file_id}",
    response_model=EvidenceDownloadResponse,
    status_code=status.HTTP_200_OK,
    summary="Get short-lived signed access to evidence file (Moderator only)",
    description=(
        "Generate a short-lived signed download URL for an uploaded evidence attachment. "
        "Strictly verifies moderator JWT, confirms report exists, and verifies the file belongs "
        "to the specified report. Storage credentials and private bucket paths are strictly concealed."
    ),
    responses={
        200: {"description": "Signed download URL and file metadata returned"},
        401: {"description": "Missing, invalid, or expired JWT bearer token"},
        403: {"description": "Inactive moderator account"},
        404: {"description": "Report or evidence file not found, or file does not belong to report"},
        422: {"description": "Invalid UUID format"},
    },
)
def get_report_evidence(
    report_id: uuid.UUID,
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_moderator: Moderator = Depends(get_current_moderator),
) -> EvidenceDownloadResponse:
    """Retrieve signed access for an evidence file attached to a report."""
    report = get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )

    evidence_file = get_evidence_file(db=db, report_id=report_id, file_id=file_id)
    if not evidence_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence file with ID '{file_id}' not found for report '{report_id}'.",
        )

    storage_service = get_storage_service()
    signed_url = storage_service.generate_signed_url(evidence_file.storage_key, expires_in=300)

    # In local fallback mode, prefix with base endpoint
    if signed_url.startswith("/api/v1/moderator/evidence/stream"):
        signed_url = f"/api/v1/moderator/reports/{report_id}/evidence/{file_id}/stream"

    return EvidenceDownloadResponse(
        id=evidence_file.id,
        original_filename=evidence_file.original_filename,
        mime_type=evidence_file.mime_type,
        file_size=evidence_file.file_size,
        download_url=signed_url,
        expires_in=300,
    )


@router.get(
    "/reports/{report_id}/evidence/{file_id}/stream",
    status_code=status.HTTP_200_OK,
    summary="Securely stream evidence file content (Moderator only)",
    description=(
        "Directly stream the binary bytes of an uploaded evidence file to an authenticated moderator. "
        "Sets appropriate Content-Type and Content-Disposition headers."
    ),
    responses={
        200: {"description": "Binary file streamed with appropriate Content-Type"},
        401: {"description": "Missing, invalid, or expired JWT bearer token"},
        403: {"description": "Inactive moderator account"},
        404: {"description": "Report or evidence file not found"},
        422: {"description": "Invalid UUID format"},
    },
)
def stream_report_evidence(
    report_id: uuid.UUID,
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_moderator: Moderator = Depends(get_current_moderator),
) -> Response:
    """Stream evidence file content to an authorized moderator."""
    report = get_report_by_id(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )

    evidence_file = get_evidence_file(db=db, report_id=report_id, file_id=file_id)
    if not evidence_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence file with ID '{file_id}' not found for report '{report_id}'.",
        )

    storage_service = get_storage_service()
    try:
        file_bytes = storage_service.get_file_bytes(evidence_file.storage_key)
    except Exception:
        raise HTTPException(status_code=404, detail="Failed to retrieve file from storage provider.")

    return Response(
        content=file_bytes,
        media_type=evidence_file.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{evidence_file.original_filename}"',
            "Content-Length": str(evidence_file.file_size),
        },
    )
