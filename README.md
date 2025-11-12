# Running Coach

A web application to track your running and fitness stats using Strava integration.

## Features

- Strava OAuth2 authentication
- Automatic activity sync
- Running statistics and analytics
- Beautiful, responsive UI

## Prerequisites

- **Docker & Docker Compose** (recommended) OR
- Python 3.8+ and pip
- Strava API credentials

## Quick Start with Docker (Recommended)

### 0. Install Docker Desktop

If you don't have Docker installed:

1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Install Docker Desktop
3. Open the **Docker Desktop** application
4. Sign in with your Docker account (or GitHub account)
5. Wait for Docker Desktop to fully start - you'll see "Docker Desktop is running" in the app
6. Keep Docker Desktop running in the background

**Important:** Docker Desktop must be running before you execute any `docker-compose` commands!

### 1. Get Strava API Credentials

1. Go to https://www.strava.com/settings/api
2. Create a new application
3. Set the **Authorization Callback Domain** to `localhost`
4. Note your **Client ID** and **Client Secret**

### 2. Configure Environment Variables

**Open your terminal** and navigate to the project:

```bash
cd running-coach
cp .env.example .env
```

Edit `.env` and add your Strava credentials:

```
STRAVA_CLIENT_ID=your_actual_client_id
STRAVA_CLIENT_SECRET=your_actual_client_secret
SECRET_KEY=your-random-secret-key-here
REDIRECT_URI=http://localhost:8000/auth/callback
```

To generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Or use any random string generator.

### 3. Build and Run with Docker Compose

**In your terminal**, make sure you're in the project directory and run:

```bash
docker-compose up --build
```

This will:
- Build the Docker image
- Install all dependencies
- Start the application
- Show you logs in the terminal

The application will be available at: **http://localhost:8000**

**Other useful commands:**

To run in detached mode (background):
```bash
docker-compose up -d
```

To view logs when running in detached mode:
```bash
docker-compose logs -f
```

To stop:
```bash
docker-compose down
```

To rebuild after code changes:
```bash
docker-compose up --build
```

### 4. Test the Login Flow

1. Open http://localhost:8000 in your browser
2. Click "Connect with Strava"
3. Authorize the application on Strava's page
4. You'll be redirected back to the dashboard with your athlete info

## Alternative: Run Without Docker

If you prefer not to use Docker:

### 1. Install Dependencies

```bash
cd running-coach
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment (same as above)

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run the Application

```bash
uvicorn app.main:app --reload
```

The application will be available at: http://localhost:8000

## Project Structure

```
running-coach/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── routers/
│   │   ├── __init__.py
│   │   └── auth.py          # Authentication routes
│   ├── templates/           # HTML templates
│   │   ├── index.html
│   │   └── dashboard.html
│   └── static/
│       └── css/
│           └── style.css
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── .dockerignore           # Docker ignore file
├── .env                     # Environment variables (not in git)
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
└── README.md
```

## Next Steps

- [ ] Add database for storing user data and tokens
- [ ] Implement session management
- [ ] Fetch and display activities from Strava
- [ ] Add running statistics and analytics
- [ ] Create goal tracking features
- [ ] Add data visualization charts

## Technologies Used

- **FastAPI** - Modern Python web framework
- **Strava API** - OAuth2 and activity data
- **Jinja2** - Template engine
- **HTTPX** - Async HTTP client
- **Uvicorn** - ASGI server