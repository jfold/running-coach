from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
from urllib.parse import urlencode
from app.config import get_settings
import secrets

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()

# In-memory storage for state tokens (use Redis or DB in production)
state_store = {}


@router.get("/login")
async def login(request: Request):
    """Initiate Strava OAuth flow"""
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    state_store[state] = True

    # Build Strava authorization URL
    params = {
        "client_id": settings.strava_client_id,
        "redirect_uri": settings.redirect_uri,
        "response_type": "code",
        "scope": "read,activity:read,activity:read_all,profile:read_all",
        "state": state,
        "approval_prompt": "auto"
    }

    auth_url = f"{settings.strava_authorize_url}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle Strava OAuth callback"""

    # Check for errors
    if error:
        raise HTTPException(status_code=400, detail=f"Authorization failed: {error}")

    # Verify state to prevent CSRF
    if not state or state not in state_store:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Remove used state
    del state_store[state]

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    # Exchange authorization code for access token
    async with httpx.AsyncClient() as client:
        token_data = {
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }

        response = await client.post(settings.strava_token_url, data=token_data)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to exchange authorization code"
            )

        token_response = response.json()

    # Extract user information and tokens
    athlete = token_response.get("athlete", {})
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    expires_at = token_response.get("expires_at")

    # TODO: Store tokens and user info in database/session
    # For now, we'll just display the user info

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "athlete": athlete,
            "message": "Successfully authenticated with Strava!"
        }
    )


@router.get("/logout")
async def logout():
    """Logout user"""
    # TODO: Clear session/cookies and revoke Strava token
    return RedirectResponse(url="/")
