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

### 1. Get Strava API Credentials

1. Go to https://www.strava.com/settings/api
2. Create a new application
3. Set the **Authorization Callback Domain** to `localhost`
4. Note your **Client ID** and **Client Secret**

### 2. Configure Environment Variables

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

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

That's it! The application will be available at: **http://localhost:8000**

To run in detached mode:
```bash
docker-compose up -d
```

To stop:
```bash
docker-compose down
```

### 4. Test the Login Flow

1. Open http://localhost:8000 in your browser
2. Click "Connect with Strava"
3. Authorize the application
4. You'll be redirected back to the dashboard

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