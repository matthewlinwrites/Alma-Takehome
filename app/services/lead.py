import os
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.lead import Lead, LeadState
from app.services import email as email_service


def create_lead(
    db: Session,
    first_name: str,
    last_name: str,
    lead_email: str,
    resume: UploadFile | None = None,
) -> Lead:
    resume_path = None
    if resume and resume.filename:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, resume.filename)
        with open(file_path, "wb") as f:
            f.write(resume.file.read())
        resume_path = file_path

    lead = Lead(
        first_name=first_name,
        last_name=last_name,
        email=lead_email,
        resume_path=resume_path,
        state=LeadState.PENDING,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    email_service.send_prospect_email(lead.email, lead.first_name)
    email_service.send_attorney_email(lead.id, lead.first_name, lead.last_name)

    return lead


def get_leads(db: Session) -> list[Lead]:
    stmt = select(Lead).where(Lead.deleted_at.is_(None)).order_by(Lead.created_at.desc())
    return list(db.scalars(stmt).all())


def get_lead(db: Session, lead_id: str) -> Lead:
    stmt = select(Lead).where(Lead.id == lead_id, Lead.deleted_at.is_(None))
    lead = db.scalars(stmt).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


def update_lead_state(db: Session, lead_id: str, new_state: LeadState) -> Lead:
    lead = get_lead(db, lead_id)

    if lead.state == LeadState.REACHED_OUT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead has already been marked as REACHED_OUT",
        )
    if new_state != LeadState.REACHED_OUT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only transition from PENDING to REACHED_OUT",
        )

    lead.state = new_state
    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    return lead


def soft_delete_lead(db: Session, lead_id: str) -> Lead:
    lead = get_lead(db, lead_id)
    lead.deleted_at = datetime.now(timezone.utc)
    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    return lead
