"""Business logic for confidential reports, transactional state transitions, and case lookups."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.evidence_file import EvidenceFile
from app.models.report import Report, ReportCategory, ReportStatus
from app.models.status_update import StatusUpdate
from app.schemas.report import ReportCreate
from app.services.storage_service import get_storage_service
from app.utils.case_code import generate_case_code, hash_case_code


class InvalidStatusTransitionError(ValueError):
    """Raised when an illegal status lifecycle transition is attempted."""
    pass


# Deterministic state machine defining permissible transitions:
# SUBMITTED -> UNDER_REVIEW -> RESOLVED
# OR
# SUBMITTED -> UNDER_REVIEW -> DISMISSED
VALID_TRANSITIONS = {
    ReportStatus.SUBMITTED: {ReportStatus.UNDER_REVIEW},
    ReportStatus.UNDER_REVIEW: {ReportStatus.RESOLVED, ReportStatus.DISMISSED},
    ReportStatus.RESOLVED: set(),
    ReportStatus.DISMISSED: set(),
}


def create_report(
    db: Session,
    report_in: ReportCreate,
    evidence_file_data: Optional[Tuple[str, str, int, bytes]] = None,
) -> Tuple[Report, str]:
    """Create a new confidential report with transactional atomicity.

    Privacy & Security Guarantees:
    - Generates a cryptographically strong, unpredictable case code (CSPRNG, 32^16 = 2^80 ≈ 1.2089 × 10^24 combinations, ~80 bits of entropy).
    - Persists ONLY the one-way HMAC-SHA256 digest using a server-side secret key in the database.
    - Transactionally creates the report and its initial SUBMITTED audit log.
    - If an evidence file is attached, uploads to private object storage and stores metadata.
    - Automatically cleans up uploaded storage objects if the database transaction fails.
    - Returns the persistent report entity and the plaintext case code (for the reporter only).
    """
    case_code = generate_case_code()
    code_hash = hash_case_code(case_code)

    # Collision defense
    while db.query(Report).filter(Report.case_code_hash == code_hash).first():
        case_code = generate_case_code()
        code_hash = hash_case_code(case_code)

    storage_service = get_storage_service()
    uploaded_storage_key: Optional[str] = None

    try:
        db_report = Report(
            case_code_hash=code_hash,
            category=report_in.category,
            description=report_in.description,
            evidence_url=report_in.evidence_url,
            status=ReportStatus.SUBMITTED,
        )
        db.add(db_report)
        db.flush()

        # Handle optional evidence file upload
        if evidence_file_data:
            clean_filename, mime_type, file_size, file_bytes = evidence_file_data
            storage_key = storage_service.generate_storage_key(db_report.id, clean_filename)
            # Upload to object storage
            storage_service.upload_file(storage_key=storage_key, file_bytes=file_bytes, mime_type=mime_type)
            uploaded_storage_key = storage_key

            evidence_rec = EvidenceFile(
                report_id=db_report.id,
                original_filename=clean_filename,
                storage_key=storage_key,
                mime_type=mime_type,
                file_size=file_size,
            )
            db.add(evidence_rec)

        # Initial status update history
        initial_update = StatusUpdate(
            report_id=db_report.id,
            status=ReportStatus.SUBMITTED,
            update_message="Report submitted securely. Assigned confidential case code for tracking.",
        )
        db.add(initial_update)
        db.commit()
        db.refresh(db_report)
        return db_report, case_code
    except Exception:
        db.rollback()
        # Clean up uploaded storage object on partial failure
        if uploaded_storage_key:
            storage_service.delete_file(uploaded_storage_key)
        raise


def get_evidence_file(
    db: Session,
    report_id: uuid.UUID,
    file_id: uuid.UUID,
) -> Optional[EvidenceFile]:
    """Retrieve an evidence file ensuring it belongs to the specified report."""
    return db.query(EvidenceFile).filter(
        EvidenceFile.id == file_id,
        EvidenceFile.report_id == report_id,
    ).first()


def get_report_by_case_code(db: Session, case_code: str) -> Optional[Report]:
    """Retrieve a report using the reporter's plaintext case code."""
    code_hash = hash_case_code(case_code)
    return db.query(Report).filter(Report.case_code_hash == code_hash).first()


def get_report_by_id(db: Session, report_id: uuid.UUID) -> Optional[Report]:
    """Retrieve a report by internal UUID (moderator-only access)."""
    return db.query(Report).filter(Report.id == report_id).first()


def get_reports(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[ReportStatus] = None,
    category_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Report]:
    """Retrieve reports with pagination, category/status filtering, and search for moderator review."""
    query = db.query(Report)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    if category_filter:
        cat_clean = category_filter.strip().upper()
        query = query.filter(Report.category == cat_clean)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(Report.description.ilike(term))
    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


def update_report_status(
    db: Session,
    report: Report,
    new_status: ReportStatus,
    message: str,
) -> Report:
    """Validate and execute an atomic status transition on a report.

    Validates:
    - Verifies report is not permanently closed.
    - Target status is valid for the current lifecycle state.
    - Appends audit trail entry into `status_updates`.
    - Guarantees transaction atomicity (both update or neither does).
    """
    if report.is_closed:
        raise InvalidStatusTransitionError("This case has been permanently closed and cannot be transitioned.")

    if report.status == new_status:
        raise InvalidStatusTransitionError(f"Report is already in '{new_status.value}' status.")

    allowed = VALID_TRANSITIONS.get(report.status, set())
    if new_status not in allowed:
        if allowed:
            allowed_str = ", ".join(s.value for s in allowed)
            err_msg = (
                f"Cannot transition from '{report.status.value}' to '{new_status.value}'. "
                f"Allowed next states: [{allowed_str}]"
            )
        else:
            err_msg = f"Report in terminal status '{report.status.value}' cannot be transitioned."
        raise InvalidStatusTransitionError(err_msg)

    try:
        report.status = new_status
        report.updated_at = datetime.now(timezone.utc)
        audit_update = StatusUpdate(
            report_id=report.id,
            status=new_status,
            update_message=message.strip(),
        )
        db.add(audit_update)
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise


def close_report(
    db: Session,
    report: Report,
    message: Optional[str] = None,
) -> Report:
    """Permanently close a case. Closed cases cannot undergo further status transitions."""
    if report.is_closed:
        raise InvalidStatusTransitionError("Case is already permanently closed.")

    try:
        report.is_closed = True
        report.closed_at = datetime.now(timezone.utc)
        report.updated_at = datetime.now(timezone.utc)
        close_message = message.strip() if message and message.strip() else "Case permanently closed by moderator."
        audit_update = StatusUpdate(
            report_id=report.id,
            status=report.status,
            update_message=close_message,
        )
        db.add(audit_update)
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise

