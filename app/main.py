from fastapi import FastAPI, Request, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth
from app.config import get_settings
from app.services.user_settings import user_settings_service
from app.services.personal_records import personal_records_service
from app.services.cache import cache_service
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
async def get_activities(request: Request, start_date: str, end_date: str, refresh: bool = False):
    """Get activities within a date range with caching"""
    # Check if user is authenticated
    access_token = request.session.get("access_token")
    if not access_token:
        return {"error": "Not authenticated"}, 401

    athlete = request.session.get("athlete", {})
    user_id = str(athlete.get("id"))

    try:
        # Check cache first (cache for 1 hour for activities)
        cache_key = f"activities_{user_id}_{start_date}_{end_date}"

        if not refresh:
            cached_data = cache_service.get(cache_key, max_age_hours=1)
            if cached_data:
                print(f"Returning cached activities for user {user_id}")
                return cached_data

        print(f"Fetching activities from Strava for user {user_id}")

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

                if response.status_code == 429:
                    # Rate limited
                    return {"error": "Rate limited", "activities": []}, 429

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

        result = {"activities": activities}

        # Cache the result
        cache_service.set(cache_key, result)

        return result

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
        # Fetch activity list
        activities = []
        page = 1
        per_page = 30  # Just get 30 most recent

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {access_token}"}

            # Get one page of activities
            response = await client.get(
                f"{settings.strava_api_base}/athlete/activities",
                headers=headers,
                params={
                    "page": page,
                    "per_page": per_page
                }
            )

            if response.status_code == 429:
                # Rate limited - return empty for now
                return {
                    "1km": None,
                    "5km": None,
                    "10km": None,
                    "half_marathon": None,
                    "marathon": None,
                    "rate_limited": True
                }

            if response.status_code == 200:
                activities = response.json()

        # Filter only running activities and use the simple distance-matching approach
        from app.services.personal_records import personal_records_service
        personal_records = personal_records_service.calculate_personal_records(activities)

        return personal_records

    except Exception as e:
        print(f"ERROR in personal_records: {str(e)}")
        return {"error": str(e)}, 500


@app.get("/api/best-efforts")
async def get_best_efforts(request: Request, refresh: bool = False):
    """Get athlete's best efforts from detailed activity data with caching"""
    access_token = request.session.get("access_token")
    if not access_token:
        return {"error": "Not authenticated"}, 401

    athlete = request.session.get("athlete", {})
    user_id = str(athlete.get("id"))

    try:
        # Check cache first (cache for 24 hours) unless refresh is requested
        cache_key = f"best_efforts_{user_id}"

        if not refresh:
            cached_data = cache_service.get(cache_key, max_age_hours=24)
            if cached_data:
                print(f"Returning cached best efforts for user {user_id}")
                cached_data["cached"] = True
                return cached_data

        # Cache miss - fetch from Strava
        print(f"Cache miss - fetching best efforts from Strava for user {user_id}")

        # Fetch activity list first
        activity_ids = []
        page = 1

        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {"Authorization": f"Bearer {access_token}"}

            # Get list of run activities (just first page to limit API calls)
            response = await client.get(
                f"{settings.strava_api_base}/athlete/activities",
                headers=headers,
                params={
                    "page": page,
                    "per_page": 30
                }
            )

            if response.status_code == 429:
                # Rate limited - return empty with message
                return {
                    "best_efforts": {},
                    "rate_limited": True,
                    "message": "Rate limited by Strava. Please try again in 15 minutes."
                }

            if response.status_code == 200:
                batch = response.json()
                # Only get IDs for running activities
                run_ids = [a['id'] for a in batch if a.get('type') == 'Run']
                activity_ids.extend(run_ids[:15])  # Limit to 15 most recent runs

            # Fetch detailed activity data for each run to get best_efforts
            all_best_efforts = []
            for activity_id in activity_ids:
                detail_response = await client.get(
                    f"{settings.strava_api_base}/activities/{activity_id}",
                    headers=headers
                )

                if detail_response.status_code == 429:
                    # Hit rate limit mid-fetch, return what we have
                    print(f"Rate limited after fetching {len(all_best_efforts)} activities")
                    break

                if detail_response.status_code == 200:
                    detailed_activity = detail_response.json()
                    best_efforts = detailed_activity.get('best_efforts', [])

                    if best_efforts:
                        all_best_efforts.append(best_efforts)

        # Calculate best efforts from all activities
        best_efforts_data = personal_records_service.calculate_personal_records_from_best_efforts(all_best_efforts)

        # Cache the result
        result = {
            "best_efforts": best_efforts_data,
            "cached": False,
            "activities_checked": len(activity_ids)
        }

        cache_service.set(cache_key, result)

        return result

    except Exception as e:
        print(f"ERROR in best_efforts: {str(e)}")
        return {"error": str(e)}, 500


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
