"""Auth0 authentication dependency."""

import os

from fastapi_plugin.fast_api_client import Auth0FastAPI

auth0_domain = os.environ.get("AUTH0_DOMAIN")
auth0_audience = os.environ.get("AUTH0_AUDIENCE")

if not auth0_domain or not auth0_audience:
    raise RuntimeError("AUTH0_DOMAIN and AUTH0_AUDIENCE must be set")

auth0 = Auth0FastAPI(domain=auth0_domain, audience=auth0_audience)

_verifier = auth0.require_auth()


async def get_current_user(claims: dict = Depends(_verifier)) -> dict:
    """Dependency that validates the Auth0 JWT and returns the claims."""
    return claims


# # Uncomment to bypass auth for local dev/testing (re-comment before committing):
# async def get_current_user() -> dict:
#     return {"sub": "dev-user"}
