"""Section router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.section import (
    SectionCreate,
    SectionResponse,
    SectionUpdate,
)
from app.services import section as section_service
from app.services import verify_lock

router = APIRouter(prefix="/sections", tags=["sections"])


@router.post("", response_model=SectionResponse, status_code=201)
def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    """Create a new section in a schedule."""
    try:
        return section_service.create_section(db, section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{section_id}", response_model=SectionResponse)
def update_section(
    section_id: int,
    section: SectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update an existing section. Caller must hold the active lock on this section."""
    verify_lock(db, section_id, current_user.user_id)
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
