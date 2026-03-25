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
from app.services.section import ScheduleNotFoundError

router = APIRouter(prefix="/sections", tags=["sections"])


@router.get("/{schedule_id}/rich", response_model=list[SectionRichResponse])
def get_rich_sections(schedule_id: int, db: Session = Depends(get_db)):
    """Get all sections with denormalized course, time block, and instructor data."""
    try:
        section_service.require_schedule(db, schedule_id)
        return section_service.get_rich_sections(db, schedule_id)
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found") from None


@router.get("/{schedule_id}", response_model=list[SectionResponse])
def get_sections(schedule_id: int, db: Session = Depends(get_db)):
    """Get all sections for a schedule."""
    try:
        section_service.require_schedule(db, schedule_id)
        return section_service.get_all_sections(db, schedule_id)
    except ScheduleNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule not found") from None


@router.post("", response_model=SectionResponse, status_code=201)
def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    """Create a new section in a schedule."""
    try:
        return section_service.create_section(db, section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{section_id}", response_model=SectionResponse)
def update_section(
    section_id: int, section: SectionUpdate, db: Session = Depends(get_db)
):
    """Update an existing section."""
    try:
        updated = section_service.update_section(db, section_id, section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if updated is None:
        raise HTTPException(status_code=404, detail="Section not found")
    return updated


@router.delete("/{section_id}", status_code=204)
def delete_section(section_id: int, db: Session = Depends(get_db)):
    """Delete a section from a schedule."""
    deleted = section_service.delete_section(db, section_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Section not found")
    return None
