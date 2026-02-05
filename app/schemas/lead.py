from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.lead import LeadState


class LeadResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    resume_path: str | None
    state: LeadState
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadUpdateRequest(BaseModel):
    state: LeadState


class LeadCreateFields(BaseModel):
    """Used internally to validate the form fields on lead creation."""

    first_name: str
    last_name: str
    email: EmailStr
