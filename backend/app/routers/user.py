"""User management and invite endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_db_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import InviteLinkResponse, InviteRequest, InviteResponse, UserResponse
from app.services import user as user_service

router = APIRouter(prefix="/api", tags=["users"])


@router.post("/invites", response_model=InviteResponse, status_code=201)
def create_invite(
    body: InviteRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Invite a faculty member. Requires admin role.

    Looks up the faculty record by NUID, creates a User, registers them in
    Auth0, generates a password-change ticket, and sends an invite email.
    """
    try:
        result = user_service.invite_user(db, body.nuid, body.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return InviteResponse(user=result.user, signup_url=result.signup_url)


@router.get("/invites/export", response_model=list[InviteLinkResponse])
def export_invites(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return invite links for all active faculty without a linked account.

    Creates pending User records for any who were not yet invited.
    Requires admin role.
    """
    return user_service.export_invites(db)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return all users. Requires admin role."""
    return user_service.get_all_users(db)


@router.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_db_user)):
    """Return the profile of the currently authenticated user."""
    return current_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Return a single user by ID. Requires admin role."""
    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return user
