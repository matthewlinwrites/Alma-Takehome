from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models.lead import LeadState
from app.schemas.lead import LeadCreateFields, LeadResponse, LeadUpdateRequest
from app.services import lead as lead_service

router = APIRouter(prefix="/api/leads", tags=["leads"])


# --- Public endpoints ---


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> LeadResponse:
    # Validate fields via Pydantic (email format, etc.)
    try:
        LeadCreateFields(first_name=first_name, last_name=last_name, email=email)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors(),
        )

    lead = lead_service.create_lead(db, first_name, last_name, email, resume)
    return LeadResponse.model_validate(lead)


# --- Internal endpoints (auth required) ---


@router.get("", response_model=list[LeadResponse], dependencies=[Depends(verify_api_key)])
def list_leads(db: Session = Depends(get_db)) -> list[LeadResponse]:
    leads = lead_service.get_leads(db)
    return [LeadResponse.model_validate(lead) for lead in leads]


@router.get("/{lead_id}", response_model=LeadResponse, dependencies=[Depends(verify_api_key)])
def get_lead(lead_id: str, db: Session = Depends(get_db)) -> LeadResponse:
    lead = lead_service.get_lead(db, lead_id)
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse, dependencies=[Depends(verify_api_key)])
def update_lead(
    lead_id: str,
    body: LeadUpdateRequest,
    db: Session = Depends(get_db),
) -> LeadResponse:
    lead = lead_service.update_lead_state(db, lead_id, body.state)
    return LeadResponse.model_validate(lead)


@router.delete(
    "/{lead_id}",
    response_model=LeadResponse,
    dependencies=[Depends(verify_api_key)],
)
def delete_lead(lead_id: str, db: Session = Depends(get_db)) -> LeadResponse:
    lead = lead_service.soft_delete_lead(db, lead_id)
    return LeadResponse.model_validate(lead)
