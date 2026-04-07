"""Auth0 helpers."""

from urllib.parse import urlencode

from app.core.settings import settings


def build_signup_url(email: str) -> str:
    """Return an /authorize URL that drops the user
    directly into the Auth0 sign-up form."""
    params = urlencode(
        {
            "client_id": settings.AUTH0_SPA_CLIENT_ID,
            "redirect_uri": settings.APP_BASE_URL,
            "response_type": "code",
            "scope": "openid profile email",
            "screen_hint": "signup",
            "login_hint": email,
        }
    )
    return f"https://{settings.AUTH0_DOMAIN}/authorize?{params}"
