"""User and invite business logic."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.user import UserResponse
from app.services import auth0_service


@dataclass
class InviteResult:
    user: UserResponse
    signup_url: str


def invite_user(db: Session, nuid: int, role: str) -> InviteResult:
    """Invite a faculty member.

    1. Validates the faculty record exists and hasn't already been invited.
    2. Creates the local User record with auth0_sub=None.
    3. Returns a pre-filled Auth0 sign-up URL.

    On first login Auth0 redirects back to the app; get_or_link_user matches
    the new Auth0 sub to this record by email and backfills the sub.
    """
    from app.repositories import (
        faculty as faculty_repo,  # avoid circular at module level
    )

    faculty = faculty_repo.get_by_nuid(db, nuid)
    if faculty is None:
        raise ValueError(f"Faculty with NUID {nuid} not found")

    if user_repo.get_by_nuid(db, nuid) is not None:
        raise ValueError(f"Faculty member {nuid} has already been invited")

    if user_repo.get_by_email(db, faculty.email) is not None:
        raise ValueError(f"A user with email {faculty.email} already exists")

    user = User(
        nuid=faculty.nuid,
        first_name=faculty.first_name,
        last_name=faculty.last_name,
        email=faculty.email,
        role=role,
        auth0_sub=None,
        active=True,
    )
    user_repo.create(db, user)

    signup_url = auth0_service.build_signup_url(faculty.email)

    return InviteResult(
        user=UserResponse.model_validate(user),
        signup_url=signup_url,
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return user_repo.get_by_id(db, user_id)


def get_all_users(db: Session) -> list[User]:
    return user_repo.get_all(db)


def get_or_link_user(db: Session, sub: str, access_token: str) -> User:
    """Resolve the current authenticated user from the DB.

    On first login the auth0_sub is null; we match by email via the Auth0
    /userinfo endpoint and persist the sub for future requests.
    """
    import httpx

    from app.core.settings import settings

    user = user_repo.get_by_auth0_sub(db, sub)
    if user is not None:
        return user

    # First login: look up email from Auth0 userinfo
    resp = httpx.get(
        f"https://{settings.AUTH0_DOMAIN}/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    email = resp.json().get("email")
    if not email:
        raise ValueError("Could not retrieve email from Auth0 userinfo")

    user = user_repo.get_by_email(db, email)
    if user is None:
        raise LookupError(f"No user record found for {email}. Contact an admin.")

    user_repo.set_auth0_sub(db, user, sub)
    return user
