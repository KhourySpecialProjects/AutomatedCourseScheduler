"""Section router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.section import SectionResponse
from app.services import section as section_service

router = APIRouter(prefix="/sections", tags=["sections"])


# We will need to specify schedule ID at some point
@router.get("", response_model=list[SectionResponse])
def get_sections(db: Session = Depends(get_db)):
    return section_service.get_all_sections(db)
