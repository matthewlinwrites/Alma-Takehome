from collections.abc import Generator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import SessionLocal

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str | None:
    if not settings.AUTH_ENABLED:
        return None
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key
