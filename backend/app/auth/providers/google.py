from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from typing import Optional
import httpx # type: ignore
from urllib.parse import urlencode
import logging
from app.config.settings import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, FRONTEND_URL
from app.auth.security_jwt import create_access_token
from app.auth.security_passwords import hash_password
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.db import models
from sqlalchemy.exc import OperationalError as SAOperationalError

router = APIRouter(prefix="/auth/google", tags=["auth", "google"])

logger = logging.getLogger(__name__)

GOOGLE_OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_USERINFO = "https://openidconnect.googleapis.com/v1/userinfo"


@router.get("/login")
def login(popup: Optional[bool] = False):
    # Build authorization URL using redirect configured in env
    state = "popup" if popup else ""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    # Build query string safely
    qs = urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{GOOGLE_OAUTH_AUTH_URL}?{qs}"
    return RedirectResponse(url)


async def handle_google_callback(code: Optional[str], db: Session):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = await client.post(GOOGLE_OAUTH_TOKEN_URL, data=data, headers=headers)
        try:
            token_json = resp.json()
        except Exception:
            token_json = None
        if resp.status_code != 200:
            # Log full response for debugging
            logger.error("Google token exchange failed (status=%s): %s", resp.status_code, resp.text)
            raise RuntimeError(f"Token exchange failed: status={resp.status_code} body={resp.text}")

        # Get userinfo
        access_token = token_json.get("access_token") # type: ignore
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token returned")
        ui_resp = await client.get(GOOGLE_OAUTH_USERINFO, headers={"Authorization": f"Bearer {access_token}"})
        try:
            info = ui_resp.json()
        except Exception:
            info = None
        if ui_resp.status_code != 200 or not info:
            logger.error("Google userinfo failed (status=%s): %s", ui_resp.status_code, ui_resp.text)
            raise RuntimeError(f"Failed to fetch user info: status={ui_resp.status_code} body={ui_resp.text}")

    email = info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    # Find or create user
    try:
        persona = db.query(models.User).filter(models.User.email == email.lower()).first()
        created = False
        if not persona:
            created = True
            persona = models.User(email=email.lower(), password_hash=hash_password("google-oauth"))
            db.add(persona)
            db.commit()
            db.refresh(persona)
        # Include role claims for faster client gating
        try:
            effective_role = getattr(persona, 'role', 'user') or 'user'
            if getattr(persona, 'is_superadmin', False):
                effective_role = 'admin'
            is_super = bool(getattr(persona, 'is_superadmin', False))
        except Exception:
            effective_role = 'user'; is_super = False
        token = create_access_token(str(persona.id), role=effective_role, is_superadmin=is_super)
    except SAOperationalError as e:
        # DB not reachable / invalid credentials. Allow a temporary fallback for testing/dev:
        logger.exception("DB OperationalError when finding/creating persona — falling back to pseudo-user")
        # Issue a token for pseudo-user sub = "0" (static fallback). Do NOT use this in production.
        token = create_access_token("0", role=None, is_superadmin=False)
        return {"access_token": token, "token_type": "bearer", "email": email, "note": "db_unavailable"}
    except Exception as e:
        logger.exception("DB error when finding/creating persona")
        raise RuntimeError(f"DB error: {e}")

    # If the OAuth flow used state=popup, return an HTML page that posts the token to window.opener
    # so popups can close themselves and communicate with the parent. Otherwise redirect to frontend /home with token in fragment.
    request_state = None
    try:
        # If called inside FastAPI route, Request is available in outer scope; otherwise ignore
        request_state = Request  # type: ignore
    except Exception:
        request_state = None

    # Decide response based on 'state' query param handled by the route caller
    # The routes pass through the query params; to keep it simple we read nothing here and rely on the callback route wrapper to choose.
    # Return a JSON by default; wrapper routes may instead return HTML.
    return {"access_token": token, "token_type": "bearer", "email": persona.email, "created": created}


from fastapi.responses import HTMLResponse
import traceback
from app.config.settings import DEBUG


def _render_postmessage_html(token: str, email: str, created: bool = False) -> str:
    # Posts token to opener and closes the popup. Uses window.location.origin as target origin for postMessage.
    safe_token = token.replace("\n", "")
    # include created flag so the opener can know if the user was newly created
    created_js = 'true' if created else 'false'
    return f"""<!doctype html>
<html>
<head><meta charset='utf-8'><title>Logging in...</title></head>
<body>
<script>
(function(){{
    try {{
    const payload = {{ type: "google-auth", token: "{safe_token}", email: "{email}", status: 200, created: {created_js}, origin: window.location.origin }};
        // Try to determine opener origin; cross-origin access may throw, so fall back to '*'
        let targetOrigin = '*';
        try {{
            if (window.opener && !window.opener.closed && window.opener.location && window.opener.location.origin) {{
                targetOrigin = window.opener.location.origin;
            }}
        }} catch (err) {{ /* ignore cross-origin access errors and use wildcard */ }}

        if (window.opener && !window.opener.closed) {{
            // Use a permissive origin so message is delivered; the opener will validate event.origin
            window.opener.postMessage(payload, targetOrigin);
            window.close();
        }} else {{
            // Fallback: redirect top to frontend home with token in fragment
            window.location.href = '{FRONTEND_URL}/home#access_token={safe_token}';
        }}
    }} catch (e) {{
        try {{ window.location.href = '{FRONTEND_URL}/home'; }} catch (e) {{ }}
    }}
}})();
</script>
<p>Logging in... If you are not redirected, close this window.</p>
</body>
</html>
"""


@router.get("/callback")
async def callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        result = await handle_google_callback(code=code, db=db)
        token = result.get('access_token')
        email = result.get('email')
        if state == 'popup':
            html = _render_postmessage_html(token, email, result.get('created', False)) # type: ignore
            return HTMLResponse(content=html, status_code=200)
        # Non-popup: redirect user to frontend /home with token in fragment
        return RedirectResponse(url=f"{FRONTEND_URL}/home#access_token={token}")
    except Exception as e:
        # Log full exception
        logger.exception("Google callback failed")
        tb = traceback.format_exc()
        if DEBUG:
            # Return stacktrace for easier debugging in dev
            return HTMLResponse(content=f"<pre>{tb}</pre>", status_code=500)
        else:
            # Generic response for production
            return HTMLResponse(content="<p>Internal server error during Google callback. Check server logs.</p>", status_code=500)


@router.get("/authorized")
async def authorized(request: Request, code: Optional[str] = None, state: Optional[str] = None, db: Session = Depends(get_db)):
        # Alternate path under /auth/google/authorized
        return await callback(request=request, code=code, state=state, db=db)
