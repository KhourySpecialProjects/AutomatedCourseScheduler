"""Section router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.section import (
    SectionCreate,
    SectionResponse,
    SectionRichResponse,
    SectionUpdate,
)
from app.services import section as section_service

router = APIRouter(prefix="/sections", tags=["sections"])


@router.get("/{schedule_id}/rich", response_model=list[SectionRichResponse])
def get_rich_sections(schedule_id: int, db: Session = Depends(get_db)):
    """Get all sections with denormalized course, time block, and instructor data."""
    return section_service.get_rich_sections(db, schedule_id)


@router.get("/{schedule_id}", response_model=list[SectionResponse])
def get_sections(schedule_id: int, db: Session = Depends(get_db)):
    """Get all sections."""
    return section_service.get_all_sections(db, schedule_id)


@router.post("", response_model=SectionResponse, status_code=201)
def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    """Create a new section in a schedule."""
    # TODO: Implement section creation
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put("/{section_id}", response_model=SectionResponse)
def update_section(
    section_id: int, section: SectionUpdate, db: Session = Depends(get_db)
):
    """Update an existing section."""
    # TODO: Implement section update
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{section_id}", status_code=204)
def delete_section(section_id: int, db: Session = Depends(get_db)):
    """Delete a section from a schedule."""
    # TODO: Implement section deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")
