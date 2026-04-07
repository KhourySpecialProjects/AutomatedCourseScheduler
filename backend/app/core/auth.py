"""Auth0 authentication dependencies."""

import os

from fastapi import Depends, HTTPException, Request
from fastapi_plugin.fast_api_client import Auth0FastAPI
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

auth0_domain = os.environ.get("AUTH0_DOMAIN")
auth0_audience = os.environ.get("AUTH0_AUDIENCE")

if not auth0_domain or not auth0_audience:
    raise RuntimeError("AUTH0_DOMAIN and AUTH0_AUDIENCE must be set")

auth0 = Auth0FastAPI(domain=auth0_domain, audience=auth0_audience)

_verifier = auth0.require_auth()


async def get_current_user(claims: dict = Depends(_verifier)) -> dict:
    """Validates the Auth0 JWT and returns the raw claims.

    Used as a lightweight auth guard on existing routes that don't need
    the full DB user object.
    """
    return claims


async def get_db_user(
    request: Request,
    claims: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Resolves the authenticated user from the database.

    On first login the auth0_sub is null in the DB; we call Auth0's /userinfo
    endpoint with the bearer token to get the email, match it to a User record,
    and persist the sub for all subsequent requests.
    """
    from app.services.user_service import get_or_link_user

    sub = claims["sub"]
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")

    try:
        return await get_or_link_user(db, sub, token)
    except LookupError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to resolve user: {exc}") from exc


async def require_admin(user: User = Depends(get_db_user)) -> User:
    """Guards a route to admin-role users only."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
