"""User and invite business logic."""

from dataclasses import dataclass

import requests
from jose import jwt
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.user import AdminInviteRequest, UserResponse
from app.services import auth0_service


@dataclass
class InviteResult:
    user: UserResponse
    signup_url: str


def invite_admin(db: Session, body: AdminInviteRequest) -> InviteResult:
    """Create pending admin without a faculty record; signup URL uses email for Auth0 login_hint."""
    if user_repo.get_by_nuid(db, body.nuid) is not None:
        raise ValueError(f"A user with NUID {body.nuid} already exists")

    if user_repo.get_by_email(db, body.email) is not None:
        raise ValueError(f"A user with email {body.email} already exists")

    user = User(
        nuid=body.nuid,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        role="ADMIN",
        auth0_sub=None,
        active=True,
    )
    user_repo.create(db, user)

    signup_url = auth0_service.build_signup_url(user.email)

    return InviteResult(
        user=UserResponse.model_validate(user),
        signup_url=signup_url,
    )


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


def export_invites(db: Session) -> list:
    """Return invite link data for all active faculty without a linked account.

    Creates User records for any faculty without one (marking them as invited).
    Faculty with a pending User record (auth0_sub=None) are included but not
    re-created.
    """
    from app.repositories import faculty as faculty_repo
    from app.schemas.user import InviteLinkResponse

    targets = faculty_repo.get_uninvited_or_pending_active(db)
    results = []

    for faculty in targets:
        if user_repo.get_by_nuid(db, faculty.nuid) is None:
            user_repo.create(
                db,
                User(
                    nuid=faculty.nuid,
                    first_name=faculty.first_name,
                    last_name=faculty.last_name,
                    email=faculty.email,
                    role="VIEWER",
                    auth0_sub=None,
                    active=True,
                ),
            )
        results.append(
            InviteLinkResponse(
                first_name=faculty.first_name or "",
                last_name=faculty.last_name or "",
                email=faculty.email,
                invite_link=auth0_service.build_signup_url(faculty.email),
            )
        )

    return results


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return user_repo.get_by_id(db, user_id)


def get_all_users(db: Session) -> list[User]:
    return user_repo.get_all(db)


async def get_or_link_user(db: Session, sub: str, access_token: str) -> User:
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
    async with httpx.AsyncClient() as client:
        resp = await client.get(
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


_jwks = None


def get_jwks():
    global _jwks
    if _jwks is None:
        _jwks = requests.get(f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json").json()
    return _jwks


def get_sub(token: str) -> str:
    header = jwt.get_unverified_header(token)
    key = next(k for k in get_jwks()["keys"] if k["kid"] == header["kid"])
    payload = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=settings.AUTH0_AUDIENCE,
        issuer=f"https://{settings.AUTH0_DOMAIN}/",
    )
    return payload["sub"]
