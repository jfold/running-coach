from fastapi import FastAPI, Request, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth
from app.config import get_settings
from app.services.user_settings import user_settings_service
from app.services.personal_records import personal_records_service
import httpx
from datetime import datetime
from typing import Optional

settings = get_settings()

app = FastAPI(title="Running Coach", description="Track your running stats with Strava")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth.router)

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with login"""
    # If already logged in, redirect to dashboard
    if "access_token" in request.session:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard with athlete info and activities"""
    # Check if user is authenticated
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/")

    athlete = request.session.get("athlete", {})

    # Fetch latest activities from Strava
    activities = []
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(
            f"{settings.strava_api_base}/athlete/activities",
            headers=headers,
            params={"per_page": 10}  # Get last 10 activities
        )

        if response.status_code == 200:
            activities = response.json()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "athlete": athlete,
            "activities": activities
        }
    )


@app.get("/api/activities")
async def get_activities(request: Request, start_date: str, end_date: str):
    """Get activities within a date range"""
    # Check if user is authenticated
    access_token = request.session.get("access_token")
    if not access_token:
        return {"error": "Not authenticated"}, 401

    try:
        # Convert dates to timestamps
        start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()) + 86399  # End of day

        # Fetch activities from Strava
        activities = []
        page = 1
        per_page = 100

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}

            while True:
                response = await client.get(
                    f"{settings.strava_api_base}/athlete/activities",
                    headers=headers,
                    params={
                        "after": start_timestamp,
                        "before": end_timestamp,
                        "page": page,
                        "per_page": per_page
                    }
                )

                if response.status_code != 200:
                    break

                batch = response.json()
                if not batch:
                    break

                activities.extend(batch)
                page += 1

                # Limit to prevent excessive requests
                if len(activities) >= 200:
                    break

        return {"activities": activities}

    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/athlete")
async def get_athlete(request: Request):
    """Get full athlete details from Strava"""
    access_token = request.session.get("access_token")
    if not access_token:
        return {"error": "Not authenticated"}, 401

    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(
                f"{settings.strava_api_base}/athlete",
                headers=headers
            )

            if response.status_code == 200:
                athlete_data = response.json()
                # Update session with latest data
                request.session["athlete"] = athlete_data
                return athlete_data
            else:
                return {"error": "Failed to fetch athlete data"}, response.status_code

    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/hr-settings")
async def get_hr_settings(request: Request):
    """Get user's heart rate settings"""
    athlete = request.session.get("athlete", {})
    if not athlete:
        return {"error": "Not authenticated"}, 401

    user_id = str(athlete.get("id"))
    settings = user_settings_service.get_settings(user_id)
    return settings


@app.post("/api/hr-settings/zones")
async def update_hr_zones(request: Request, zones: dict = Body(...)):
    """Update heart rate zones manually"""
    athlete = request.session.get("athlete", {})
    if not athlete:
        return {"error": "Not authenticated"}, 401

    user_id = str(athlete.get("id"))
    settings = user_settings_service.update_hr_zones(user_id, zones)
    return settings


@app.post("/api/hr-settings/params")
async def update_hr_params(
    request: Request,
    max_hr: Optional[int] = Body(None),
    fitness_age: Optional[int] = Body(None),
    actual_age: Optional[int] = Body(None)
):
    """Update HR parameters (max HR, fitness age, actual age)"""
    athlete = request.session.get("athlete", {})
    if not athlete:
        return {"error": "Not authenticated"}, 401

    user_id = str(athlete.get("id"))
    settings = user_settings_service.update_hr_params(
        user_id,
        max_hr=max_hr,
        fitness_age=fitness_age,
        actual_age=actual_age
    )
    return settings


@app.get("/api/personal-records")
async def get_personal_records(request: Request):
    """Get athlete's personal records for standard distances"""
    access_token = request.session.get("access_token")
    if not access_token:
        return {"error": "Not authenticated"}, 401

    try:
        # Fetch all activities (up to 200 for performance)
        activities = []
        page = 1
        per_page = 100

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}

            while True:
                response = await client.get(
                    f"{settings.strava_api_base}/athlete/activities",
                    headers=headers,
                    params={
                        "page": page,
                        "per_page": per_page
                    }
                )

                if response.status_code != 200:
                    break

                batch = response.json()
                if not batch:
                    break

                activities.extend(batch)
                page += 1

                # Limit to prevent excessive requests (get last 200 activities)
                if len(activities) >= 200:
                    break

        # Calculate personal records
        personal_records = personal_records_service.calculate_personal_records(activities)

        return personal_records

    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
